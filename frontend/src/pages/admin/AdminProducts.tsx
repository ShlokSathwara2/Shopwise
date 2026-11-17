import { useEffect, useMemo, useState } from 'react'
import {
  Archive,
  ArchiveRestore,
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
  Pencil,
  Plus,
  Search,
  Trash2,
  X,
} from 'lucide-react'
import { api, money } from '../../api'
import { useFetch } from '../../hooks/useFetch'
import { useToast } from '../../context/ToastContext'
import { PageLoader } from '../../components/UI'
import type { Category, Product } from '../../types'

interface ProductForm {
  name: string
  description: string
  category: string
  price: string
  stock: string
  image: string
  material: string
  colour: string
  is_active: boolean
}

const emptyForm: ProductForm = {
  name: '',
  description: '',
  category: '',
  price: '',
  stock: '',
  image: '',
  material: '',
  colour: '',
  is_active: true,
}

const PAGE_SIZE = 10

export function AdminProducts() {
  const { push } = useToast()
  const { data: products, loading, reload } = useFetch(() => api.adminProducts(''), [])
  const { data: categories } = useFetch(api.categories, [])
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [editing, setEditing] = useState<Product | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [form, setForm] = useState<ProductForm>(emptyForm)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null)
  const [deleting, setDeleting] = useState(false)

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    return (products || []).filter(
      (product) =>
        !query ||
        product.name.toLowerCase().includes(query) ||
        product.category.toLowerCase().includes(query) ||
        product.code.toLowerCase().includes(query),
    )
  }, [products, search])

  const pages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE))
  const visible = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE)
  const liveProducts = (products || []).filter((product) => product.is_active !== false)
  const archived = (products || []).filter((product) => product.is_active === false)
  const activeCount = liveProducts.filter((product) => product.stock > 0).length

  useEffect(() => {
    if (page > pages) setPage(pages)
  }, [page, pages])

  const openCreate = () => {
    setEditing(null)
    setForm({ ...emptyForm, category: categories?.[0]?.name || 'Everyday Finds' })
    setFormError('')
    setFormOpen(true)
  }

  const openEdit = (product: Product) => {
    setEditing(product)
    setForm({
      name: product.name,
      description: product.description,
      category: product.category,
      price: String(product.price),
      stock: String(product.stock),
      image: product.image,
      material: product.material,
      colour: product.colour,
      is_active: product.is_active !== false,
    })
    setFormError('')
    setFormOpen(true)
  }

  const update = (key: keyof ProductForm, value: string | boolean) => {
    setForm((current) => ({ ...current, [key]: value }))
    setFormError('')
  }

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (form.name.trim().length < 2) return setFormError('Give the product a name.')
    if (!form.category) return setFormError('Choose a category.')
    if (!form.price || Number(form.price) <= 0) return setFormError('Enter a price greater than zero.')
    if (form.stock === '' || Number(form.stock) < 0) return setFormError('Enter a stock level.')
    setSaving(true)
    try {
      const payload = {
        name: form.name.trim(),
        description: form.description.trim(),
        category: form.category,
        price: Number(form.price),
        stock: Number(form.stock),
        image: form.image.trim(),
        material: form.material.trim(),
        colour: form.colour.trim(),
      }
      if (editing) {
        await api.adminUpdateProduct(editing.id, { ...payload, is_active: form.is_active })
        push(`${form.name.trim()} updated.`, 'success')
      } else {
        await api.adminCreateProduct(payload)
        push(`${form.name.trim()} added to the shop.`, 'success')
      }
      setFormOpen(false)
      reload()
    } catch (error) {
      setFormError(error instanceof Error ? error.message : 'Could not save this product.')
    } finally {
      setSaving(false)
    }
  }

  const confirmDelete = async () => {
    if (!deleteTarget) return
    setDeleting(true)
    try {
      await api.adminDeleteProduct(deleteTarget.id)
      push(`${deleteTarget.name} removed from the storefront.`, 'success')
      setDeleteTarget(null)
      reload()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not remove this product.', 'error')
    } finally {
      setDeleting(false)
    }
  }

  const restore = async (product: Product) => {
    try {
      await api.adminUpdateProduct(product.id, {
        name: product.name,
        description: product.description,
        category: product.category,
        price: product.price,
        stock: product.stock,
        image: product.image,
        material: product.material,
        colour: product.colour,
        is_active: true,
      })
      push(`${product.name} restored to the shop.`, 'success')
      reload()
    } catch (error) {
      push(error instanceof Error ? error.message : 'Could not restore this product.', 'error')
    }
  }

  if (loading || !products) return <PageLoader label="Opening the stockroom…" />

  return (
    <div className="admin-page">
      <div className="admin-page__head">
        <div>
          <span className="eyebrow">Catalogue</span>
          <h1>Products</h1>
          <p>{liveProducts.length.toLocaleString()} active pieces across {categories?.length || 0} categories. Add, edit or retire anything in the edit.</p>
        </div>
        <div className="admin-page__actions">
          <button className="button button--dark button--small" onClick={openCreate}><Plus size={16} /> Add product</button>
        </div>
      </div>

      <div className="admin-mini-stats">
        <div><span>Active products</span><strong>{liveProducts.length.toLocaleString()}</strong></div>
        <div><span>In stock</span><strong>{activeCount.toLocaleString()}</strong></div>
        <div><span>Low stock (&lt;25)</span><strong>{liveProducts.filter((product) => product.stock < 25).length}</strong></div>
        <div><span>Archived</span><strong>{archived.length}</strong></div>
      </div>

      <section className="admin-card">
        <div className="admin-toolbar">
          <div className="admin-search">
            <Search size={16} />
            <input value={search} onChange={(event) => { setSearch(event.target.value); setPage(1) }} placeholder="Search by name, category or SKU…" />
            {search && <button onClick={() => setSearch('')} aria-label="Clear search"><X size={14} /></button>}
          </div>
          <span className="admin-toolbar__count">{filtered.length} results</span>
        </div>
        <div className="admin-table-wrap">
          <table className="admin-table admin-table--products">
            <thead>
              <tr><th>Product</th><th>Category</th><th>Price</th><th>Stock</th><th>Rating</th><th>Status</th><th /></tr>
            </thead>
            <tbody>
              {visible.map((product) => {
                const inactive = product.is_active === false
                return (
                  <tr key={product.id} className={inactive ? 'is-archived' : ''}>
                    <td>
                      <div className="admin-product-cell">
                        <img src={product.image || '/static/products/placeholder.svg'} alt="" />
                        <div><strong>{product.name}</strong><span>{product.code}</span></div>
                      </div>
                    </td>
                    <td><span className="category-tag">{product.category}</span></td>
                    <td>{money(product.price)}</td>
                    <td><span className={`stock-tag ${product.stock < 25 ? 'stock-tag--low' : ''}`}>{inactive ? '—' : product.stock}</span></td>
                    <td>{product.rating > 0 ? product.rating.toFixed(1) : '—'}</td>
                    <td><span className={`status-pill ${inactive ? 'status-pill--archived' : product.stock < 25 ? 'status-pill--low' : 'status-pill--delivered'}`}>{inactive ? 'Archived' : product.stock < 25 ? 'Low stock' : 'Live'}</span></td>
                    <td>
                      <div className="admin-row-actions">
                        <button onClick={() => openEdit(product)} aria-label={`Edit ${product.name}`} title="Edit"><Pencil size={14} /></button>
                        {inactive ? (
                          <button onClick={() => restore(product)} aria-label={`Restore ${product.name}`} title="Restore"><ArchiveRestore size={14} /></button>
                        ) : (
                          <button onClick={() => setDeleteTarget(product)} aria-label={`Remove ${product.name}`} title="Remove"><Trash2 size={14} /></button>
                        )}
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          {visible.length === 0 && <div className="admin-empty"><p>No products match “{search}”.</p></div>}
        </div>
        <div className="admin-pagination">
          <span>Showing {visible.length ? (page - 1) * PAGE_SIZE + 1 : 0}–{Math.min(page * PAGE_SIZE, filtered.length)} of {filtered.length}</span>
          <div>
            <button disabled={page <= 1} onClick={() => setPage((p) => p - 1)} aria-label="Previous page"><ChevronLeft size={15} /></button>
            <span>{page} / {pages}</span>
            <button disabled={page >= pages} onClick={() => setPage((p) => p + 1)} aria-label="Next page"><ChevronRight size={15} /></button>
          </div>
        </div>
      </section>

      {archived.length > 0 && <p className="admin-footnote"><Archive size={14} /> {archived.length} archived product{archived.length === 1 ? '' : 's'} hidden from the shop, retained in historical orders.</p>}

      {formOpen && (
        <div className="modal">
          <div className="modal__backdrop" onClick={() => !saving && setFormOpen(false)} />
          <div className="modal__panel modal__panel--wide">
            <div className="modal__head">
              <div>
                <span className="eyebrow">{editing ? 'Edit product' : 'New product'}</span>
                <h2>{editing ? editing.name : 'Add a considered piece'}</h2>
              </div>
              <button onClick={() => setFormOpen(false)} disabled={saving} aria-label="Close"><X size={19} /></button>
            </div>
            <form onSubmit={submit} className="modal__form">
              <div className="modal-product-preview">
                <img src={form.image || '/static/products/placeholder.svg'} alt="" />
                <div>
                  <span className="eyebrow">Catalogue preview</span>
                  <strong>{form.name || 'Your new product'}</strong>
                  <span>{form.category || 'Choose a category'} · {form.price ? money(Number(form.price)) : '$0.00'}</span>
                </div>
              </div>
              <div className="form-grid">
                <label className="field field--full"><span>Product name</span><input value={form.name} onChange={(e) => update('name', e.target.value)} placeholder="e.g. Stoneware Serving Bowl" /></label>
                <label className="field"><span>Category</span><select value={form.category} onChange={(e) => update('category', e.target.value)}>{(categories || []).map((category: Category) => <option key={category.name}>{category.name}</option>)}</select></label>
                <label className="field"><span>Price (USD)</span><input type="number" step="0.01" min="0" value={form.price} onChange={(e) => update('price', e.target.value)} placeholder="24.00" /></label>
                <label className="field"><span>Stock on hand</span><input type="number" min="0" value={form.stock} onChange={(e) => update('stock', e.target.value)} placeholder="40" /></label>
                <label className="field"><span>Colour</span><input value={form.colour} onChange={(e) => update('colour', e.target.value)} placeholder="Cream" /></label>
                <label className="field"><span>Material</span><input value={form.material} onChange={(e) => update('material', e.target.value)} placeholder="Stoneware" /></label>
                <label className="field field--full"><span>Image URL</span><div className="input-with-icon"><ImageIcon size={15} /><input value={form.image} onChange={(e) => update('image', e.target.value)} placeholder="/static/products/placeholder.svg" /></div></label>
                <label className="field field--full"><span>Description</span><textarea value={form.description} onChange={(e) => update('description', e.target.value)} rows={3} placeholder="What makes this piece worth living with?" /></label>
              </div>
              {editing && (
                <label className="checkbox-row"><input type="checkbox" checked={form.is_active} onChange={(e) => update('is_active', e.target.checked)} /><span>Visible in the storefront</span></label>
              )}
              {formError && <p className="auth-error">{formError}</p>}
              <div className="modal__actions">
                <button type="button" className="button button--ghost" onClick={() => setFormOpen(false)} disabled={saving}>Cancel</button>
                <button className="button button--dark" disabled={saving}>{saving ? <span className="btn-spinner" /> : null}{saving ? 'Saving…' : editing ? 'Save changes' : 'Add to shop'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {deleteTarget && (
        <div className="modal">
          <div className="modal__backdrop" onClick={() => !deleting && setDeleteTarget(null)} />
          <div className="modal__panel modal__panel--confirm">
            <span className="modal__warning"><Trash2 size={20} /></span>
            <h2>Remove this piece?</h2>
            <p><strong>{deleteTarget.name}</strong> will be hidden from the shop and removed from active carts. Historical orders will keep their record.</p>
            <div className="modal__actions">
              <button className="button button--ghost" onClick={() => setDeleteTarget(null)} disabled={deleting}>Keep it</button>
              <button className="button button--danger" onClick={confirmDelete} disabled={deleting}>{deleting ? 'Removing…' : 'Remove product'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
