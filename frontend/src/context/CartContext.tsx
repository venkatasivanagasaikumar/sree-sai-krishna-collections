import React, { createContext, useContext, useState, useEffect } from 'react';
import { CartTotals, CartItemDetail } from '../types';
import { api } from '../services/api';
import { useAuth } from './AuthContext';

interface CartContextType {
  cart: CartTotals;
  isLoading: boolean;
  itemCount: number;
  addToCart: (productId: string, quantity?: number, variantId?: string) => Promise<void>;
  updateQuantity: (productId: string, quantity: number, variantId?: string) => Promise<void>;
  removeFromCart: (productId: string, variantId?: string) => Promise<void>;
  applyCoupon: (code: string) => Promise<void>;
  removeCoupon: () => Promise<void>;
  clearCart: () => void;
  toastMessage: string | null;
  clearToast: () => void;
}

const defaultCart: CartTotals = {
  items: [],
  subtotal: 0,
  discount_amount: 0,
  shipping_fee: 0,
  final_amount: 0,
  free_shipping_eligible: false,
  amount_needed_for_free_shipping: 999
};

const CartContext = createContext<CartContextType | undefined>(undefined);

export const CartProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated } = useAuth();
  const [cart, setCart] = useState<CartTotals>(defaultCart);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  const loadCart = async () => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        // Check if there was guest items in localStorage to merge
        const guestCart = localStorage.getItem('ssk_guest_cart');
        if (guestCart) {
          try {
            const parsed = JSON.parse(guestCart);
            if (Array.isArray(parsed) && parsed.length > 0) {
              const merged = await api.mergeGuestCart(parsed);
              localStorage.removeItem('ssk_guest_cart');
              setCart(merged);
              setIsLoading(false);
              return;
            }
          } catch (e) {
            console.error('Failed to merge guest cart:', e);
          }
        }
        const userCart = await api.getCart();
        setCart(userCart);
      } else {
        // Load guest cart
        const saved = localStorage.getItem('ssk_guest_cart');
        const items = saved ? JSON.parse(saved) : [];
        if (items.length > 0) {
          const validated = await api.validateGuestCart(items);
          setCart(validated);
        } else {
          setCart(defaultCart);
        }
      }
    } catch (err) {
      console.error('Error loading cart:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadCart();
  }, [isAuthenticated]);

  const addToCart = async (productId: string, quantity = 1, variantId?: string) => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        const updated = await api.addToCart(productId, quantity, variantId);
        setCart(updated);
      } else {
        const saved = localStorage.getItem('ssk_guest_cart');
        let items: any[] = saved ? JSON.parse(saved) : [];
        const existing = items.find(i => i.product_id === productId && i.variant_id === variantId);
        if (existing) {
          existing.quantity += quantity;
        } else {
          items.push({ product_id: productId, quantity, variant_id: variantId });
        }
        localStorage.setItem('ssk_guest_cart', JSON.stringify(items));
        const validated = await api.validateGuestCart(items);
        setCart(validated);
      }
      showToast('Item added to your shopping bag!');
    } catch (err: any) {
      showToast(err.message || 'Failed to add item to bag');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const updateQuantity = async (productId: string, quantity: number, variantId?: string) => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        const updated = await api.updateCartQuantity(productId, quantity, variantId);
        setCart(updated);
      } else {
        const saved = localStorage.getItem('ssk_guest_cart');
        let items: any[] = saved ? JSON.parse(saved) : [];
        if (quantity <= 0) {
          items = items.filter(i => !(i.product_id === productId && i.variant_id === variantId));
        } else {
          const item = items.find(i => i.product_id === productId && i.variant_id === variantId);
          if (item) item.quantity = quantity;
        }
        localStorage.setItem('ssk_guest_cart', JSON.stringify(items));
        const validated = await api.validateGuestCart(items);
        setCart(validated);
      }
    } catch (err: any) {
      showToast(err.message || 'Failed to update bag');
    } finally {
      setIsLoading(false);
    }
  };

  const removeFromCart = async (productId: string, variantId?: string) => {
    await updateQuantity(productId, 0, variantId);
    showToast('Item removed from shopping bag');
  };

  const applyCoupon = async (code: string) => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        const updated = await api.applyCoupon(code);
        setCart(updated);
      } else {
        const saved = localStorage.getItem('ssk_guest_cart');
        const items = saved ? JSON.parse(saved) : [];
        const validated = await api.validateGuestCart(items, code);
        setCart(validated);
      }
      showToast(`Coupon '${code.toUpperCase()}' applied successfully!`);
    } catch (err: any) {
      showToast(err.message || 'Invalid coupon code');
      throw err;
    } finally {
      setIsLoading(false);
    }
  };

  const removeCoupon = async () => {
    setIsLoading(true);
    try {
      if (isAuthenticated) {
        const updated = await api.removeCoupon();
        setCart(updated);
      } else {
        const saved = localStorage.getItem('ssk_guest_cart');
        const items = saved ? JSON.parse(saved) : [];
        const validated = await api.validateGuestCart(items);
        setCart(validated);
      }
      showToast('Coupon removed');
    } catch (err: any) {
      showToast(err.message || 'Failed to remove coupon');
    } finally {
      setIsLoading(false);
    }
  };

  const clearCart = () => {
    localStorage.removeItem('ssk_guest_cart');
    setCart(defaultCart);
  };

  const itemCount = cart.items.reduce((sum, i) => sum + i.quantity, 0);

  return (
    <CartContext.Provider
      value={{
        cart,
        isLoading,
        itemCount,
        addToCart,
        updateQuantity,
        removeFromCart,
        applyCoupon,
        removeCoupon,
        clearCart,
        toastMessage,
        clearToast: () => setToastMessage(null)
      }}
    >
      {children}
    </CartContext.Provider>
  );
};

export const useCart = () => {
  const context = useContext(CartContext);
  if (!context) throw new Error('useCart must be used within a CartProvider');
  return context;
};
