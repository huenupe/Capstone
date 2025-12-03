import { create } from 'zustand'
import { ordersService } from '../services/orders'

// Tiempo de cache: 3 minutos (180 segundos)
const CACHE_DURATION_MS = 180 * 1000

export const useOrdersStore = create((set, get) => ({
  orders: [],
  pagination: {
    count: 0,
    next: null,
    previous: null,
    currentPage: 1,
    pageSize: 20,
  },
  isLoadingOrders: false,
  errorOrders: null,
  lastFetchedAt: null,
  fetchInProgress: false,
  prefetchedNextPage: null, // Buffer para prefetch de siguiente página

  /**
   * Fetch de órdenes con cache inteligente y paginación.
   * Solo hace request si:
   * - No hay órdenes en memoria, O
   * - Los datos tienen más de 2-3 minutos de antigüedad, O
   * - Se fuerza con force=true
   * 
   * ✅ OPTIMIZACIÓN: Evita múltiples requests duplicados si ya hay datos frescos.
   * ✅ PAGINACIÓN: Soporta paginación para reducir carga inicial.
   * 
   * @param {boolean} force - Forzar fetch incluso si hay datos frescos
   * @param {Object} paginationParams - { page: 1, page_size: 20 }
   * @returns {Promise<void>}
   */
  fetchOrdersOnce: async (force = false, paginationParams = {}) => {
    const { orders, lastFetchedAt, fetchInProgress, pagination } = get()
    
    // Evitar múltiples fetches simultáneos
    if (fetchInProgress) {
      if (import.meta.env.DEV) {
        console.log('[ordersStore] fetchOrdersOnce ya en progreso, omitiendo...')
      }
      return
    }
    
    // Verificar cache (2-3 minutos) - solo si no hay paginación nueva
    const now = Date.now()
    const cacheValid = lastFetchedAt && (now - lastFetchedAt) < CACHE_DURATION_MS
    const isNewPage = paginationParams.page && paginationParams.page !== pagination.currentPage
    
    if (!force && orders.length > 0 && cacheValid && !isNewPage) {
      if (import.meta.env.DEV) {
        console.log('[ordersStore] Usando datos cacheados (frescos)')
      }
      return
    }
    
    set({ fetchInProgress: true, isLoadingOrders: true, errorOrders: null })
    
    try {
      if (import.meta.env.DEV) {
        console.time('GET /api/orders/ (store)')
      }
      
      // Usar paginación si se proporciona, sino usar defaults
      const params = {
        page: paginationParams.page || pagination.currentPage || 1,
        page_size: paginationParams.page_size || pagination.pageSize || 20,
      }
      
      const data = await ordersService.getUserOrders(params)
      
      if (import.meta.env.DEV) {
        console.timeEnd('GET /api/orders/ (store)')
        console.log('[ordersStore] Orders fetched:', data)
      }
      
      // Si la respuesta tiene paginación (count, next, previous)
      if (data.count !== undefined) {
        set({
          orders: Array.isArray(data.results) ? data.results : [],
          pagination: {
            count: data.count || 0,
            next: data.next || null,
            previous: data.previous || null,
            currentPage: params.page,
            pageSize: params.page_size,
          },
          lastFetchedAt: now,
          errorOrders: null,
        })
        
        // ✅ PREFETCH: Cargar siguiente página en background si existe y no se fuerza
        if (data.next && !force) {
          // Prefetch en background sin bloquear UI
          get().prefetchNextPage(data.next).catch(err => {
            if (import.meta.env.DEV) {
              console.log('[ordersStore] Prefetch falló (no crítico):', err)
            }
          })
        }
      } else {
        // Fallback: respuesta sin paginación
        set({
          orders: Array.isArray(data) ? data : [],
          lastFetchedAt: now,
          errorOrders: null,
        })
      }
    } catch (error) {
      console.error('[ordersStore] Error fetching orders:', error)
      
      // ✅ MEJORA: Manejo de errores HTTP (401/403 → limpiar órdenes)
      const status = error.response?.status
      if (status === 401 || status === 403) {
        // Usuario no autenticado o sin permisos → limpiar estado
        get().clearOrders()
      }
      
      set({ 
        errorOrders: error.response?.data?.error || 'Error al cargar los pedidos' 
      })
      throw error
    } finally {
      set({ fetchInProgress: false, isLoadingOrders: false })
    }
  },

  /**
   * Prefetch de la siguiente página en background
   * Almacena los datos en prefetchedNextPage para uso futuro
   * @param {string} nextUrl - URL de la siguiente página
   * @returns {Promise<void>}
   */
  prefetchNextPage: async (nextUrl) => {
    try {
      if (import.meta.env.DEV) {
        console.log('[ordersStore] Prefetching next page:', nextUrl)
      }
      
      // Extraer parámetros de la URL
      const url = new URL(nextUrl, window.location.origin)
      const page = parseInt(url.searchParams.get('page') || '1')
      const pageSize = parseInt(url.searchParams.get('page_size') || '20')
      
      // Hacer fetch en background
      const data = await ordersService.getUserOrders({ page, page_size: pageSize })
      
      if (data.count !== undefined && Array.isArray(data.results)) {
        set({ prefetchedNextPage: data })
        
        if (import.meta.env.DEV) {
          console.log('[ordersStore] Prefetch completado:', data.results.length, 'items')
        }
      }
    } catch (error) {
      // Prefetch falla silenciosamente (no crítico)
      if (import.meta.env.DEV) {
        console.log('[ordersStore] Prefetch error (no crítico):', error)
      }
    }
  },

  /**
   * Limpiar estado de órdenes (útil al cerrar sesión)
   * ✅ MEJORA: Resetea completamente pagination y prefetch
   */
  clearOrders: () => {
    set({ 
      orders: [],
      pagination: {
        count: 0,
        next: null,
        previous: null,
        currentPage: 1,
        pageSize: 20,
      },
      lastFetchedAt: null,
      errorOrders: null,
      prefetchedNextPage: null,
    })
  },
}))

