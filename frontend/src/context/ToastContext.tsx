import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { CheckCircle2, AlertCircle, Info, X } from 'lucide-react'

type ToastVariant = 'default' | 'success' | 'error'
interface Toast {
  id: number
  message: string
  variant: ToastVariant
}

interface ToastValue {
  push: (message: string, variant?: ToastVariant) => void
}

const ToastContext = createContext<ToastValue | undefined>(undefined)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])
  const counter = useRef(0)

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((t) => t.id !== id))
  }, [])

  const push = useCallback((message: string, variant: ToastVariant = 'default') => {
    const id = ++counter.current
    setToasts((current) => [...current, { id, message, variant }])
    window.setTimeout(() => remove(id), 3800)
  }, [remove])

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="toast-stack" aria-live="polite">
        {toasts.map((toast) => (
          <div key={toast.id} className={`toast toast--${toast.variant}`}>
            {toast.variant === 'success' ? <CheckCircle2 size={17} /> : toast.variant === 'error' ? <AlertCircle size={17} /> : <Info size={17} />}
            <span>{toast.message}</span>
            <button className="toast__close" onClick={() => remove(toast.id)} aria-label="Dismiss notification">
              <X size={14} />
            </button>
            <div className="toast__progress" />
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  )
}

export function useToast() {
  const context = useContext(ToastContext)
  if (!context) throw new Error('useToast must be used inside ToastProvider')
  return context
}
