const Spinner = ({ size = 'md', className = '' }) => {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  }
  
  return (
    <div className={`inline-block ${sizes[size]} ${className}`}>
      <div className="animate-spin rounded-full border-4 border-gray-200 border-t-primary-600"></div>
    </div>
  )
}

export default Spinner





