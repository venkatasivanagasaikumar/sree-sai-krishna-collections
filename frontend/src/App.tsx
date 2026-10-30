import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import { WishlistProvider } from './context/WishlistContext';

// Layouts
import { StorefrontLayout } from './components/layout/StorefrontLayout';
import { AdminLayout } from './components/admin/AdminLayout';

// Storefront Pages
import { HomePage } from './pages/storefront/HomePage';
import { ShopPage } from './pages/storefront/ShopPage';
import { ProductDetailPage } from './pages/storefront/ProductDetailPage';
import { PoliciesPage } from './pages/storefront/PoliciesPage';
import { ContactPage } from './pages/storefront/ContactPage';
import { CartPage } from './pages/checkout/CartPage';
import { CheckoutPage } from './pages/checkout/CheckoutPage';
import { OrderSuccessPage } from './pages/checkout/OrderSuccessPage';
import { OrderTrackingPage } from './pages/account/OrderTrackingPage';
import { WishlistPage } from './pages/account/WishlistPage';
import { AccountPage } from './pages/account/AccountPage';

// Auth Pages
import { LoginPage } from './pages/authentication/LoginPage';
import { RegisterPage } from './pages/authentication/RegisterPage';
import { ForgotPasswordPage } from './pages/authentication/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/authentication/ResetPasswordPage';
import { AdminLoginPage } from './pages/authentication/AdminLoginPage';

// Admin Pages
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminProductsPage } from './pages/admin/AdminProductsPage';
import { AdminOrdersPage } from './pages/admin/AdminOrdersPage';
import { AdminInventoryPage } from './pages/admin/AdminInventoryPage';
import { AdminReturnsPage } from './pages/admin/AdminReturnsPage';
import { AdminCustomersPage } from './pages/admin/AdminCustomersPage';
import { AdminPromotionsPage } from './pages/admin/AdminPromotionsPage';
import { AdminReportsPage } from './pages/admin/AdminReportsPage';
import { AdminSettingsPage } from './pages/admin/AdminSettingsPage';
import { AdminSheetsSyncPage } from './pages/admin/AdminSheetsSyncPage';

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CartProvider>
          <WishlistProvider>
            <Routes>
              {/* Customer Storefront Routes */}
              <Route element={<StorefrontLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/shop" element={<ShopPage />} />
                <Route path="/product/:idOrSku" element={<ProductDetailPage />} />
                <Route path="/cart" element={<CartPage />} />
                <Route path="/checkout" element={<CheckoutPage />} />
                <Route path="/order-success/:orderId" element={<OrderSuccessPage />} />
                <Route path="/wishlist" element={<WishlistPage />} />
                <Route path="/account" element={<AccountPage />} />
                <Route path="/account/orders" element={<AccountPage />} />
                <Route path="/account/orders/:orderId" element={<OrderTrackingPage />} />
                <Route path="/policies" element={<PoliciesPage />} />
                <Route path="/terms" element={<PoliciesPage />} />
                <Route path="/privacy" element={<PoliciesPage />} />
                <Route path="/returns-policy" element={<PoliciesPage />} />
                <Route path="/contact" element={<ContactPage />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />
                <Route path="/forgot-password" element={<ForgotPasswordPage />} />
                <Route path="/reset-password" element={<ResetPasswordPage />} />
              </Route>

              {/* Dedicated Admin / Seller Login */}
              <Route path="/admin/login" element={<AdminLoginPage />} />

              {/* Secure Admin / Seller Dashboard Routes (Meesho Supplier Panel style) */}
              <Route path="/admin" element={<AdminLayout />}>
                <Route index element={<Navigate to="/admin/dashboard" replace />} />
                <Route path="dashboard" element={<AdminDashboardPage />} />
                <Route path="products" element={<AdminProductsPage />} />
                <Route path="orders" element={<AdminOrdersPage />} />
                <Route path="inventory" element={<AdminInventoryPage />} />
                <Route path="returns" element={<AdminReturnsPage />} />
                <Route path="customers" element={<AdminCustomersPage />} />
                <Route path="promotions" element={<AdminPromotionsPage />} />
                <Route path="reports" element={<AdminReportsPage />} />
                <Route path="sheets-sync" element={<AdminSheetsSyncPage />} />
                <Route path="settings" element={<AdminSettingsPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </WishlistProvider>
        </CartProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
