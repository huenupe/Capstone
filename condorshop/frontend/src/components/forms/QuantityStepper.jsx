const QuantityStepper = ({
  value,
  onChange,
  min = 1,
  max = 999,
  disabled = false,
  className = '',
}) => {
  const handleDecrease = () => {
    if (value > min) {
      onChange(value - 1)
    }
  }

  const handleIncrease = () => {
    if (value < max) {
      onChange(value + 1)
    }
  }

  const handleChange = (e) => {
    const newValue = parseInt(e.target.value) || min
    if (newValue >= min && newValue <= max) {
      onChange(newValue)
    }
  }

  return (
    <div className={`flex items-center border rounded-lg ${className}`}>
      <button
        type="button"
        onClick={handleDecrease}
        disabled={disabled || value <= min}
        className="px-3 py-1 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
        </svg>
      </button>
      
      <input
        type="number"
        value={value}
        onChange={handleChange}
        min={min}
        max={max}
        disabled={disabled}
        className="w-16 text-center border-0 focus:outline-none focus:ring-0 disabled:bg-gray-100"
      />
      
      <button
        type="button"
        onClick={handleIncrease}
        disabled={disabled || value >= max}
        className="px-3 py-1 text-gray-600 hover:text-gray-800 disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none"
      >
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
      </button>
    </div>
  )
}

export default QuantityStepper





