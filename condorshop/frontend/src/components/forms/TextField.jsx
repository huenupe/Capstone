const TextField = ({
  label,
  name,
  type = 'text',
  value,
  onChange,
  register,
  validation,
  error,
  placeholder,
  helperText,
  required = false,
  disabled = false,
  className = '',
  ...props
}) => {
  const inputProps = register
    ? register(name, validation)
    : {
        value: value || '',
        onChange,
      }

  return (
    <div className={`mb-4 ${className}`}>
      {label && (
        <label htmlFor={name} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      {type === 'textarea' ? (
        <textarea
          id={name}
          name={name}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          rows={4}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            error ? 'border-red-500' : 'border-gray-300'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          {...inputProps}
          {...props}
        />
      ) : (
        <input
          type={type}
          id={name}
          name={name}
          placeholder={placeholder}
          required={required}
          disabled={disabled}
          aria-invalid={error ? 'true' : 'false'}
          aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
            error ? 'border-red-500' : 'border-gray-300'
          } ${disabled ? 'bg-gray-100 cursor-not-allowed' : ''}`}
          {...inputProps}
          {...props}
        />
      )}
      {helperText && !error && (
        <p id={`${name}-helper`} className="mt-1 text-sm text-gray-500">{helperText}</p>
      )}
      {error && (
        <p id={`${name}-error`} className="mt-1 text-sm text-red-600" role="alert">{error}</p>
      )}
    </div>
  )
}

export default TextField

