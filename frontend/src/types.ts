export interface User {
  id: number
  name: string
  email: string
  is_admin: boolean
  created_at: string
}

export interface Category {
  name: string
  count: number
}

export interface Product {
  id: number
  code: string
  name: string
  description: string
  category: string
  price: number
  stock: number
  rating: number
  review_count: number
  image: string
  material: string
  colour: string
  popularity: number
  is_active?: boolean
}

export interface ProductList {
  items: Product[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Review {
  id: number
  rating: number
  title: string
  comment: string
  created_at: string
  user_name: string
}

export interface CartItem {
  id: number
  product: Product
  quantity: number
  line_total: number
}

export interface Cart {
  items: CartItem[]
  subtotal: number
  count: number
}

export interface OrderItem {
  product_id: number | null
  product_code: string
  product_name: string
  quantity: number
  unit_price: number
  line_total: number
  image: string
}

export interface Order {
  id: number
  reference: string
  total: number
  status: string
  payment_method: string
  payment_last4: string
  shipping_name: string
  shipping_address: string
  shipping_city: string
  shipping_postcode: string
  shipping_country: string
  created_at: string
  items: OrderItem[]
}

export interface Recommendation {
  title: string
  subtitle: string
  strategy: string
  generated_ms: number
  personalized: boolean
  model_label: string
  items: Product[]
}

export interface CheckoutPayload {
  shipping_name: string
  shipping_address: string
  shipping_city: string
  shipping_postcode: string
  shipping_country: string
  payment_name: string
  payment_card: string
  payment_expiry: string
  payment_cvc: string
}

export interface AdminTotals {
  revenue: number
  orders: number
  customers: number
  products: number
  avg_order: number
  low_stock: number
  units: number
}

export interface AdminStats {
  totals: AdminTotals
  revenue_by_day: { date: string; revenue: number; orders: number }[]
  revenue_by_category: { category: string; revenue: number; units: number }[]
  top_products: { id: number; name: string; image: string; category: string; units: number; revenue: number }[]
  recent_orders: { id: number; reference: string; total: number; status: string; created_at: string; items: number }[]
  events: Record<string, number>
  model: {
    best_model: string
    metrics: Record<string, ModelScore>
    trained_at?: string
    dataset: Record<string, unknown>
  }
}

export interface ModelScore {
  'precision@5': number
  'precision@10': number
  'recall@5': number
  'recall@10': number
  'hit_rate@5': number
  'hit_rate@10': number
  'ndcg@5': number
  'ndcg@10': number
  'coverage@5': number
  'coverage@10': number
  offline_ms_per_user: number
  description: string
  params: Record<string, unknown>
  evaluated_users: number
}

export interface GridPoint {
  content_weight: number
  item_cf_weight: number
  svd_weight: number
  'ndcg@10': number
  'hit_rate@10': number
  'precision@10': number
}

export interface ModelMetrics {
  trained_at: string
  best_model: string
  training_seconds: number
  models: Record<string, ModelScore>
  validation: {
    selected: GridPoint
    grid_top5: GridPoint[]
    grid_best_per_alpha: GridPoint[]
    validation_users: number
    svd_rank_selection: { rank: number; 'ndcg@10': number; 'hit_rate@10': number }[]
  }
  dataset: {
    catalog_products: number
    customers: number
    purchase_lines: number
    unique_user_product_pairs: number
    train_pairs: number
    validation_pairs: number
    test_pairs: number
    evaluation_users: number
    sparsity: number
    avg_distinct_products_per_customer: number
    avg_test_items_per_customer: number
    split_method: string
    date_range: string[]
  }
  source: { name: string; url: string; raw_lines: number; raw_customers: number; raw_products: number }
}
