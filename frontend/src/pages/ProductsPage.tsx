import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowRight, ChevronLeft, ChevronRight, Search, SlidersHorizontal, X } from 'lucide-react'
import { api } from '../api'
import { useFetch } from '../hooks/useFetch'
import { ProductGrid } from '../components/ProductCard'
import { Breadcrumbs, EmptyState, PageLoader } from '../components/UI'
import type { Category } from '../types'

const SORT_OPTIONS = [
  { value: 'featured', label: 'Featured' },
  { value: 'newest', label: 'Newest first' },
  { value: 'price_asc', label: 'Price: low to high' },
  { value: 'price_desc', label: 'Price: high to low' },
  { value: 'rating', label: 'Best rated' },
  { value: 'name', label: 'A–Z' },
]

const PAGE_SIZE = 12

export function ProductsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const search = searchParams.get('search') || ''
  const category = searchParams.get('category') || ''
  const sort = searchParams.get('sort') || 'featured'
  const page = Number(searchParams.get('page') || 1)
  const minPrice = searchParams.get('min_price') || ''
  const maxPrice = searchParams.get('max_price') || ''
  const inStock = searchParams.get('in_stock') === 'true'

  const [draftSearch, setDraftSearch] = useState(search)
  const [draftMin, setDraftMin] = useState(minPrice)
  const [draftMax, setDraftMax] = useState(maxPrice)
  const [filtersOpen, setFiltersOpen] = useState(false)

  useEffect(() => {
    setDraftSearch(search)
    setDraftMin(minPrice)
    setDraftMax(maxPrice)
  }, [search, minPrice, maxPrice])

  const { data: categories, loading: categoriesLoading } = useFetch(api.categories, [])
  const { data, loading, error } = useFetch(
    () =>
      api.products({
        search,
        category,
        sort,
        page,
        page_size: PAGE_SIZE,
        min_price: minPrice || undefined,
        max_price: maxPrice || undefined,
        in_stock: inStock || undefined,
      }),
    [search, category, sort, page, minPrice, maxPrice, inStock],
  )

  const update = (values: Record<string, string | undefined>, resetPage = true) => {
    const next = new URLSearchParams(searchParams)
    Object.entries(values).forEach(([key, value]) => {
      if (value === undefined || value === '') next.delete(key)
      else next.set(key, value)
    })
    if (resetPage) next.delete('page')
    setSearchParams(next)
  }

  const applyFilters = (event: React.FormEvent) => {
    event.preventDefault()
    update({ min_price: draftMin || undefined, max_price: draftMax || undefined })
    setFiltersOpen(false)
  }

  const clearAll = () => {
    setSearchParams(new URLSearchParams())
    setFiltersOpen(false)
  }

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault()
    update({ search: draftSearch.trim() || undefined })
  }

  const activeFilters = [category, search, minPrice, maxPrice, inStock].filter(Boolean).length
  const total = data?.total ?? 0

  const FilterPanel = (
    <div className="filter-panel">
      <div className="filter-panel__head">
        <h3>Refine</h3>
        {activeFilters > 0 && <button onClick={clearAll} className="filter-clear">Clear all</button>}
      </div>

      <div className="filter-group">
        <h4>Category</h4>
        <div className="filter-categories">
          <button className={!category ? 'is-selected' : ''} onClick={() => update({ category: undefined })}>
            <span>All pieces</span>
            <span>{categories?.reduce((sum, c) => sum + c.count, 0) ?? '—'}</span>
          </button>
          {categories?.map((c: Category) => (
            <button
              key={c.name}
              className={category === c.name ? 'is-selected' : ''}
              onClick={() => update({ category: c.name })}
            >
              <span>{c.name}</span>
              <span>{c.count}</span>
            </button>
          ))}
        </div>
      </div>

      <form className="filter-group" onSubmit={applyFilters}>
        <h4>Price</h4>
        <div className="price-inputs">
          <label>
            <span>Min</span>
            <input type="number" min="0" step="1" value={draftMin} onChange={(e) => setDraftMin(e.target.value)} placeholder="0" />
          </label>
          <span className="price-inputs__dash">–</span>
          <label>
            <span>Max</span>
            <input type="number" min="0" step="1" value={draftMax} onChange={(e) => setDraftMax(e.target.value)} placeholder="250" />
          </label>
        </div>
        <button className="button button--outline button--small" type="submit">Apply price</button>
      </form>

      <div className="filter-group">
        <label className="switch-row">
          <span>
            <strong>In stock only</strong>
            <small>Ready to ship</small>
          </span>
          <input
            type="checkbox"
            checked={inStock}
            onChange={(event) => update({ in_stock: event.target.checked ? 'true' : undefined })}
          />
          <span className="switch" aria-hidden />
        </label>
      </div>

      <div className="filter-panel__note">
        <span>Not sure where to start?</span>
        <Link to="/shop?sort=rating">Browse our best-rated pieces <ArrowRight size={13} /></Link>
      </div>
    </div>
  )

  return (
    <div className="shell section page-shop">
      <Breadcrumbs items={[{ label: 'Home', to: '/' }, { label: 'Shop' }]} />
      <div className="shop-head">
        <div>
          <span className="eyebrow">The full collection</span>
          <h1>{search ? <>Results for <em>“{search}”</em></> : category ? <>{category}</> : 'Everything, considered.'}</h1>
          <p>{loading ? 'Gathering pieces…' : `${total} ${total === 1 ? 'piece' : 'pieces'} ${category ? `in ${category}` : 'across the shop'}`}</p>
        </div>
        <form className="shop-search" onSubmit={submitSearch}>
          <Search size={17} />
          <input value={draftSearch} onChange={(e) => setDraftSearch(e.target.value)} placeholder="Search by name, category…" />
          {draftSearch && <button type="button" onClick={() => { setDraftSearch(''); update({ search: undefined }) }} aria-label="Clear search"><X size={15} /></button>}
        </form>
      </div>

      <div className="shop-toolbar">
        <button className="filter-toggle" onClick={() => setFiltersOpen(true)}>
          <SlidersHorizontal size={16} /> Filters {activeFilters > 0 && <span>{activeFilters}</span>}
        </button>
        <div className="shop-toolbar__right">
          <span className="sort-label">Sort</span>
          <select value={sort} onChange={(e) => update({ sort: e.target.value })} aria-label="Sort products">
            {SORT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
        </div>
      </div>

      <div className="shop-layout">
        <aside className="shop-sidebar">{categoriesLoading ? <PageLoader label="Loading filters…" /> : FilterPanel}</aside>
        <div className="shop-results">
          {error && <EmptyState title="The shop is taking a moment" text={error} action={<button className="button button--dark" onClick={() => window.location.reload()}>Try again</button>} />}
          {loading && !error && (
            <div className="product-grid">
              {Array.from({ length: 9 }).map((_, i) => <div className="skeleton-card" key={i}><div className="skeleton skeleton--image" /><div className="skeleton skeleton--line" /><div className="skeleton skeleton--line skeleton--short" /></div>)}
            </div>
          )}
          {!loading && !error && data && data.items.length === 0 && (
            <EmptyState
              title="No pieces match that yet"
              text="Try a softer search, a different category, or clear the filters. There is plenty more in the shop."
              action={<button className="button button--dark" onClick={clearAll}>Clear filters</button>}
            />
          )}
          {!loading && !error && data && data.items.length > 0 && (
            <>
              <ProductGrid products={data.items} />
              <Pagination page={page} pages={data.pages} onChange={(next) => update({ page: String(next) }, false)} />
            </>
          )}
        </div>
      </div>

      {filtersOpen && (
        <div className="filter-drawer">
          <div className="filter-drawer__overlay" onClick={() => setFiltersOpen(false)} />
          <div className="filter-drawer__panel">
            <button className="filter-drawer__close" onClick={() => setFiltersOpen(false)} aria-label="Close filters"><X size={20} /></button>
            {FilterPanel}
          </div>
        </div>
      )}
    </div>
  )
}

function Pagination({ page, pages, onChange }: { page: number; pages: number; onChange: (page: number) => void }) {
  if (pages <= 1) return null
  const visible = Array.from({ length: pages }, (_, i) => i + 1).filter((p) => p === 1 || p === pages || Math.abs(p - page) <= 1)
  return (
    <nav className="pagination" aria-label="Pagination">
      <button disabled={page <= 1} onClick={() => onChange(page - 1)} aria-label="Previous page"><ChevronLeft size={16} /></button>
      {visible.map((p, index) => {
        const previous = visible[index - 1]
        return (
          <span key={p} className="pagination__group">
            {previous && p - previous > 1 && <span className="pagination__ellipsis">…</span>}
            <button className={p === page ? 'is-current' : ''} onClick={() => onChange(p)}>{p}</button>
          </span>
        )
      })}
      <button disabled={page >= pages} onClick={() => onChange(page + 1)} aria-label="Next page"><ChevronRight size={16} /></button>
    </nav>
  )
}
