import { Link } from 'react-router-dom'

const Footer = () => {
  return (
    <footer className="bg-gray-800 text-gray-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <h3 className="text-white text-lg font-semibold mb-4">CondorShop</h3>
            <p className="text-sm">
              Tu tienda online de confianza. Encuentra los mejores productos con envío rápido y seguro.
            </p>
          </div>
          
          <div>
            <h4 className="text-white text-sm font-semibold mb-4">Enlaces</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link to="/" className="hover:text-white transition-colors">
                  Inicio
                </Link>
              </li>
              <li>
                <Link to="/cart" className="hover:text-white transition-colors">
                  Carrito
                </Link>
              </li>
            </ul>
          </div>
          
          <div>
            <h4 className="text-white text-sm font-semibold mb-4">Contacto</h4>
            <p className="text-sm">
              Email: contacto@condorshop.cl
            </p>
            <p className="text-sm mt-2">
              Teléfono: +56 9 1234 5678
            </p>
          </div>
        </div>
        
        <div className="border-t border-gray-700 mt-8 pt-8 text-center text-sm">
          <p>&copy; {new Date().getFullYear()} CondorShop. Todos los derechos reservados.</p>
        </div>
      </div>
    </footer>
  )
}

export default Footer





