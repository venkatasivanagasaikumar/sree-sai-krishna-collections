import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Trash2, ShoppingBag, ArrowRight, Tag, Truck, ShieldCheck } from 'lucide-react';
import { useCart } from '../../context/CartContext';
import { PageTransition } from '../../components/animations/PageTransition';
import { FadeIn } from '../../components/animations/FadeIn';

export const CartPage: React.FC = () => {
  const navigate = useNavigate();
  const { cart, updateQuantity, removeFromCart, applyCoupon, removeCoupon, isLoading } = useCart();
  const [couponInput, setCouponInput] = useState('');
  const [couponError, setCouponError] = useState<string | null>(null);

  const handleApplyCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    setCouponError(null);
    if (!couponInput.trim()) return;
    try {
      await applyCoupon(couponInput.trim());
      setCouponInput('');
    } catch (err: any) {
      setCouponError(err.message || 'Invalid coupon');
    }
  };

  if (cart.items.length === 0) {
    return (
      <PageTransition className="max-w-2xl mx-auto text-center py-24 px-4">
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="w-20 h-20 bg-ssk-blue-light rounded-full flex items-center justify-center mx-auto mb-4 text-ssk-navy shadow-sm"
        >
          <ShoppingBag className="w-10 h-10" />
        </motion.div>
        <h2 className="text-2xl font-serif font-bold text-ssk-navy mb-2">Your Shopping Bag is Empty</h2>
        <p className="text-xs sm:text-sm text-ssk-text-secondary max-w-sm mx-auto mb-6">
          Explore our handcrafted 1-gram gold sets, antique jhumkas, and premium hair accessories to add elegance to your collection.
        </p>
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="inline-block">
          <Link
            to="/shop"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl shadow-lg transition-all"
          >
            <span>Explore Jewellery</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy mb-8">
        Your Shopping Bag ({cart.items.reduce((sum, i) => sum + i.quantity, 0)} items)
      </h1>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left: Cart Items List */}
        <div className="lg:col-span-8 space-y-4">
          
          {/* Free Shipping Progress Alert */}
          <div className="p-4 bg-ssk-blue-light/70 rounded-2xl border border-ssk-border space-y-2 shadow-sm">
            <div className="flex items-center justify-between text-xs font-bold text-ssk-navy">
              <span className="flex items-center gap-1.5">
                <Truck className="w-4 h-4 text-ssk-gold" />
                {cart.free_shipping_eligible ? (
                  <span className="text-ssk-success">You have unlocked FREE Express Delivery!</span>
                ) : (
                  <span>Add ₹{cart.amount_needed_for_free_shipping} more for FREE Express Shipping</span>
                )}
              </span>
              <span>₹999 Threshold</span>
            </div>
            <div className="w-full bg-white rounded-full h-2 overflow-hidden border border-ssk-border">
              <motion.div
                className="bg-gradient-to-r from-ssk-gold to-ssk-navy h-2 rounded-full"
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.round((cart.subtotal / 999) * 100))}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              />
            </div>
          </div>

          {/* Items Container with AnimatePresence */}
          <div className="bg-white rounded-2xl border border-ssk-border divide-y divide-ssk-border shadow-sm overflow-hidden">
            <AnimatePresence>
              {cart.items.map((item) => (
                <motion.div
                  key={`${item.product_id}-${item.variant_id || 'default'}`}
                  layout
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20, height: 0, overflow: 'hidden' }}
                  transition={{ duration: 0.25 }}
                  className="p-4 sm:p-6 flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between"
                >
                  <div className="flex gap-4 items-center flex-1">
                    <img
                      src={item.image || '/logo.svg'}
                      alt={item.name}
                      className="w-20 h-20 rounded-xl object-cover border border-ssk-border flex-shrink-0"
                    />
                    <div className="space-y-1">
                      <Link
                        to={`/product/${item.sku}`}
                        className="text-xs sm:text-sm font-semibold text-ssk-text hover:text-ssk-navy line-clamp-2 leading-snug transition-colors"
                      >
                        {item.name}
                      </Link>
                      <p className="text-[11px] text-ssk-text-secondary font-mono">SKU: {item.sku}</p>
                      <div className="flex items-baseline gap-2">
                        <span className="text-sm font-bold text-ssk-navy">₹{item.price.toLocaleString('en-IN')}</span>
                        {item.mrp > item.price && (
                          <span className="text-xs text-ssk-text-secondary line-through">₹{item.mrp.toLocaleString('en-IN')}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Quantity Controls & Delete */}
                  <div className="flex items-center justify-between sm:justify-end gap-6 w-full sm:w-auto pt-2 sm:pt-0 border-t sm:border-0 border-ssk-border">
                    <div className="flex items-center border border-ssk-border rounded-xl bg-white overflow-hidden shadow-sm">
                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={() => updateQuantity(item.product_id, item.quantity - 1, item.variant_id)}
                        className="px-3 py-1.5 hover:bg-gray-100 text-xs font-bold text-ssk-navy"
                      >
                        -
                      </motion.button>
                      <span className="px-3 py-1.5 text-xs font-bold text-ssk-text min-w-[28px] text-center">
                        {item.quantity}
                      </span>
                      <motion.button
                        whileTap={{ scale: 0.9 }}
                        onClick={() => updateQuantity(item.product_id, item.quantity + 1, item.variant_id)}
                        className="px-3 py-1.5 hover:bg-gray-100 text-xs font-bold text-ssk-navy"
                      >
                        +
                      </motion.button>
                    </div>

                    <div className="text-right min-w-[80px]">
                      <span className="text-sm font-bold text-ssk-navy">
                        ₹{item.total_price.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.15 }}
                      whileTap={{ scale: 0.85 }}
                      onClick={() => removeFromCart(item.product_id, item.variant_id)}
                      className="p-2 text-ssk-text-secondary hover:text-ssk-error rounded-lg hover:bg-red-50 transition-colors"
                      title="Remove item"
                      aria-label="Remove item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          <div className="flex items-center justify-between pt-2">
            <Link
              to="/shop"
              className="text-xs font-bold text-ssk-navy hover:text-ssk-gold flex items-center gap-1 transition-colors"
            >
              &larr; Continue Shopping
            </Link>
          </div>
        </div>

        {/* Right: Order Summary Card */}
        <div className="lg:col-span-4 space-y-4 sticky top-28">
          
          {/* Coupon Box */}
          <div className="bg-white p-5 rounded-2xl border border-ssk-border shadow-sm space-y-3">
            <h3 className="text-xs font-bold text-ssk-navy uppercase tracking-wider flex items-center gap-1.5">
              <Tag className="w-4 h-4 text-ssk-gold" />
              <span>Apply Promo Code</span>
            </h3>

            {cart.coupon_code ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-xl text-xs"
              >
                <div>
                  <span className="font-bold text-green-800">{cart.coupon_code}</span>
                  <span className="block text-[10px] text-green-700">₹{cart.discount_amount} saved</span>
                </div>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={removeCoupon}
                  className="text-xs text-red-600 font-bold hover:underline"
                >
                  Remove
                </motion.button>
              </motion.div>
            ) : (
              <form onSubmit={handleApplyCoupon} className="space-y-2">
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Enter code (e.g. SSKFIRST10)"
                    value={couponInput}
                    onChange={(e) => setCouponInput(e.target.value.toUpperCase())}
                    className="flex-1 px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-mono uppercase focus:outline-none focus:border-ssk-gold"
                  />
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    type="submit"
                    className="px-4 py-2 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl transition-colors"
                  >
                    Apply
                  </motion.button>
                </div>
                {couponError && <p className="text-[11px] text-ssk-error">{couponError}</p>}
              </form>
            )}
          </div>

          {/* Pricing Breakdown */}
          <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-bold text-ssk-navy border-b border-ssk-border pb-3">
              Order Summary
            </h3>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between text-ssk-text">
                <span>Subtotal</span>
                <span className="font-semibold">₹{cart.subtotal.toLocaleString('en-IN')}</span>
              </div>

              {cart.discount_amount > 0 && (
                <div className="flex justify-between text-ssk-success font-medium">
                  <span>Coupon Discount</span>
                  <span>-₹{cart.discount_amount.toLocaleString('en-IN')}</span>
                </div>
              )}

              <div className="flex justify-between text-ssk-text">
                <span>Estimated Shipping</span>
                <span className="font-semibold">
                  {cart.shipping_fee === 0 ? (
                    <span className="text-ssk-success uppercase font-bold text-[11px]">FREE</span>
                  ) : (
                    `₹${cart.shipping_fee}`
                  )}
                </span>
              </div>

              <div className="pt-3 border-t border-ssk-border flex justify-between items-baseline text-base font-bold text-ssk-navy">
                <span>Total Amount</span>
                <span className="text-xl font-serif">₹{cart.final_amount.toLocaleString('en-IN')}</span>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={() => navigate('/checkout')}
              className="w-full py-4 bg-gradient-to-r from-ssk-gold to-ssk-gold-dark hover:from-ssk-gold-light hover:to-ssk-gold text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
            >
              <span>Proceed to Checkout</span>
              <ArrowRight className="w-4 h-4" />
            </motion.button>

            <div className="pt-2 flex items-center justify-center gap-2 text-[10px] text-ssk-text-secondary">
              <ShieldCheck className="w-3.5 h-3.5 text-ssk-success" />
              <span>Safe & Secure 256-bit Encrypted Checkout</span>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  );
};
