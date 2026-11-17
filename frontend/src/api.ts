import type {
  AdminStats,
  Cart,
  Category,
  CheckoutPayload,
  ModelMetrics,
  Order,
  Product,
  ProductList,
  Recommendation,
  Review,
  User,
} from './types'

const TOKEN_KEY = 'shopwise_token'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {})
  if (options.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const token = getToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(path, { ...options, headers })
  } catch {
    throw new ApiError('Could not reach the Shopwise API. Is the backend running?', 0)
  }
  if (response.status === 401 && token) {
    window.dispatchEvent(new Event('shopwise:unauthorized'))
  }
  if (!response.ok) {
    let message = 'Something went wrong. Please try again.'
    try {
      const data = await response.json()
      if (typeof data.detail === 'string') message = data.detail
      else if (Array.isArray(data.detail)) message = data.detail[0]?.msg || message
    } catch {
      /* keep generic message */
    }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function qs(params: Record<string, string | number | boolean | undefined | null>) {
  const search = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value))
  })
  const text = search.toString()
  return text ? `?${text}` : ''
}

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    }),
  register: (name: string, email: string, password: string) =>
    request<{ access_token: string; user: User }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    }),
  me: () => request<User>('/api/auth/me'),

  categories: () => request<Category[]>('/api/products/categories'),
  products: (params: Record<string, string | number | boolean | undefined>) =>
    request<ProductList>(`/api/products${qs(params)}`),
  product: (id: number | string) => request<Product>(`/api/products/${id}`),
  reviews: (id: number | string) => request<Review[]>(`/api/products/${id}/reviews`),
  createReview: (id: number | string, payload: { rating: number; title: string; comment: string }) =>
    request<Review>(`/api/products/${id}/reviews`, { method: 'POST', body: JSON.stringify(payload) }),

  homeRecommendations: (limit = 8) => request<Recommendation>(`/api/recommendations/home?limit=${limit}`),
  similar: (id: number | string, limit = 8) =>
    request<Recommendation>(`/api/recommendations/similar/${id}?limit=${limit}`),
  alsoBought: (id: number | string, limit = 8) =>
    request<Recommendation>(`/api/recommendations/also-bought/${id}?limit=${limit}`),
  trending: (limit = 8) => request<Recommendation>(`/api/recommendations/trending?limit=${limit}`),
  modelInfo: () => request<Record<string, unknown>>('/api/recommendations/model-info'),

  cart: () => request<Cart>('/api/cart'),
  addToCart: (productId: number, quantity = 1) =>
    request<Cart>('/api/cart/items', { method: 'POST', body: JSON.stringify({ product_id: productId, quantity }) }),
  updateCart: (itemId: number, quantity: number) =>
    request<Cart>(`/api/cart/items/${itemId}`, { method: 'PATCH', body: JSON.stringify({ quantity }) }),
  removeCartItem: (itemId: number) => request<Cart>(`/api/cart/items/${itemId}`, { method: 'DELETE' }),
  clearCart: () => request<Cart>('/api/cart', { method: 'DELETE' }),

  orders: () => request<Order[]>('/api/orders'),
  order: (id: number | string) => request<Order>(`/api/orders/${id}`),
  checkout: (payload: CheckoutPayload) =>
    request<Order>('/api/orders/checkout', { method: 'POST', body: JSON.stringify(payload) }),

  logEvent: (productId: number, eventType: 'view' | 'cart_add' | 'purchase' = 'view') =>
    request<{ message: string }>('/api/events', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, event_type: eventType, meta: { surface: 'web' } }),
    }).catch(() => ({ message: 'ignored' })),

  adminStats: () => request<AdminStats>('/api/admin/stats'),
  adminProducts: (search = '') => request<Product[]>(`/api/admin/products${qs({ search })}`),
  adminCreateProduct: (payload: Record<string, unknown>) =>
    request<Product>('/api/admin/products', { method: 'POST', body: JSON.stringify(payload) }),
  adminUpdateProduct: (id: number, payload: Record<string, unknown>) =>
    request<Product>(`/api/admin/products/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
  adminDeleteProduct: (id: number) =>
    request<{ message: string }>(`/api/admin/products/${id}`, { method: 'DELETE' }),
  adminOrders: (limit = 500) => request<Order[]>(`/api/admin/orders?limit=${limit}`),
  adminMetrics: () => request<ModelMetrics>('/api/admin/model-metrics'),
  adminRetrain: () => request<{ message: string; detail: string }>('/api/admin/retrain', { method: 'POST' }),
  adminUsers: () => request<{ id: number; name: string; email: string; joined: string; orders: number }[]>('/api/admin/users'),
}

export const money = (value: number) =>
  new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2 }).format(value)

export const shortDate = (value: string) =>
  new Date(value).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })

export const longDate = (value: string) =>
  new Date(value).toLocaleDateString('en-US', { weekday: 'short', month: 'long', day: 'numeric', year: 'numeric' })

export const categorySlug = (name: string) =>
  name.toLowerCase().replace(/&/g, ' ').replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '')
