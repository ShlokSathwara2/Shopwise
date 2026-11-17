import { Link } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, Leaf, RotateCcw, ShieldCheck, Sparkles, Truck } from 'lucide-react'
import { api, categorySlug } from '../api'
import { useAuth } from '../context/AuthContext'
import { useFetch } from '../hooks/useFetch'
import { ProductGrid, ProductImage, ProductRail } from '../components/ProductCard'
import { PageLoader, SectionHeading } from '../components/UI'
import type { Category, Product, Recommendation } from '../types'

const FEATURES = [
  { icon: Truck, title: 'Complimentary delivery', text: 'On every order over $75, packed with care.' },
  { icon: Leaf, title: 'Considered materials', text: 'Pieces chosen to be kept, not replaced.' },
  { icon: RotateCcw, title: '30-day returns', text: 'A little room to change your mind.' },
  { icon: ShieldCheck, title: 'Secure checkout', text: 'A simple, encrypted mock-payment flow.' },
]

export function HomePage() {
  const { user } = useAuth()
  const { data, loading } = useFetch(async () => {
    const [categories, recommendations, featured, trending] = await Promise.all([
      api.categories(),
      api.homeRecommendations(8),
      api.products({ sort: 'featured', page_size: 8 }),
      api.trending(4),
    ])
    return { categories, recommendations, featured, trending }
  }, [user?.id])

  if (loading || !data) return <PageLoader label="Arranging the shop window…" />

  const { categories, recommendations, featured, trending } = data
  const heroProduct: Product | undefined = recommendations.items[0] || featured.items[0]
  const editorialCategories = categories.slice(0, 5)
  const recommendedIds = new Set(recommendations.items.map((product) => product.id))
  const freshTrending = trending.items.filter((product) => !recommendedIds.has(product.id))

  return (
    <div className="home">
      <section className="hero">
        <div className="shell hero__grid">
          <div className="hero__copy">
            <span className="eyebrow hero__eyebrow"><Sparkles size={13} /> The new home edit · Vol. 04</span>
            <h1>Objects with a<br /><em>little more soul.</em></h1>
            <p>
              Useful, beautiful things for the everyday — sourced from a real retail catalogue and matched to you
              by a recommender that learns what you love.
            </p>
            <div className="hero__actions">
              <Link to="/shop" className="button button--dark">Shop the collection <ArrowRight size={16} /></Link>
              <a href="#recommended" className="button button--ghost">Your edit <ArrowUpRight size={16} /></a>
            </div>
            <div className="hero__proof">
              <span><strong>1,000</strong> considered pieces</span>
              <span><strong>13</strong> curated edits</span>
              <span><strong>4.3★</strong> average rating</span>
            </div>
          </div>
          <div className="hero__visual">
            <div className="hero__poster">
              <img src="/static/hero.svg" alt="The Shopwise home edit" />
              <span className="hero__poster-label">The autumn / winter edit</span>
            </div>
            {heroProduct && (
              <Link to={`/product/${heroProduct.id}`} className="hero__card">
                <ProductImage src={heroProduct.image} alt={heroProduct.name} className="hero__card-image" />
                <div>
                  <span className="eyebrow">Editor’s pick</span>
                  <h3>{heroProduct.name}</h3>
                  <p>{heroProduct.category}</p>
                </div>
                <span className="hero__card-arrow"><ArrowUpRight size={16} /></span>
              </Link>
            )}
            <span className="hero__stamp">Shopwise<br />Est. 2026</span>
          </div>
        </div>
      </section>

      <section className="feature-strip">
        <div className="shell feature-strip__grid">
          {FEATURES.map((feature) => (
            <div className="feature-strip__item" key={feature.title}>
              <feature.icon size={21} strokeWidth={1.5} />
              <div>
                <h4>{feature.title}</h4>
                <p>{feature.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="shell section">
        <SectionHeading
          eyebrow="Browse the edits"
          title="A place for everything"
          subtitle="Thirteen small worlds, one considered collection."
          action={<Link to="/shop" className="text-link">All categories <ArrowRight size={14} /></Link>}
        />
        <div className="category-grid">
          {editorialCategories.map((category: Category, index: number) => (
            <Link
              to={`/shop?category=${encodeURIComponent(category.name)}`}
              className={`category-card ${index === 0 ? 'category-card--wide' : ''}`}
              key={category.name}
            >
              <img src={`/static/categories/${categorySlug(category.name)}.svg`} alt="" loading="lazy" />
              <div className="category-card__overlay">
                <span>{String(index + 1).padStart(2, '0')}</span>
                <h3>{category.name}</h3>
                <p>{category.count} pieces <ArrowUpRight size={13} /></p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <div id="recommended" className="shell">
        <ProductRail
          title={recommendations.title}
          subtitle={recommendations.subtitle}
          modelLabel={recommendations.model_label}
          products={recommendations.items}
          viewAll="/shop"
        />
        <div className="model-note">
          <span className="model-note__pulse" />
          {recommendations.personalized
            ? `Personalised in ${recommendations.generated_ms.toFixed(0)} ms · hybrid content + collaborative filtering`
            : 'Popularity baseline · sign in and browse to unlock personal recommendations'}
        </div>
      </div>

      <section className="shell section">
        <SectionHeading
          eyebrow="The considered edit"
          title={user ? 'Chosen with you in mind' : 'The pieces everyone is talking about'}
          subtitle="Our most-loved objects, arranged for slow mornings and good tables."
          action={<Link to="/shop?sort=rating" className="text-link">Shop best rated <ArrowRight size={14} /></Link>}
        />
        <ProductGrid products={featured.items} />
      </section>

      <section className="shell editorial">
        <div className="editorial__image">
          <img src="/static/categories/textiles.svg" alt="Soft textiles from the Shopwise collection" />
        </div>
        <div className="editorial__copy">
          <span className="eyebrow">A note from the studio</span>
          <h2>Buy less.<br />Choose <em>well.</em></h2>
          <p>
            The best objects earn their place. They are used, mended, moved from room to room and remembered.
            Every piece here is selected for that kind of life — and our recommendation engine helps you find
            the ones that fit yours.
          </p>
          <Link to="/shop?category=Textiles" className="button button--outline">Explore textiles <ArrowRight size={15} /></Link>
          <div className="editorial__signature">— The Shopwise team</div>
        </div>
      </section>

      {freshTrending.length > 0 && (
        <section className="shell section section--tight">
          <ProductRail
            title="Moving quickly"
            subtitle="The pieces shoppers are adding to their bags right now."
            modelLabel={trending.model_label}
            products={freshTrending}
          />
        </section>
      )}

      <section className="service-banner">
        <div className="shell service-banner__inner">
          <div>
            <span className="eyebrow eyebrow--light">Here if you need us</span>
            <h2>A real shop, with a little<br />machine-learning magic.</h2>
          </div>
          <div className="service-banner__copy">
            <p>Browse, build a bag and check out in under a minute. Every view, save and order helps make your next visit a little more personal.</p>
            <Link to="/login" className="button button--cream">Sign in to your edit <ArrowRight size={16} /></Link>
          </div>
        </div>
      </section>
    </div>
  )
}
