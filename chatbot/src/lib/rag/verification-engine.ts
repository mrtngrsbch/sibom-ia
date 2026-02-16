/**
 * Layer 4: VerificationEngine
 * 
 * Motor de verificación post-generación para detectar alucinaciones numéricas
 * en respuestas sobre documentos Balance.
 * 
 * Funcionalidades:
 * 1. Extrae números monetarios de la respuesta del LLM
 * 2. Verifica si esos números existen en los chunks de origen
 * 3. Calcula confidence score (0-1)
 * 4. Agrega badges visuales (✅/⚠️/❌)
 * 5. Detecta alucinaciones automáticamente
 */

// ============================================================================
// Types
// ============================================================================

export interface ExtractedNumber {
  /** Valor numérico parseado */
  value: number;
  
  /** String original (ej: "$469,581,055.31") */
  original: string;
  
  /** Posición en el texto */
  position: number;
  
  /** Contexto (palabras alrededor) */
  context?: string;
}

export interface ValidationResult {
  /** Número validado */
  number: ExtractedNumber;
  
  /** ¿Se encontró en las fuentes? */
  found: boolean;
  
  /** Confidence (0-1): 1 = match exacto, 0.8-0.99 = similar, <0.8 = no encontrado */
  confidence: number;
  
  /** Source chunk donde se encontró (si found=true) */
  sourceChunk?: string;
  
  /** Razón de la validación */
  reason: string;
}

export interface VerificationReport {
  /** Cantidad de números extraídos */
  totalNumbers: number;
  
  /** Cantidad de números verificados */
  verifiedNumbers: number;
  
  /** Confidence global (0-1) */
  overallConfidence: number;
  
  /** ¿Es probable alucinación? */
  possibleHallucination: boolean;
  
  /** Resultados individuales por número */
  validations: ValidationResult[];
  
  /** Mensaje legible para el usuario */
  message: string;
}

// ============================================================================
// Configuration
// ============================================================================

