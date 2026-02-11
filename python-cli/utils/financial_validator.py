
"""
Financial Validator & Metadata Injector
---------------------------------------
Validación aritmética de balances municipales y estrategia de inyección de metadatos para RAG.

Author: Antigravity (MIT/Stanford Agent)
Date: 2026-01-08
"""

import pandas as pd
import numpy as np
import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime

# ============================================================================
# METADATA SCHEMA
# ============================================================================

@dataclass
class FinancialMetadata:
    """Clase para la estrategia de metadatos 'Parent-Child'."""
    entity: str           # "Municipalidad de Carlos Tejedor"
    document_type: str    # "Balance de Sumas y Saldos"
    period: str           # "2024-01"
    year: int             # 2024
    month: int            # 1
    page_number: int
    source_file: str

@dataclass
class FinancialChunk:
    """Schema enriquecido para cada chunk del RAG."""
    chunk_id: str
    metadata: FinancialMetadata
    
    # Jerarquía del documento (Headers superiores)
    hierarchy: Dict[str, str] = field(default_factory=dict)
    
    # Datos estructurados ("Payload")
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Texto para embedding (Sentence-transformer optimized)
    embedding_text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "metadata": asdict(self.metadata),
            "hierarchy": self.hierarchy,
            "data": self.data,
            "embedding_text": self.embedding_text
        }

# ============================================================================
# VALIDATION LOGIC
# ============================================================================

class FinancialValidator:
    """
    Validación determinística de tablas financieras.
    Regla principal: Saldo Inicial + Debe - Haber = Saldo Final
    """
    
    def __init__(self, tolerance: float = 0.05):
        self.tolerance = tolerance

    @staticmethod
    def clean_currency(value: Any) -> float:
        """
        Normaliza strings financieros (OCR) a floats.
        Maneja formatos argentinos: 1.000,00 -> 1000.00
        """
        if pd.isna(value) or value == '' or value is None:
            return 0.0
        
        # Convertir a string y limpiar basura
        clean = str(value).strip()
        
        # Eliminar caracteres no numéricos excepto puntos, comas y menos
        clean = re.sub(r'[^\d.,-]', '', clean)
        
        if not clean:
            return 0.0

        try:
            # Heurística para formato argentino (miles con punto, decimal con coma)
            if ',' in clean and '.' in clean:
                # Caso: 1.500,50
                if clean.rfind(',') > clean.rfind('.'):
                    clean = clean.replace('.', '').replace(',', '.')
                # Caso raro: 1,500.50 (formato US mezclado)
                else:
                    clean = clean.replace(',', '') 
            elif ',' in clean:
                # Caso: 1500,50 -> chequear si es separador de miles o decimal
                parts = clean.split(',')
                # Si la parte decimal es exactamente 3 digitos, asumo miles (1,500)
                # OJO: Esto es riesgoso en montos exactos, pero común.
                # Preferimos asumir coma=decimal en contexto AR salvo que sea obvio.
                if len(parts) == 2 and len(parts[1]) == 3:
                     clean = clean.replace(',', '') # asumo miles
                else:
                     clean = clean.replace(',', '.') # asumo decimal
            
            # Si solo tiene puntos, eliminar si son miles, mantener si es decimal?
            # En AR 1.500 es miles. 1.500.000 es millones.
            # Python float() usa punto como decimal.
            # ESTRATEGIA SEGURA: Si hay más de un punto, son miles.
            elif clean.count('.') > 1:
                clean = clean.replace('.', '')
            
            return float(clean)
        except ValueError:
            return 0.0

    def validate_balance_sheet(self, df: pd.DataFrame, 
                               col_mapping: Dict[str, str] = None) -> pd.DataFrame:
        """
        Valida la ecuación contable en un DataFrame.
        Retorna el DF con columnas 'calculated_final', 'diff', 'is_valid'.
        
        Args:
            df: DataFrame con los datos OCR.
            col_mapping: Diccionario mapeando columnas estandar a las del DF.
                         Default: {'initial': 'saldo_inicial', 'debit': 'debe', 
                                   'credit': 'haber', 'final': 'saldo_final'}
        """
        if col_mapping is None:
            col_mapping = {
                'initial': 'saldo_inicial',
                'debit': 'debe',
                'credit': 'haber',
                'final': 'saldo_final'
            }
            
        # Verificar que existan las columnas
        required_cols = list(col_mapping.values())
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            raise ValueError(f"Faltan columnas requeridas en el DataFrame: {missing}")

        # Copia para no mutar original
        valid_df = df.copy()

        # 1. Normalización Vectorizada
        for col in required_cols:
            valid_df[col] = valid_df[col].apply(self.clean_currency)

        # 2. Cálculo Vectorizado
        # Saldo Final Calculado = Inicial + Debe - Haber
        # NOTA: Dependiendo de si es cuenta de Activo (Deudor) o Pasivo (Acreedor)
        # la formula cambia. PERO en reportes municipales standard (RAFAM),
        # suelen presentarse columnas separadas o signos.
        # Asumiremos Saldo Deudor x defecto para la validación simple.
        
        valid_df['calculated_final'] = (
            valid_df[col_mapping['initial']] + 
            valid_df[col_mapping['debit']] - 
            valid_df[col_mapping['credit']]
        )
        
        # 3. Validación (Diferencia Absoluta)
        valid_df['diff'] = (valid_df['calculated_final'] - valid_df[col_mapping['final']]).abs()
        valid_df['is_valid'] = valid_df['diff'] < self.tolerance
        
        return valid_df

