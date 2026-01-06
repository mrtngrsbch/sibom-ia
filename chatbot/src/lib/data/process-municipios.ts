/**
 * Script para procesar datos de municipios y boletines
 * Genera estadísticas y extrae fechas de publicación
 * Usa boletines_index.json como fuente única de verdad (consistente con /api/stats)
 */

import { readFileSync } from 'fs';
import { join } from 'path';

interface MunicipioRow {
  municipio: string;
  url: string;
  datos: 'yes' | 'no';
  cityId: number;
}

interface BoletinIndexEntry {
  id: string;
  municipality: string;
  type: string;
  number: string;
  title: string;
  date: string;
  url: string;
  status: string;
  filename: string;
}

interface MunicipioStats {
  municipio: string;
  url: string;
  cityId: number;
  tieneDatos: boolean;
  cantidadBoletines: number;
  primeraPublicacion: string | null;
  ultimaPublicacion: string | null;
}

interface GlobalStats {
  totalMunicipios: number;
  municipiosConDatos: number;
  municipiosSinDatos: number;
  totalDocumentos: number;
  municipios: MunicipioStats[];
}

/**
 * Parse de la tabla de municipios desde el archivo MD
 */
function parseMunicipiosFromMd(mdContent: string): MunicipioRow[] {
  const lines = mdContent.split('\n');
  const municipios: MunicipioRow[] = [];

  // Buscar líneas de la tabla (después del header)
  let headerFound = false;
  for (const line of lines) {
    // Buscar header solo si no lo hemos encontrado y la línea contiene el header exacto
    if (!headerFound && line.trim().startsWith('| Municipio') && line.includes('URL') && line.includes('datos')) {
      headerFound = true;
      continue;
    }

    // Después del header, procesar filas de la tabla
    if (headerFound && line.startsWith('|')) {
      // Saltar línea de separación
      if (line.includes('---') || line.includes(':--')) continue;

      const parts = line.split('|').map(p => p.trim()).filter(p => p);
      if (parts.length >= 3) {
        const municipio = parts[0];
        const url = parts[1];
        const datos = parts[2] as 'yes' | 'no';

        // Validar que tenga URL válida
        if (!url.includes('http')) continue;

        // Extraer cityId de la URL
        const match = url.match(/\/cities\/(\d+)/);
        const cityId = match ? parseInt(match[1]) : 0;

        municipios.push({ municipio, url, datos, cityId });
      }
    }
  }

  return municipios;
}

/**
 * Normalizar nombre de municipio para coincidir con el índice
 */
function normalizeMunicipioName(name: string): string {
  return name
    .replace('Municipio de ', '')
    .replace('Municipio De ', '')
    .replace('Municipio ', '')
    .trim();
}

/**
 * Parsear fecha en formato DD/MM/YYYY a objeto Date
 */
function parseDate(dateStr: string): Date | null {
  if (!dateStr) return null;
  const parts = dateStr.split('/');
  if (parts.length !== 3) return null;

  const day = parseInt(parts[0]);
  const month = parseInt(parts[1]) - 1; // Mes en JS es 0-indexed
  const year = parseInt(parts[2]);

  return new Date(year, month, day);
}

/**
 * Formatear fecha de Date a DD/MM/YYYY
 */
function formatDate(date: Date): string {
  const day = String(date.getDate()).padStart(2, '0');
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const year = date.getFullYear();
  return `${day}/${month}/${year}`;
}

/**
 * Procesar boletines de un municipio desde el índice
 */
function processBoletinesMunicipio(
  municipioName: string,
  boletinesIndex: BoletinIndexEntry[]
): { cantidad: number; primera: string | null; ultima: string | null } {
  const normalizedName = normalizeMunicipioName(municipioName);

  // Filtrar boletines de este municipio
  const municipioBoletines = boletinesIndex.filter(
    b => b.municipality === normalizedName
  );

  if (municipioBoletines.length === 0) {
    return { cantidad: 0, primera: null, ultima: null };
  }

  // Extraer y ordenar fechas
  const fechas: Date[] = [];
  for (const boletin of municipioBoletines) {
    if (boletin.date) {
      const fecha = parseDate(boletin.date);
      if (fecha && !isNaN(fecha.getTime())) {
        fechas.push(fecha);
      }
    }
  }

  if (fechas.length === 0) {
    return { cantidad: municipioBoletines.length, primera: null, ultima: null };
  }

  // Ordenar fechas
  fechas.sort((a, b) => a.getTime() - b.getTime());

  return {
    cantidad: municipioBoletines.length,
    primera: formatDate(fechas[0]),
    ultima: formatDate(fechas[fechas.length - 1])
  };
}

/**
 * Generar estadísticas globales usando boletines_index.json
 */
export function generateMunicipiosStats(): GlobalStats {
  // Paths relativos al proyecto
  const rootPath = process.cwd();
  const mdPath = join(rootPath, '..', 'docs', 'Municipios_contenidos.md');
  const indexPath = join(rootPath, '..', 'python-cli', 'boletines_index.json');

  // Leer archivo MD
  const mdContent = readFileSync(mdPath, 'utf-8');
  const municipiosData = parseMunicipiosFromMd(mdContent);

  // Leer índice de boletines
  const indexContent = readFileSync(indexPath, 'utf-8');
  const boletinesIndex: BoletinIndexEntry[] = JSON.parse(indexContent);

  // Procesar cada municipio
  const municipiosStats: MunicipioStats[] = municipiosData.map(m => {
    // Siempre procesar boletines - no confiar en el MD file
    const boletinesInfo = processBoletinesMunicipio(m.municipio, boletinesIndex);

    return {
      municipio: m.municipio,
      url: m.url,
      cityId: m.cityId,
      tieneDatos: boletinesInfo.cantidad > 0, // Basado en datos reales del índice
      cantidadBoletines: boletinesInfo.cantidad,
      primeraPublicacion: boletinesInfo.primera,
      ultimaPublicacion: boletinesInfo.ultima
    };
  });

  // Calcular estadísticas globales
  const totalDocumentos = municipiosStats.reduce(
    (sum, m) => sum + m.cantidadBoletines,
    0
  );

  return {
    totalMunicipios: municipiosData.length,
    municipiosConDatos: municipiosData.filter(m => m.datos === 'yes').length,
    municipiosSinDatos: municipiosData.filter(m => m.datos === 'no').length,
    totalDocumentos,
    municipios: municipiosStats
  };
}
