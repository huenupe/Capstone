/**
 * Componente Stepper reutilizable para el checkout
 * Muestra diferentes pasos según si el usuario está logueado o es invitado
 */

const CheckoutStepper = ({ currentStep, isAuthenticated }) => {
  // Para usuarios logueados: 1) Carro 2) Dirección/Entrega 3) Pago
  // Para invitados: 1) Carro 2) Datos de cliente 3) Dirección/Entrega 4) Pago
  
  const steps = isAuthenticated 
    ? [
        { number: 1, label: 'Carro', key: 'cart' },
        { number: 2, label: 'Dirección', key: 'address' },
        { number: 3, label: 'Pago', key: 'payment' },
      ]
    : [
        { number: 1, label: 'Carro', key: 'cart' },
        { number: 2, label: 'Datos', key: 'customer' },
        { number: 3, label: 'Dirección', key: 'address' },
        { number: 4, label: 'Pago', key: 'payment' },
      ]

  const getStepStatus = (step) => {
    const stepIndex = steps.findIndex(s => s.key === step.key)
    const currentStepIndex = steps.findIndex(s => s.key === currentStep)
    
    if (stepIndex < currentStepIndex) {
      return 'completed'
    } else if (stepIndex === currentStepIndex) {
      return 'current'
    } else {
      return 'pending'
    }
  }

  return (
    <div className="flex items-center justify-center mb-8" role="progressbar" aria-valuenow={steps.findIndex(s => s.key === currentStep) + 1} aria-valuemin={1} aria-valuemax={steps.length}>
      <div className="flex items-center">
        {steps.map((step, index) => {
          const status = getStepStatus(step, index)
          const isCompleted = status === 'completed'
          const isCurrent = status === 'current'
          
          return (
            <div key={step.key} className="flex items-center">
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                    isCompleted
                      ? 'bg-green-500 text-white'
                      : isCurrent
                      ? 'bg-primary-600 text-white'
                      : 'bg-gray-300 text-gray-600'
                  }`}
                  aria-current={isCurrent ? 'step' : undefined}
                >
                  {isCompleted ? (
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.number
                  )}
                </div>
                <span className={`mt-2 text-xs font-medium ${
                  isCurrent ? 'text-primary-600' : isCompleted ? 'text-green-600' : 'text-gray-500'
                }`}>
                  {step.label}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`w-16 md:w-24 h-1 mx-2 transition-colors ${
                    isCompleted ? 'bg-green-500' : isCurrent ? 'bg-primary-600' : 'bg-gray-300'
                  }`}
                  aria-hidden="true"
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default CheckoutStepper

