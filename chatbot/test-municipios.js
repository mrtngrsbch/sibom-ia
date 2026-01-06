// Script de prueba para verificar el procesamiento de municipios
const fs = require('fs');
const path = require('path');

// Paths
const rootPath = __dirname;
const mdPath = path.join(rootPath, '..', 'docs', 'Municipios_contenidos.md');
const boletinesPath = path.join(rootPath, '..', 'python-cli', 'boletines');

console.log('=== Verificando rutas ===');
console.log('MD Path:', mdPath);
console.log('MD exists:', fs.existsSync(mdPath));
console.log('Boletines Path:', boletinesPath);
console.log('Boletines exists:', fs.existsSync(boletinesPath));

// Leer MD
console.log('\n=== Leyendo MD ===');
const mdContent = fs.readFileSync(mdPath, 'utf-8');
const lines = mdContent.split('\n');

// Parsear municipios
const municipios = [];
let inTable = false;

for (const line of lines) {
  if (line.startsWith('| Municipio')) {
    inTable = true;
    continue;
  }
  if (inTable && line.startsWith('|')) {
    // Saltar separador
    if (line.includes('--') || line.includes(':--')) continue;

    const parts = line.split('|').map(p => p.trim()).filter(p => p);
    if (parts.length >= 3) {
      const municipio = parts[0];
      const url = parts[1];
      const datos = parts[2];

      // Saltar si no tiene formato válido
      if (!url.includes('http')) continue;

      const match = url.match(/\/cities\/(\d+)/);
      const cityId = match ? parseInt(match[1]) : 0;

      municipios.push({ municipio, url, datos, cityId });
    }
  }
}

console.log(`Municipios encontrados: ${municipios.length}`);
console.log('Primeros 3:', municipios.slice(0, 3));

// Probar con Carlos Tejedor
console.log('\n=== Probando Carlos Tejedor ===');
const carlosTejedor = municipios.find(m => m.municipio.includes('Carlos Tejedor'));
console.log('Municipio:', carlosTejedor);

if (carlosTejedor) {
  const normalizedName = carlosTejedor.municipio
    .replace('Municipio de ', '')
    .replace('Municipio De ', '')
    .replace('Municipio ', '')
    .trim()
    .replace(/ /g, '_');

  console.log('Nombre normalizado:', normalizedName);

  const files = fs.readdirSync(boletinesPath);
  const boletinesFiles = files.filter(f =>
    f.startsWith(normalizedName) && f.endsWith('.json')
  );

  console.log(`Boletines encontrados: ${boletinesFiles.length}`);
  console.log('Primeros 5:', boletinesFiles.slice(0, 5));

  if (boletinesFiles.length > 0) {
    // Leer primer boletín
    const firstFile = boletinesFiles[0];
    const content = fs.readFileSync(path.join(boletinesPath, firstFile), 'utf-8');
    const boletin = JSON.parse(content);

    console.log('\nPrimer boletín:');
    console.log('  Number:', boletin.number);
    console.log('  Date:', boletin.date);
    console.log('  Description:', boletin.description);
  }
}

console.log('\n=== Fin de la prueba ===');
