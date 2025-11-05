import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

// Función para montar la aplicación de forma segura
function mountApp() {
  // Validación del elemento root antes de montar
  const rootElement = document.getElementById('root')

  if (!rootElement) {
    console.error('Root element not found. Make sure <div id="root"></div> exists in index.html')
    document.body.innerHTML = `
      <div style="padding: 20px; font-family: sans-serif;">
        <h1>Error: Elemento root no encontrado</h1>
        <p>Verifica que index.html tenga &lt;div id="root"&gt;&lt;/div&gt;</p>
        <button onclick="window.location.reload()">Recargar</button>
      </div>
    `
    return
  }

  // Crear root y montar app con manejo de errores
  try {
    const root = ReactDOM.createRoot(rootElement)
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>
    )
  } catch (error) {
    console.error('Error mounting React app:', error)
    rootElement.innerHTML = `
      <div style="padding: 20px; font-family: sans-serif;">
        <h1>Error al cargar la aplicación</h1>
        <p>${error.message || 'Error desconocido'}</p>
        <button onclick="window.location.reload()">Recargar</button>
      </div>
    `
  }
}

// Esperar a que el DOM esté completamente cargado
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', mountApp)
} else {
  // DOM ya está listo
  mountApp()
}