# ============================================================================
# CHUNKING & INJECTION STRATEGY
# ============================================================================

class ChunkGenerator:
    """Generador de chunks enriquecidos para RAG."""
    
    @staticmethod
    def generate_chunks(df: pd.DataFrame, metadata: FinancialMetadata) -> List[FinancialChunk]:
        """
        Convierte filas validadas en chunks listos para insertar en VectorDB.
        """
        chunks = []
        
        for idx, row in df.iterrows():
            # Construir ID único
            chunk_id = f"{metadata.entity}_{metadata.year}_{metadata.period}_row_{idx}".lower().replace(" ", "_")
            
            # Datos estructurados de la fila
            row_data = row.to_dict()
            
            # Limpiar datos técnicos de validación antes de meter en "data"
            for tech_col in ['calculated_final', 'diff', 'is_valid']:
                if tech_col in row_data:
                    del row_data[tech_col]

            # Construir texto para embedding (Natural Language Optimization)
            # Template: "{Entidad}: {Cuenta} ({Codigo}). Saldo: {Saldo}."
            
            # Mapeo flexible de columnas
            account_name = row.get('nombre_cuenta') or row.get('DESCRIPCION') or row.get('cuenta') or 'Cuenta desconocida'
            account_code = row.get('codigo_cuenta') or row.get('CUENTA') or ''
            
            # Saldo final puede estar en varias columnas (Debe/Haber o unificado)
            final_bal_raw = row.get('saldo_final') or row.get('SALDO FINAL DEBE') or row.get('SALDO FINAL') or row.get('IMPORTE') or 0.0
            # Si es haber, lo mostramos como crédito o negativo si es necesario, por ahora lo dejamos simple
            if not final_bal_raw and row.get('SALDO FINAL HABER'):
                 final_bal_raw = row.get('SALDO FINAL HABER')

            # Limpiar y convertir a float para el texto del embedding
            final_bal = 0.0
            if final_bal_raw:
                try:
                    if isinstance(final_bal_raw, str):
                        # Limpieza común de formatos latinos/europeos (1.234,56 -> 1234.56)
                        cleaned = final_bal_raw.replace('.', '').replace(',', '.')
                        final_bal = float(cleaned)
                    else:
                        final_bal = float(final_bal_raw)
                except:
                    final_bal = 0.0

            embedding_text = (
                f"Balance {metadata.entity} ({metadata.period}). "
                f"Cuenta: {account_name} " + (f"({account_code}). " if account_code else ". ") +
                f"Saldo Final: ${final_bal:,.2f}."
            )

            chunk = FinancialChunk(
                chunk_id=chunk_id,
                metadata=metadata,
                hierarchy={}, # TODO: Extraer jerarquía si está disponible en col 'rubro'
                data=row_data,
                embedding_text=embedding_text
            )
            
            chunks.append(chunk)
            
        return chunks

# ============================================================================
# UTILITIES
# ============================================================================

def markdown_to_dataframe(md_table: str) -> pd.DataFrame:
    """
    Parses a Markdown table into a pandas DataFrame.
    Handles standard pipe-separated tables.
    """
    lines = md_table.strip().split('\n')
    
    # Filter out separator lines (dashes)
    lines = [line for line in lines if '---' not in line]
    
    if len(lines) < 2:
        return pd.DataFrame()

    # Extract headers
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    
    # Extract data
    data = []
    for line in lines[1:]:
        # Split by pipe and strip whitespace
        row = [cell.strip() for cell in line.split('|')]
        
        # Remove empty strings from leading/trailing pipes
        if line.strip().startswith('|'):
            row = row[1:]
        if line.strip().endswith('|'):
            row = row[:-1]
            
        data.append(row)

    # Create DataFrame
    try:
        # Fill missing columns with None to match header length
        cleaned_data = []
        for row in data:
            if len(row) < len(headers):
                row.extend([None] * (len(headers) - len(row)))
            elif len(row) > len(headers):
                row = row[:len(headers)]
            cleaned_data.append(row)
            
        df = pd.DataFrame(cleaned_data, columns=headers)
        return df
    except Exception:
        return pd.DataFrame()

