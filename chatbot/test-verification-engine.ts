/**
 * Test Suite: VerificationEngine (Layer 4)
 * 
 * Valida detección de alucinaciones numéricas en respuestas Balance
 */

import {
  extractNumbers,
  validateNumber,
  validateNumbers,
  verifyResponse,
  addConfidenceBadge,
  needsVerification,
  explainVerification,
  type ExtractedNumber,
  type ValidationResult,
  type VerificationReport,
} from './src/lib/rag/verification-engine';

// ============================================================================
// Mock Data
// ============================================================================

const mockSourceChunks = [
  `Balance Carlos Tejedor 2024-T1:
   Saldo Inicial: $469,581,055.31
   Total Ingresos: $185,233,456.78
   Total Egresos: $157,891,234.56
   Saldo Final: $496,923,277.53`,
  
  `Detalle de Ingresos:
   | Código | Descripción | Monto |
   | 111210108 | Sueldos Personal | $136,995,512.25 |
   | 111210208 | Cargas Sociales | $28,450,123.45 |`,
  
  `Gastos en Servicios:
   Total gastado: $45,678,901.23
   Principales rubros:
   - Servicios públicos: $12,345,678.90
   - Mantenimiento: $8,234,567.89`,
];

// ============================================================================
// Test Cases
// ============================================================================

interface TestCase {
  name: string;
  response: string;
  expectedNumbers: number;
  expectedVerified: number;
  expectedConfidence: 'high' | 'medium' | 'low';
  expectedHallucination: boolean;
}

const testCases: TestCase[] = [
  {
    name: 'Test 1: Respuesta 100% correcta',
    response: 'El saldo inicial de Carlos Tejedor en 2024-T1 es $469,581,055.31 y el saldo final es $496,923,277.53.',
    expectedNumbers: 2,
    expectedVerified: 2,
    expectedConfidence: 'high', // >=0.95
    expectedHallucination: false,
  },
  
  {
    name: 'Test 2: Respuesta con números aproximados',
    response: 'El saldo inicial es aproximadamente $469.5 millones y el final $497 millones.',
    expectedNumbers: 2,
    expectedVerified: 2,
    expectedConfidence: 'high', // Similarity match
    expectedHallucination: false,
  },
  
  {
    name: 'Test 3: Respuesta parcialmente correcta',
    response: 'El total de ingresos fue $185,233,456.78 pero los egresos fueron $200,000,000 (INCORRECTO).',
    expectedNumbers: 2,
    expectedVerified: 1,
    expectedConfidence: 'medium', // 0.5-0.8
    expectedHallucination: false, // 50% verified
  },
  
  {
    name: 'Test 4: Alucinación detectada',
    response: 'El saldo inicial es $999,999,999.99 y el final $888,888,888.88.',
    expectedNumbers: 2,
    expectedVerified: 0,
    expectedConfidence: 'low', // <0.5
    expectedHallucination: true,
  },
  
  {
    name: 'Test 5: Respuesta cualitativa (sin números)',
    response: 'El balance muestra una gestión fiscal responsable con superávit operativo.',
    expectedNumbers: 0,
    expectedVerified: 0,
    expectedConfidence: 'high', // No numbers = no risk
    expectedHallucination: false,
  },
  
  {
    name: 'Test 6: Mezcla de formatos',
    response: 'Los sueldos suman $136,995,512.25 y los servicios $45.678.901,23 (formato europeo).',
    expectedNumbers: 2,
    expectedVerified: 2,
    expectedConfidence: 'high',
    expectedHallucination: false,
  },
];

// ============================================================================
// Test Execution
// ============================================================================

console.log('='.repeat(80));
console.log('TEST: VerificationEngine (Layer 4)');
console.log('='.repeat(80));
console.log();

let passedTests = 0;
let failedTests = 0;

