import {
  User, Product, Category, CartTotals, Order, DashboardKPIs,
  InventoryMovement, Coupon, CustomerSummary, Review
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('ssk_access_token');
  const headers = new Headers(options.headers || {});

  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers
  });

  if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/register')) {
    // Attempt token refresh
    const refreshToken = localStorage.getItem('ssk_refresh_token');
    if (refreshToken) {
      try {
        const refreshRes = await fetch(`${API_BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: refreshToken })
        });
        if (refreshRes.ok) {
          const data = await refreshRes.json();
          localStorage.setItem('ssk_access_token', data.access_token);
          localStorage.setItem('ssk_refresh_token', data.refresh_token);
          // Retry original request
          headers.set('Authorization', `Bearer ${data.access_token}`);
          const retryRes = await fetch(`${API_BASE_URL}${endpoint}`, { ...options, headers });
          if (retryRes.ok) return await retryRes.json();
        }
      } catch (e) {
        console.error('Refresh token failed:', e);
      }
    }
  }

  if (!response.ok) {
    let errorDetail = 'Request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Auth
  login: (data: any) => request<any>('/auth/login', { method: 'POST', body: JSON.stringify(data) }),
  register: (data: any) => request<any>('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
  getProfile: () => request<User>('/auth/me'),
  updateProfile: (data: any) => request<any>('/auth/me', { method: 'PUT', body: JSON.stringify(data) }),
  addAddress: (data: any) => request<any>('/auth/addresses', { method: 'POST', body: JSON.stringify(data) }),
  deleteAddress: (id: string) => request<any>(`/auth/addresses/${id}`, { method: 'DELETE' }),

  // Products
  getProducts: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.append(k, String(v));
    });
    return request<{ products: Product[]; total: number; page: number; pages: number }>(`/products?${q.toString()}`);
  },
  getProductByIdOrSku: (idOrSku: string) => request<Product>(`/products/${idOrSku}`),
  getFeaturedProducts: () => request<Product[]>('/products/featured'),
  getBestsellerProducts: () => request<Product[]>('/products/bestsellers'),
  getTrendingProducts: () => request<Product[]>('/products/trending'),
  createProduct: (data: any) => request<any>('/products', { method: 'POST', body: JSON.stringify(data) }),
  updateProduct: (id: string, data: any) => request<any>(`/products/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProduct: (id: string) => request<any>(`/products/${id}`, { method: 'DELETE' }),
  exportProductsCsv: () => request<{ csv_content: string; filename: string }>('/products/admin/export/csv'),

  // Categories
  getCategories: () => request<Category[]>('/categories'),
  getAllCategoriesAdmin: () => request<Category[]>('/categories/admin/all'),
  createCategory: (data: any) => request<any>('/categories', { method: 'POST', body: JSON.stringify(data) }),
  updateCategory: (id: string, data: any) => request<any>(`/categories/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCategory: (id: string) => request<any>(`/categories/${id}`, { method: 'DELETE' }),

  // Cart
  getCart: () => request<CartTotals>('/cart'),
  addToCart: (productId: string, quantity = 1, variantId?: string) =>
    request<CartTotals>('/cart/items', {
      method: 'POST',
      body: JSON.stringify({ product_id: productId, quantity, variant_id: variantId })
    }),
  updateCartQuantity: (productId: string, quantity: number, variantId?: string) => {
    const q = variantId ? `?variant_id=${variantId}&quantity=${quantity}` : `?quantity=${quantity}`;
    return request<CartTotals>(`/cart/items/${productId}${q}`, { method: 'PUT' });
  },
  removeFromCart: (productId: string, variantId?: string) => {
    const q = variantId ? `?variant_id=${variantId}` : '';
    return request<CartTotals>(`/cart/items/${productId}${q}`, { method: 'DELETE' });
  },
  applyCoupon: (code: string) =>
    request<CartTotals>('/cart/coupon', { method: 'POST', body: JSON.stringify({ code }) }),
  removeCoupon: () => request<CartTotals>('/cart/coupon', { method: 'DELETE' }),
  validateGuestCart: (items: any[], couponCode?: string) =>
    request<CartTotals>('/cart/validate-guest', { method: 'POST', body: JSON.stringify({ items, coupon_code: couponCode }) }),
  mergeGuestCart: (items: any[]) =>
    request<CartTotals>('/cart/merge', { method: 'POST', body: JSON.stringify(items) }),

  // Orders
  createOrder: (data: any) => request<any>('/orders', { method: 'POST', body: JSON.stringify(data) }),
  getMyOrders: () => request<Order[]>('/orders/my-orders'),
  getOrderById: (orderId: string, verification?: string) =>
    request<Order>(`/orders/${orderId}${verification ? `?verification=${encodeURIComponent(verification)}` : ''}`),
  cancelOrder: (orderId: string, reason: string) =>
    request<any>(`/orders/${orderId}/cancel?reason=${encodeURIComponent(reason)}`, { method: 'POST' }),
  requestReturn: (orderId: string, data: any) =>
    request<any>(`/orders/${orderId}/return`, { method: 'POST', body: JSON.stringify(data) }),

  // Admin Orders
  listOrdersAdmin: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.append(k, String(v));
    });
    return request<{ orders: Order[]; total: number; page: number; pages: number }>(`/orders/admin/all?${q.toString()}`);
  },
  updateOrderStatusAdmin: (orderId: string, data: any) =>
    request<any>(`/orders/admin/${orderId}/status`, { method: 'PUT', body: JSON.stringify(data) }),
  getPackingSlip: (orderId: string) => request<any>(`/orders/admin/${orderId}/packing-slip`),

  // Payments
  createRazorpayOrder: (orderId: string) =>
    request<any>('/payments/create-razorpay-order', { method: 'POST', body: JSON.stringify({ order_id: orderId }) }),
  verifyRazorpayPayment: (data: any) =>
    request<any>('/payments/verify-razorpay-payment', { method: 'POST', body: JSON.stringify(data) }),

  // Inventory
  getInventory: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.append(k, String(v));
    });
    return request<{ items: Product[]; total: number; page: number; pages: number }>(`/inventory?${q.toString()}`);
  },
  adjustStock: (data: any) => request<any>('/inventory/adjust', { method: 'POST', body: JSON.stringify(data) }),
  getMovements: (sku?: string) => request<InventoryMovement[]>(`/inventory/movements${sku ? `?sku=${sku}` : ''}`),

  // Returns
  listReturnsAdmin: (status?: string) => request<any[]>(`/returns/admin/all${status ? `?status_filter=${status}` : ''}`),
  updateReturnStatusAdmin: (returnId: string, data: any) =>
    request<any>(`/returns/admin/${returnId}/status`, { method: 'PUT', body: JSON.stringify(data) }),

  // Coupons
  getActiveCoupons: () => request<Coupon[]>('/coupons/active'),
  listCouponsAdmin: () => request<Coupon[]>('/coupons/admin/all'),
  createCoupon: (data: any) => request<any>('/coupons', { method: 'POST', body: JSON.stringify(data) }),
  updateCoupon: (id: string, data: any) => request<any>(`/coupons/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCoupon: (id: string) => request<any>(`/coupons/${id}`, { method: 'DELETE' }),

  // Customers & Reviews
  listCustomersAdmin: (params: Record<string, any> = {}) => {
    const q = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null && v !== '') q.append(k, String(v));
    });
    return request<{ customers: CustomerSummary[]; total: number; page: number; pages: number }>(`/customers/admin/all?${q.toString()}`);
  },
  submitContactInquiry: (data: any) => request<any>('/customers/contact', { method: 'POST', body: JSON.stringify(data) }),
  listInquiriesAdmin: () => request<any[]>('/customers/admin/inquiries'),
  submitReview: (data: any) => request<any>('/customers/reviews', { method: 'POST', body: JSON.stringify(data) }),

  // Analytics
  getDashboardAnalytics: (days = 30) => request<DashboardKPIs>(`/analytics/dashboard?days=${days}`),
  getAuditLogs: (limit = 50) => request<any[]>(`/analytics/audit-logs?limit=${limit}`),

  // Settings
  getPublicSettings: () => request<any>('/settings/public'),
  updateSettingsAdmin: (data: any) => request<any>('/settings/admin', { method: 'PUT', body: JSON.stringify(data) }),

  // File Upload
  uploadImage: async (file: File): Promise<{ url: string; filename: string; size: number }> => {
    const formData = new FormData();
    formData.append('file', file);
    const token = localStorage.getItem('ssk_access_token');
    const res = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {})
      },
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(err.detail || 'Image upload failed');
    }
    const data = await res.json();
    // Prepend API_BASE_URL if it's a relative path like /uploads/...
    const fullUrl = data.url.startsWith('http') ? data.url : `${API_BASE_URL.replace('/api/v1', '')}${data.url}`;
    return { ...data, url: fullUrl };
  },

  // Google Sheets / Excel Live Sync
  getSheetsConfig: () => request<any>('/sheets/config'),
  saveSheetsConfig: (data: any) => request<any>('/sheets/config', { method: 'POST', body: JSON.stringify(data) }),
  testSheetsConnection: (webhookUrl: string, secretKey: string) =>
    request<any>('/sheets/test-connection', { method: 'POST', body: JSON.stringify({ webhook_url: webhookUrl, secret_key: secretKey }) }),
  pushAllToSheets: () => request<any>('/sheets/push-all', { method: 'POST' }),
  exportAllForSheets: () => request<any>('/sheets/export-all'),
  getAppScriptTemplate: () => request<{ script: string; secret_key: string; owner_email: string }>('/sheets/appscript-template')
};
