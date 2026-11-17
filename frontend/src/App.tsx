import { useEffect } from 'react'
import { BrowserRouter, Outlet, Route, Routes, useLocation } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { CartProvider } from './context/CartContext'
import { ToastProvider } from './context/ToastContext'
import { Navbar } from './components/Navbar'
import { Footer } from './components/Footer'
import { CinematicSplash } from './components/CinematicSplash'
import { ProtectedRoute } from './components/ProtectedRoute'
import { HomePage } from './pages/HomePage'
import { ProductsPage } from './pages/ProductsPage'
import { ProductPage } from './pages/ProductPage'
import { CartPage } from './pages/CartPage'
import { CheckoutPage } from './pages/CheckoutPage'
import { OrderSuccessPage } from './pages/OrderSuccessPage'
import { OrdersPage } from './pages/OrdersPage'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { AdminLayout } from './pages/admin/AdminLayout'
import { AdminDashboard } from './pages/admin/AdminDashboard'
import { AdminProducts } from './pages/admin/AdminProducts'
import { AdminOrders } from './pages/admin/AdminOrders'
import { AdminModel } from './pages/admin/AdminModel'

function ScrollToTop() {
  const { pathname, search } = useLocation()
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' })
  }, [pathname, search])
  return null
}

function StorefrontLayout() {
  return (
    <>
      <Navbar />
      <main className="site-main">
        <Outlet />
      </main>
      <Footer />
    </>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <CinematicSplash />
      <ToastProvider>
        <AuthProvider>
          <CartProvider>
            <ScrollToTop />
            <Routes>
              <Route element={<StorefrontLayout />}>
                <Route index element={<HomePage />} />
                <Route path="shop" element={<ProductsPage />} />
                <Route path="product/:id" element={<ProductPage />} />
                <Route path="cart" element={<CartPage />} />
                <Route path="checkout" element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
                <Route path="orders" element={<ProtectedRoute><OrdersPage /></ProtectedRoute>} />
                <Route path="order-success/:id" element={<ProtectedRoute><OrderSuccessPage /></ProtectedRoute>} />
                <Route path="*" element={<NotFoundPage />} />
              </Route>

              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />

              <Route
                path="admin"
                element={
                  <ProtectedRoute admin>
                    <AdminLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<AdminDashboard />} />
                <Route path="products" element={<AdminProducts />} />
                <Route path="orders" element={<AdminOrders />} />
                <Route path="model" element={<AdminModel />} />
              </Route>
            </Routes>
          </CartProvider>
        </AuthProvider>
      </ToastProvider>
    </BrowserRouter>
  )
}