for (let i = 0; i < testCases.length; i++) {
  const test = testCases[i];
  
  console.log(`${test.name}`);
  console.log(`Response: "${test.response.slice(0, 100)}..."`);
  console.log();
  
  // Run verification
  const report = verifyResponse(test.response, mockSourceChunks);
  
  console.log('Result:');
  console.log(`Total numbers: ${report.totalNumbers}`);
  console.log(`Verified: ${report.verifiedNumbers}`);
  console.log(`Confidence: ${(report.overallConfidence * 100).toFixed(1)}%`);
  console.log(`Hallucination: ${report.possibleHallucination ? 'YES ⚠️' : 'NO ✅'}`);
  console.log();
  
  // Validate results
  let testPassed = true;
  
  // Check total numbers
  if (report.totalNumbers !== test.expectedNumbers) {
    console.log(`✗ Total numbers: expected ${test.expectedNumbers}, got ${report.totalNumbers} ❌`);
    testPassed = false;
  } else {
    console.log(`✓ Total numbers: ${report.totalNumbers} ✅`);
  }
  
  // Check verified count
  if (report.verifiedNumbers !== test.expectedVerified) {
    console.log(`✗ Verified: expected ${test.expectedVerified}, got ${report.verifiedNumbers} ❌`);
    testPassed = false;
  } else {
    console.log(`✓ Verified: ${report.verifiedNumbers} ✅`);
  }
  
  // Check confidence level
  let confidenceLevel: 'high' | 'medium' | 'low';
  if (report.overallConfidence >= 0.95) confidenceLevel = 'high';
  else if (report.overallConfidence >= 0.5) confidenceLevel = 'medium';
  else confidenceLevel = 'low';
  
  if (confidenceLevel !== test.expectedConfidence) {
    console.log(`✗ Confidence: expected ${test.expectedConfidence}, got ${confidenceLevel} ❌`);
    testPassed = false;
  } else {
    console.log(`✓ Confidence: ${confidenceLevel} ✅`);
  }
  
  // Check hallucination detection
  if (report.possibleHallucination !== test.expectedHallucination) {
    console.log(`✗ Hallucination: expected ${test.expectedHallucination}, got ${report.possibleHallucination} ❌`);
    testPassed = false;
  } else {
    console.log(`✓ Hallucination: ${report.possibleHallucination} ✅`);
  }
  
  if (testPassed) {
    console.log(`\n✅ Test ${i + 1} PASSED`);
    passedTests++;
  } else {
    console.log(`\n❌ Test ${i + 1} FAILED`);
    failedTests++;
  }
  
  console.log('-'.repeat(80));
  console.log();
}

// ============================================================================
// Unit Tests (Functions)
// ============================================================================

console.log('-'.repeat(80));
console.log('UNIT TESTS');
console.log('-'.repeat(80));
console.log();

// Test: extractNumbers()
console.log('Test: extractNumbers()');
const testText = 'El saldo es $469,581,055.31 y gastamos $136.995.512,25 pesos.';
const extracted = extractNumbers(testText);
console.log(`Extracted ${extracted.length} numbers:`);
extracted.forEach(n => {
  console.log(`  - ${n.original} → ${n.value.toLocaleString()}`);
});
if (extracted.length === 2 && Math.abs(extracted[0].value - 469581055.31) < 1) {
  console.log('✅ extractNumbers() works correctly\n');
} else {
  console.log('❌ extractNumbers() failed\n');
  failedTests++;
}

// Test: needsVerification()
console.log('Test: needsVerification()');
const shouldVerify = needsVerification('¿Cuál es el saldo inicial?', 'balances');
const shouldNotVerify = needsVerification('Ordenanza 123', 'ordenanza');
if (shouldVerify && !shouldNotVerify) {
  console.log('✅ needsVerification() works correctly\n');
} else {
  console.log('❌ needsVerification() failed\n');
  failedTests++;
}

// Test: addConfidenceBadge()
console.log('Test: addConfidenceBadge()');
const mockReport: VerificationReport = {
  totalNumbers: 2,
  verifiedNumbers: 2,
  overallConfidence: 1.0,
  possibleHallucination: false,
  validations: [],
  message: 'All verified',
};
const withBadge = addConfidenceBadge('El saldo es $100.', mockReport);
if (withBadge.includes('✅') && withBadge.includes('Verificado 100%')) {
  console.log('✅ addConfidenceBadge() works correctly\n');
} else {
  console.log('❌ addConfidenceBadge() failed\n');
  failedTests++;
}

// ============================================================================
// Summary
// ============================================================================

console.log('='.repeat(80));
console.log('SUMMARY');
console.log('='.repeat(80));
console.log(`Total tests: ${testCases.length + 3}`);
console.log(`Passed: ${passedTests + 3} ✅`);
console.log(`Failed: ${failedTests} ❌`);
console.log(`Success rate: ${(((passedTests + 3) / (testCases.length + 3)) * 100).toFixed(0)}%`);
console.log('='.repeat(80));
console.log();

if (failedTests === 0) {
  console.log('🎯 ALL TESTS PASSED! Layer 4 (VerificationEngine) is working correctly ✅');
  process.exit(0);
} else {
  console.log(`⚠️ ${failedTests} test(s) failed. Please review the implementation.`);
  process.exit(1);
}
