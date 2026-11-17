import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../api'
import type { Cart } from '../types'
import { useAuth } from './AuthContext'

interface CartValue {
  cart: Cart
  loading: boolean
  refresh: () => Promise<void>
  add: (productId: number, quantity?: number) => Promise<void>
  update: (itemId: number, quantity: number) => Promise<void>
  remove: (itemId: number) => Promise<void>
  clear: () => Promise<void>
}

const EMPTY_CART: Cart = { items: [], subtotal: 0, count: 0 }
const CartContext = createContext<CartValue | undefined>(undefined)

export function CartProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const [cart, setCart] = useState<Cart>(EMPTY_CART)
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    if (!user) {
      setCart(EMPTY_CART)
      return
    }
    setLoading(true)
    try {
      setCart(await api.cart())
    } catch {
      setCart(EMPTY_CART)
    } finally {
      setLoading(false)
    }
  }, [user])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const add = useCallback(async (productId: number, quantity = 1) => {
    setCart(await api.addToCart(productId, quantity))
  }, [])

  const update = useCallback(async (itemId: number, quantity: number) => {
    setCart(await api.updateCart(itemId, quantity))
  }, [])

  const remove = useCallback(async (itemId: number) => {
    setCart(await api.removeCartItem(itemId))
  }, [])

  const clear = useCallback(async () => {
    setCart(await api.clearCart())
  }, [])

  const value = useMemo(
    () => ({ cart, loading, refresh, add, update, remove, clear }),
    [cart, loading, refresh, add, update, remove, clear],
  )

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>
}

export function useCart() {
  const context = useContext(CartContext)
  if (!context) throw new Error('useCart must be used inside CartProvider')
  return context
}
