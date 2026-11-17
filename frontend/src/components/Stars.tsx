import { Star } from 'lucide-react'

export function Stars({ rating, count, size = 13, showValue = true }: { rating: number; count?: number; size?: number; showValue?: boolean }) {
  const rounded = Math.round(rating)
  return (
    <span className="stars" aria-label={`${rating.toFixed(1)} out of 5 stars${count !== undefined ? `, ${count} reviews` : ''}`}>
      <span className="stars__icons" aria-hidden>
        {[1, 2, 3, 4, 5].map((i) => (
          <Star key={i} size={size} strokeWidth={1.5} className={i <= rounded ? 'star star--filled' : 'star'} />
        ))}
      </span>
      {showValue && <span className="stars__value">{rating.toFixed(1)}</span>}
      {count !== undefined && <span className="stars__count">({count})</span>}
    </span>
  )
}
