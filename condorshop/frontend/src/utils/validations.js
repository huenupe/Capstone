/**
 * Utilidades de validación reutilizables
 */

/**
 * Valida que el texto contenga solo letras y espacios
 */
export const validateOnlyLetters = (value) => {
  if (!value) return true // Permitir vacío si no es requerido
  const lettersRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s]+$/
  return lettersRegex.test(value) || 'Solo se permiten letras y espacios'
}

/**
 * Valida formato de teléfono chileno: +569 + 8 dígitos (total 12 caracteres)
 */
export const validateChileanPhone = (value) => {
  if (!value) return true // Permitir vacío si no es requerido
  const phoneRegex = /^\+569\d{8}$/
  return phoneRegex.test(value) || 'Debe ser formato: +569 + 8 dígitos (ej: +56912345678)'
}

/**
 * Valida formato de email
 */
export const validateEmail = (value) => {
  if (!value) return true
  const emailRegex = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i
  return emailRegex.test(value) || 'Email inválido'
}

/**
 * Valida que la contraseña tenga al menos 8 caracteres
 */
export const validatePassword = (value) => {
  if (!value) return true
  return value.length >= 8 || 'La contraseña debe tener al menos 8 caracteres'
}

