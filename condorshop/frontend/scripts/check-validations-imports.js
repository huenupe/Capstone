#!/usr/bin/env node

/**
 * Script para verificar que todos los imports desde utils/validations.js
 * correspondan a funciones realmente exportadas
 * 
 * Uso: node scripts/check-validations-imports.js
 */

import { readFileSync, readdirSync, statSync } from 'fs'
import { join, dirname, resolve } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const FRONTEND_ROOT = resolve(__dirname, '..')
const SRC_DIR = join(FRONTEND_ROOT, 'src')

// Funciones exportadas en validations.js
const VALIDATION_EXPORTS = [
  'validateName',
  'validateOnlyLetters',
  'validateChileanPhone',
  'validateEmail',
  'validatePassword',
  'validatePostalCode',
  'validatePasswordMatch',
]

// Leer validations.js para obtener exports reales
function getValidationsExports() {
  const validationsPath = join(SRC_DIR, 'utils', 'validations.js')
  const content = readFileSync(validationsPath, 'utf-8')
  
  // Extraer exports nombrados
  const exportRegex = /export\s+(?:const|function)\s+(\w+)/g
  const exports = []
  let match
  
  while ((match = exportRegex.exec(content)) !== null) {
    exports.push(match[1])
  }
  
  return exports
}

// Buscar todos los archivos .jsx y .js en src
function findSourceFiles(dir, fileList = []) {
  const files = readdirSync(dir)
  
  for (const file of files) {
    const filePath = join(dir, file)
    const stat = statSync(filePath)
    
    if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
      findSourceFiles(filePath, fileList)
    } else if (file.match(/\.(js|jsx)$/)) {
      fileList.push(filePath)
    }
  }
  
  return fileList
}

// Extraer imports de validations de un archivo
function extractValidationsImports(filePath) {
  const content = readFileSync(filePath, 'utf-8')
  const imports = []
  
  // Buscar imports desde validations
  const importRegex = /import\s+{([^}]+)}\s+from\s+['"]\.\.?\/.*validations['"]/g
  let match
  
  while ((match = importRegex.exec(content)) !== null) {
    const importsList = match[1]
    // Extraer nombres individuales
    importsList.split(',').forEach(imp => {
      const name = imp.trim().split(/\s+as\s+/)[0].trim()
      if (name) {
        imports.push(name)
      }
    })
  }
  
  return imports
}

// Ejecutar verificación
function main() {
  console.log('🔍 Verificando imports de validations...\n')
  
  const actualExports = getValidationsExports()
  console.log(`✅ Funciones exportadas en validations.js: ${actualExports.join(', ')}\n`)
  
  const sourceFiles = findSourceFiles(SRC_DIR)
  const errors = []
  const warnings = []
  
  sourceFiles.forEach(filePath => {
    const imports = extractValidationsImports(filePath)
    
    if (imports.length > 0) {
      const relativePath = filePath.replace(FRONTEND_ROOT + '/', '')
      
      imports.forEach(imp => {
        if (!actualExports.includes(imp)) {
          errors.push(`❌ ${relativePath}: importa '${imp}' que no existe en validations.js`)
        }
      })
    }
  })
  
  // Verificar que todas las funciones exportadas se usen
  const allImports = new Set()
  sourceFiles.forEach(filePath => {
    extractValidationsImports(filePath).forEach(imp => allImports.add(imp))
  })
  
  actualExports.forEach(exp => {
    if (!allImports.has(exp)) {
      warnings.push(`⚠️  '${exp}' está exportada pero nunca se importa`)
    }
  })
  
  // Reportar resultados
  if (errors.length === 0 && warnings.length === 0) {
    console.log('✅ Todos los imports son válidos!\n')
    process.exit(0)
  }
  
  if (errors.length > 0) {
    console.log('❌ Errores encontrados:\n')
    errors.forEach(err => console.log(err))
    console.log('')
  }
  
  if (warnings.length > 0) {
    console.log('⚠️  Advertencias:\n')
    warnings.forEach(warn => console.log(warn))
    console.log('')
  }
  
  process.exit(errors.length > 0 ? 1 : 0)
}

main()

