/**
 * Utilidades de validación reutilizables
 * Todas las funciones exportadas son named exports para consistencia
 */

/**
 * Valida que el texto contenga solo letras, espacios, guiones y apóstrofes
 * Min 2, max 50 caracteres
 */
export const validateName = (value) => {
  if (!value) return true
  if (value.length < 2) return 'Debe tener al menos 2 caracteres'
  if (value.length > 50) return 'Debe tener máximo 50 caracteres'
  const nameRegex = /^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]+$/
  return nameRegex.test(value) || 'Solo se permiten letras, espacios, guiones y apóstrofes'
}

/**
 * Alias de validateName para mantener compatibilidad
 * Valida que el texto contenga solo letras, espacios, guiones y apóstrofes
 * Min 2, max 50 caracteres
 */
export const validateOnlyLetters = validateName

/**
 * Valida formato de teléfono chileno: +569 + 8 dígitos (total 12 caracteres)
 */
export const validateChileanPhone = (value) => {
  if (!value) return true
  const phoneRegex = /^\+569\d{8}$/
  return phoneRegex.test(value) || 'Formato: +569 + 8 dígitos (ej: +56912345678)'
}

/**
 * Valida formato de email (RFC 5322 simplificado)
 */
export const validateEmail = (value) => {
  if (!value) return true
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(value) || 'Email inválido'
}

/**
 * Valida que la contraseña tenga al menos 8 caracteres, una letra y un número
 */
export const validatePassword = (value) => {
  if (!value) return true
  if (value.length < 8) return 'Debe tener al menos 8 caracteres'
  if (!/[a-zA-Z]/.test(value)) return 'Debe contener al menos una letra'
  if (!/\d/.test(value)) return 'Debe contener al menos un número'
  return true
}

/**
 * Valida código postal (solo números, 5-7 dígitos)
 */
export const validatePostalCode = (value) => {
  if (!value) return true
  const postalRegex = /^\d{5,7}$/
  return postalRegex.test(value) || 'Código postal inválido (5-7 dígitos)'
}

/**
 * Valida confirmación de contraseña
 */
export const validatePasswordMatch = (password) => (value) => {
  if (!value) return true
  return value === password || 'Las contraseñas no coinciden'
}

