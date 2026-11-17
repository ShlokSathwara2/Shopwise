import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, ArrowRight, CreditCard, LockKeyhole, ShieldCheck, Truck } from 'lucide-react'
import { api, money } from '../api'
import { useAuth } from '../context/AuthContext'
import { useCart } from '../context/CartContext'
import { useToast } from '../context/ToastContext'
import { ProductImage } from '../components/ProductCard'
import { Breadcrumbs, EmptyState } from '../components/UI'
import type { CheckoutPayload } from '../types'

const initialForm: CheckoutPayload = {
  shipping_name: '',
  shipping_address: '',
  shipping_city: '',
  shipping_postcode: '',
  shipping_country: 'United States',
  payment_name: '',
  payment_card: '',
  payment_expiry: '',
  payment_cvc: '',
}

function formatCard(value: string) {
  return value.replace(/\D/g, '').slice(0, 16).replace(/(.{4})/g, '$1 ').trim()
}

function formatExpiry(value: string) {
  const digits = value.replace(/\D/g, '').slice(0, 4)
  return digits.length > 2 ? `${digits.slice(0, 2)}/${digits.slice(2)}` : digits
}

export function CheckoutPage() {
  const { user } = useAuth()
  const { cart, refresh } = useCart()
  const { push } = useToast()
  const navigate = useNavigate()
  const [form, setForm] = useState<CheckoutPayload>({ ...initialForm, shipping_name: user?.name || '' })
  const [errors, setErrors] = useState<Partial<Record<keyof CheckoutPayload, string>>>({})
  const [processing, setProcessing] = useState(false)

  const set = (key: keyof CheckoutPayload, value: string) => {
    setForm((current) => ({ ...current, [key]: value }))
    setErrors((current) => ({ ...current, [key]: undefined }))
  }

  const useTestCard = () => {
    setForm((current) => ({
      ...current,
      payment_name: current.payment_name || user?.name || 'Sofia Hart',
      payment_card: '4242 4242 4242 4242',
      payment_expiry: '12/29',
      payment_cvc: '123',
    }))
  }

  const validate = () => {
    const next: Partial<Record<keyof CheckoutPayload, string>> = {}
    if (form.shipping_name.trim().length < 2) next.shipping_name = 'Enter the recipient’s full name.'
    if (form.shipping_address.trim().length < 4) next.shipping_address = 'Enter a street address.'
    if (form.shipping_city.trim().length < 2) next.shipping_city = 'Enter a city.'
    if (form.shipping_postcode.trim().length < 2) next.shipping_postcode = 'Enter a postcode.'
    if (form.shipping_country.trim().length < 2) next.shipping_country = 'Enter a country.'
    if (form.payment_name.trim().length < 2) next.payment_name = 'Enter the name on the card.'
    if (form.payment_card.replace(/\D/g, '').length < 12) next.payment_card = 'Enter a valid card number.'
    if (!/^\d{2}\/\d{2}$/.test(form.payment_expiry)) next.payment_expiry = 'Use MM/YY.'
    if (!/^\d{3,4}$/.test(form.payment_cvc)) next.payment_cvc = '3 or 4 digits.'
    setErrors(next)
    if (Object.keys(next).length) {
      const firstKey = Object.keys(next)[0]
      document.querySelector<HTMLElement>(`[name="${firstKey}"]`)?.focus()
      return false
    }
    return true
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!validate()) return
    setProcessing(true)
    try {
      const order = await api.checkout(form)
      await refresh()
      push('Payment authorised — your pieces are on their way.', 'success')
      navigate(`/order-success/${order.id}`, { replace: true, state: { order } })
    } catch (error) {
      push(error instanceof Error ? error.message : 'Checkout could not be completed.', 'error')
    } finally {
      setProcessing(false)
    }
  }

  if (cart.items.length === 0) {
    return (
      <div className="shell section">
        <EmptyState title="Your bag is empty" text="Add a few considered pieces before checking out." action={<Link to="/shop" className="button button--dark">Back to the shop</Link>} />
      </div>
    )
  }

  return (
    <div className="shell section page-checkout">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Bag', to: '/cart' }, { label: 'Checkout' }]} />
      <div className="checkout-topline">
        <div>
          <span className="eyebrow">Step 2 of 3 · Checkout</span>
          <h1>Almost yours.</h1>
        </div>
        <Link to="/cart" className="text-link"><ArrowLeft size={15} /> Back to bag</Link>
      </div>

      <form className="checkout-layout" onSubmit={submit}>
        <div className="checkout-form">
          <section className="form-section">
            <div className="form-section__head">
              <span>01</span>
              <div><h2>Delivery details</h2><p>Where should we send your pieces?</p></div>
            </div>
            <div className="form-grid">
              <label className="field field--full">
                <span>Full name</span>
                <input name="shipping_name" value={form.shipping_name} onChange={(e) => set('shipping_name', e.target.value)} placeholder="Sofia Hart" autoComplete="name" />
                {errors.shipping_name && <small className="field__error">{errors.shipping_name}</small>}
              </label>
              <label className="field field--full">
                <span>Street address</span>
                <input name="shipping_address" value={form.shipping_address} onChange={(e) => set('shipping_address', e.target.value)} placeholder="14 Mercer Walk, Apt 3" autoComplete="street-address" />
                {errors.shipping_address && <small className="field__error">{errors.shipping_address}</small>}
              </label>
              <label className="field">
                <span>City</span>
                <input name="shipping_city" value={form.shipping_city} onChange={(e) => set('shipping_city', e.target.value)} placeholder="New York" autoComplete="address-level2" />
                {errors.shipping_city && <small className="field__error">{errors.shipping_city}</small>}
              </label>
              <label className="field">
                <span>Postcode</span>
                <input name="shipping_postcode" value={form.shipping_postcode} onChange={(e) => set('shipping_postcode', e.target.value)} placeholder="10012" autoComplete="postal-code" />
                {errors.shipping_postcode && <small className="field__error">{errors.shipping_postcode}</small>}
              </label>
              <label className="field field--full">
                <span>Country</span>
                <select name="shipping_country" value={form.shipping_country} onChange={(e) => set('shipping_country', e.target.value)}>
                  {['United States', 'United Kingdom', 'Canada', 'Australia', 'Germany', 'France', 'India'].map((country) => <option key={country}>{country}</option>)}
                </select>
              </label>
            </div>
          </section>

          <section className="form-section">
            <div className="form-section__head">
              <span>02</span>
              <div><h2>Payment</h2><p>Mock payment — no real money moves.</p></div>
              <button type="button" className="test-card-button" onClick={useTestCard}>Use test card</button>
            </div>
            <div className="payment-banner">
              <ShieldCheck size={18} />
              <span>This is a demonstration checkout. Use any card-shaped number; nothing is charged.</span>
            </div>
            <div className="form-grid">
              <label className="field field--full">
                <span>Name on card</span>
                <input name="payment_name" value={form.payment_name} onChange={(e) => set('payment_name', e.target.value)} placeholder="Sofia Hart" autoComplete="cc-name" />
                {errors.payment_name && <small className="field__error">{errors.payment_name}</small>}
              </label>
              <label className="field field--full">
                <span>Card number</span>
                <div className="input-with-icon">
                  <CreditCard size={16} />
                  <input name="payment_card" value={form.payment_card} onChange={(e) => set('payment_card', formatCard(e.target.value))} placeholder="4242 4242 4242 4242" inputMode="numeric" autoComplete="cc-number" />
                </div>
                {errors.payment_card && <small className="field__error">{errors.payment_card}</small>}
              </label>
              <label className="field">
                <span>Expiry</span>
                <input name="payment_expiry" value={form.payment_expiry} onChange={(e) => set('payment_expiry', formatExpiry(e.target.value))} placeholder="MM/YY" inputMode="numeric" autoComplete="cc-exp" />
                {errors.payment_expiry && <small className="field__error">{errors.payment_expiry}</small>}
              </label>
              <label className="field">
                <span>CVC</span>
                <input name="payment_cvc" value={form.payment_cvc} onChange={(e) => set('payment_cvc', e.target.value.replace(/\D/g, '').slice(0, 4))} placeholder="123" inputMode="numeric" autoComplete="cc-csc" />
                {errors.payment_cvc && <small className="field__error">{errors.payment_cvc}</small>}
              </label>
            </div>
          </section>

          <div className="checkout-submit">
            <button className="button button--dark button--large button--full" disabled={processing}>
              {processing ? <span className="btn-spinner" /> : <LockKeyhole size={16} />}
              {processing ? 'Authorising payment…' : `Pay ${money(cart.subtotal)} securely`}
            </button>
            <p><LockKeyhole size={12} /> Mock encrypted payment · 256-bit SSL simulation</p>
          </div>
        </div>

        <aside className="checkout-summary">
          <div className="checkout-summary__head">
            <h2>In your bag</h2>
            <span>{cart.count} items</span>
          </div>
          <div className="checkout-summary__items">
            {cart.items.map((item) => (
              <div className="checkout-item" key={item.id}>
                <div className="checkout-item__image">
                  <ProductImage src={item.product.image} alt={item.product.name} />
                  <span>{item.quantity}</span>
                </div>
                <div>
                  <strong>{item.product.name}</strong>
                  <span>{item.product.category}</span>
                </div>
                <span>{money(item.line_total)}</span>
              </div>
            ))}
          </div>
          <div className="checkout-summary__rows">
            <div><span>Subtotal</span><span>{money(cart.subtotal)}</span></div>
            <div><span>Delivery</span><span>Complimentary</span></div>
            <div><span>Taxes</span><span>Included</span></div>
          </div>
          <div className="checkout-summary__total"><span>Total</span><strong>{money(cart.subtotal)}</strong></div>
          <div className="checkout-summary__assurances">
            <span><Truck size={15} /> Dispatched in 1–2 working days</span>
            <span><ShieldCheck size={15} /> 30-day returns, always</span>
          </div>
          <Link to="/shop" className="text-link checkout-summary__link"><ArrowLeft size={14} /> Keep shopping</Link>
        </aside>
      </form>
    </div>
  )
}