/** Patrones de números monetarios en español argentino */
const MONEY_PATTERNS = [
  // "469 millones" (approx) - PRIMERO para evitar capturas duplicadas
  /([0-9]{1,4}(?:[.,][0-9]{1,2})?)\s*millones?/gi,
  
  // "$469,581,055.31" o "$469.581.055,31"
  /\$\s*([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)/g,
  
  // "469581055.31 pesos" o "469.581.055,31 pesos"
  /([0-9]{1,3}(?:[.,][0-9]{3})*(?:[.,][0-9]{2})?)\s*pesos/gi,
];

/** Threshold para considerar números similares (±5%) */
const SIMILARITY_THRESHOLD = 0.05;

/** Confidence mínima para considerar verificado */
const MIN_CONFIDENCE = 0.8;

// ============================================================================
// Core Functions
// ============================================================================

/**
 * Extrae números monetarios de un texto
 */
export function extractNumbers(text: string): ExtractedNumber[] {
  const extracted: ExtractedNumber[] = [];
  const seenValues = new Set<number>(); // Evitar duplicados por valor parseado
  const seenPositions = new Set<number>(); // Evitar overlapping matches
  
  for (const pattern of MONEY_PATTERNS) {
    // Reset regex lastIndex
    pattern.lastIndex = 0;
    
    let match;
    while ((match = pattern.exec(text)) !== null) {
      const original = match[0];
      const numberStr = match[1];
      const position = match.index;
      
      // Skip if this position was already covered by another pattern
      let positionCovered = false;
      for (let i = position; i < position + original.length; i++) {
        if (seenPositions.has(i)) {
          positionCovered = true;
          break;
        }
      }
      if (positionCovered) continue;
      
      // Parse number (handle both . and , as thousands/decimal separator)
      let value = parseMoneyString(numberStr);
      
      // Handle "millones" multiplier
      if (original.toLowerCase().includes('millones')) {
        value *= 1_000_000;
      }
      
      // Skip invalid numbers
      if (isNaN(value) || value <= 0) continue;
      
      // Skip if already seen (by value, not string)
      if (seenValues.has(value)) continue;
      seenValues.add(value);
      
      // Mark positions as seen
      for (let i = position; i < position + original.length; i++) {
        seenPositions.add(i);
      }
      
      // Extract context (10 chars before/after)
      const contextStart = Math.max(0, position - 10);
      const contextEnd = Math.min(text.length, position + original.length + 10);
      const context = text.slice(contextStart, contextEnd);
      
      extracted.push({
        value,
        original,
        position,
        context,
      });
    }
  }
  
  // Sort by position
  return extracted.sort((a, b) => a.position - b.position);
}

/**
 * Parsea string monetario a número
 * Handles: "469,581,055.31", "469.581.055,31", "469581055.31"
 */
function parseMoneyString(str: string): number {
  // Remove spaces
  str = str.trim();
  
  // Detect format based on last separator
  const lastComma = str.lastIndexOf(',');
  const lastDot = str.lastIndexOf('.');
  
  let normalized: string;
  
  if (lastComma > lastDot) {
    // European format: 469.581.055,31 → 469581055.31
    normalized = str.replace(/\./g, '').replace(',', '.');
  } else {
    // US format: 469,581,055.31 → 469581055.31
    normalized = str.replace(/,/g, '');
  }
  
  return parseFloat(normalized);
}

/**
 * Verifica si un número existe en los chunks de origen
 */
export function validateNumber(
  number: ExtractedNumber,
  sourceChunks: string[]
): ValidationResult {
  // Search in all source chunks
  for (const chunk of sourceChunks) {
    // Extract numbers from chunk
    const chunkNumbers = extractNumbers(chunk);
    
    for (const chunkNum of chunkNumbers) {
      // Check for exact match
      if (Math.abs(chunkNum.value - number.value) < 1) {
        return {
          number,
          found: true,
          confidence: 1.0,
          sourceChunk: chunk.slice(0, 200) + '...',
          reason: `Exact match found: ${chunkNum.original}`,
        };
      }
      
      // Check for similar match (within 5%)
      const diff = Math.abs(chunkNum.value - number.value);
      const relativeDiff = diff / Math.max(chunkNum.value, number.value);
      
      if (relativeDiff <= SIMILARITY_THRESHOLD) {
        const confidence = 1.0 - relativeDiff;
        return {
          number,
          found: true,
          confidence,
          sourceChunk: chunk.slice(0, 200) + '...',
          reason: `Similar match found: ${chunkNum.original} (diff: ${(relativeDiff * 100).toFixed(1)}%)`,
        };
      }
    }
  }
  
  // Not found
  return {
    number,
    found: false,
    confidence: 0,
    reason: 'Number not found in source chunks',
  };
}

/**
 * Verifica todos los números de una respuesta
 */
export function validateNumbers(
  numbers: ExtractedNumber[],
  sourceChunks: string[]
): ValidationResult[] {
  return numbers.map(num => validateNumber(num, sourceChunks));
}

/**
 * Genera reporte de verificación completo
 */
export function verifyResponse(
  response: string,
  sourceChunks: string[]
): VerificationReport {
  // Extract numbers from response
  const numbers = extractNumbers(response);
  
  if (numbers.length === 0) {
    // No numbers to verify (might be a qualitative response)
    return {
      totalNumbers: 0,
      verifiedNumbers: 0,
      overallConfidence: 1.0, // No numbers = no hallucination risk
      possibleHallucination: false,
      validations: [],
      message: 'No numeric data to verify',
    };
  }
  
  // Validate each number
  const validations = validateNumbers(numbers, sourceChunks);
  
  // Calculate metrics
  const verifiedCount = validations.filter(v => v.found && v.confidence >= MIN_CONFIDENCE).length;
  const avgConfidence = validations.reduce((sum, v) => sum + v.confidence, 0) / validations.length;
  
  // Detect hallucination (require at least 50% verified)
  const possibleHallucination = verifiedCount < numbers.length * 0.5; // <50% verified
  
  // Generate message
  let message: string;
  if (avgConfidence >= 0.95) {
    message = 'All numbers verified in source documents';
  } else if (avgConfidence >= 0.8) {
    message = `${verifiedCount}/${numbers.length} numbers verified`;
  } else if (avgConfidence >= 0.5) {
    message = `Some numbers could not be verified (${verifiedCount}/${numbers.length})`;
  } else {
    message = `Most numbers could not be verified (${verifiedCount}/${numbers.length})`;
  }
  
  return {
    totalNumbers: numbers.length,
    verifiedNumbers: verifiedCount,
    overallConfidence: avgConfidence,
    possibleHallucination,
    validations,
    message,
  };
}

/**
 * Agrega badge de confianza a la respuesta
 */
export function addConfidenceBadge(
  response: string,
  report: VerificationReport
): string {
  // Don't add badge if no numbers (qualitative response)
  if (report.totalNumbers === 0) {
    return response;
  }
  
  let badge: string;
  let explanation: string;
  
  if (report.overallConfidence >= 0.95) {
    badge = '✅ **Verificado 100%**';
    explanation = `Todos los datos numéricos (${report.totalNumbers}) fueron verificados en las fuentes originales.`;
  } else if (report.overallConfidence >= 0.8) {
    badge = `⚠️ **Verificado ${(report.overallConfidence * 100).toFixed(0)}%**`;
    explanation = `${report.verifiedNumbers} de ${report.totalNumbers} valores numéricos fueron verificados. Revisar valores no confirmados.`;
  } else if (report.overallConfidence >= 0.5) {
    badge = `⚠️ **Verificación parcial (${(report.overallConfidence * 100).toFixed(0)}%)**`;
    explanation = `Solo ${report.verifiedNumbers} de ${report.totalNumbers} valores pudieron verificarse. Usar con precaución.`;
  } else {
    badge = '❌ **Posible alucinación detectada**';
    explanation = `La mayoría de los valores numéricos (${report.totalNumbers - report.verifiedNumbers}/${report.totalNumbers}) no se encontraron en las fuentes. Verificar manualmente.`;
  }
  
  // Add badge at the beginning
  return `${badge}\n\n${explanation}\n\n---\n\n${response}`;
}

/**
 * Explica resultados de verificación (para debugging)
 */
export function explainVerification(report: VerificationReport): string {
  const lines = [
    `📊 VERIFICATION REPORT`,
    `Total numbers: ${report.totalNumbers}`,
    `Verified: ${report.verifiedNumbers}`,
    `Overall confidence: ${(report.overallConfidence * 100).toFixed(1)}%`,
    `Possible hallucination: ${report.possibleHallucination ? 'YES ⚠️' : 'NO ✅'}`,
    ``,
    `Individual validations:`,
  ];
  
  for (let i = 0; i < report.validations.length; i++) {
    const v = report.validations[i];
    const status = v.found ? '✅' : '❌';
    lines.push(`  ${i + 1}. ${status} ${v.number.original} (confidence: ${(v.confidence * 100).toFixed(0)}%)`);
    lines.push(`     Reason: ${v.reason}`);
  }
  
  return lines.join('\n');
}

/**
 * Verifica si una respuesta necesita verificación
 * (Solo para queries sobre Balance con datos numéricos)
 */
export function needsVerification(query: string, documentType?: string): boolean {
  // Only verify Balance queries
  if (documentType !== 'balances') return false;
  
  // Check if query is asking for numeric data
  const numericKeywords = [
    'saldo', 'monto', 'total', 'cuánto', 'cuanto',
    'valor', 'pesos', 'millones', 'ingresos', 'egresos',
    'gastos', 'presupuesto', 'balance', 'cantidad',
  ];
  
  const normalizedQuery = query.toLowerCase();
  return numericKeywords.some(keyword => normalizedQuery.includes(keyword));
}
