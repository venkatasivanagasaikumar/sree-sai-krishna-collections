export interface User {
  id: string;
  email: string;
  full_name: string;
  phone?: string;
  role: string;
  addresses?: Address[];
}

export interface Address {
  id?: string;
  name: string;
  phone: string;
  address_line1: string;
  address_line2?: string;
  landmark?: string;
  city: string;
  state: string;
  pincode: string;
  is_default?: boolean;
  type?: string;
}

export interface Category {
  id: string;
  name: string;
  slug: string;
  parent_category?: string;
  description?: string;
  image_url?: string;
  display_order: number;
  is_active: boolean;
}

export interface ProductVariant {
  variant_id: string;
  name: string;
  sku: string;
  price: number;
  mrp: number;
  stock: number;
  color?: string;
  size?: string;
  image_url?: string;
}

export interface Review {
  id?: string;
  product_id: string;
  reviewer_name: string;
  rating: number;
  title: string;
  comment: string;
  images?: string[];
  is_verified_purchase?: boolean;
  created_at: string;
}

export interface Product {
  id: string;
  name: string;
  sku: string;
  category: string;
  subcategory?: string;
  description: string;
  short_description?: string;
  mrp: number;
  price: number;
  discount_percent?: number;
  discount_amount?: number;
  stock: number;
  low_stock_threshold?: number;
  images: string[];
  materials_and_finish: string;
  jewelry_type: string;
  genuine_gold_disclaimer: string;
  colors?: string[];
  sizes?: string[];
  variants?: ProductVariant[];
  care_instructions: string;
  shipping_estimate_days: string;
  return_eligible: boolean;
  return_window_days: number;
  status: 'active' | 'draft' | 'inactive' | 'archived';
  tags?: string[];
  is_featured?: boolean;
  is_bestseller?: boolean;
  is_trending?: boolean;
  rating?: number;
  rating_count?: number;
  sales_count?: number;
  weight_grams?: number;
  reviews?: Review[];
  related_products?: Product[];
}

export interface CartItemDetail {
  product_id: string;
  variant_id?: string;
  name: string;
  sku: string;
  image: string;
  mrp: number;
  price: number;
  quantity: number;
  total_price: number;
  stock: number;
  in_stock: boolean;
}

export interface CartTotals {
  items: CartItemDetail[];
  subtotal: number;
  discount_amount: number;
  coupon_code?: string;
  shipping_fee: number;
  final_amount: number;
  free_shipping_eligible: boolean;
  amount_needed_for_free_shipping: number;
}

export interface TimelineEvent {
  status: string;
  message: string;
  timestamp: string;
  performed_by?: string;
}

export interface OrderItem {
  product_id: string;
  variant_id?: string;
  name: string;
  sku: string;
  image: string;
  unit_price: number;
  mrp: number;
  quantity: number;
  total_price: number;
}

export interface Order {
  id: string;
  order_id: string;
  user_id?: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  items: OrderItem[];
  subtotal: number;
  discount_amount: number;
  coupon_code?: string;
  shipping_fee: number;
  final_amount: number;
  currency: string;
  shipping_address: Address;
  payment_method: string;
  payment_status: string;
  order_status: string;
  fulfilment_status: string;
  carrier_name?: string;
  tracking_number?: string;
  notes?: string;
  timeline: TimelineEvent[];
  created_at: string;
  updated_at: string;
}

export interface Coupon {
  id: string;
  code: string;
  description: string;
  discount_type: 'percentage' | 'fixed';
  discount_value: number;
  min_order_value: number;
  max_discount_amount?: number;
  start_date?: string;
  expiry_date?: string;
  usage_limit_total?: number;
  times_used?: number;
  is_active: boolean;
}

export interface DashboardKPIs {
  kpis: {
    total_orders: number;
    today_orders: number;
    orders_awaiting_processing: number;
    gross_sales: number;
    period_sales: number;
    total_discounts: number;
    total_refunds: number;
    net_sales: number;
    delivered_orders: number;
    return_requests: number;
    active_products: number;
    low_stock_products: number;
  };
  order_status_distribution: Record<string, number>;
  payment_method_breakdown: Record<string, number>;
  top_selling_products: Array<{
    id: string;
    name: string;
    sku: string;
    price: number;
    sales_count: number;
    stock: number;
  }>;
  recent_orders: Array<{
    order_id: string;
    customer_name: string;
    final_amount: number;
    order_status: string;
    payment_method: string;
    created_at: string;
  }>;
  sales_trend: Array<{
    date: string;
    sales: number;
  }>;
}

export interface InventoryMovement {
  id: string;
  product_id: string;
  sku: string;
  product_name: string;
  previous_stock: number;
  quantity_change: number;
  new_stock: number;
  adjustment_type: string;
  reason: string;
  performed_by: string;
  created_at: string;
}

export interface CustomerSummary {
  id: string;
  full_name: string;
  email: string;
  phone: string;
  addresses_count: number;
  total_orders: number;
  total_spent: number;
  is_active: boolean;
  created_at: string;
}
