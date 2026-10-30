import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Tag, Plus, Trash2, CheckCircle2, XCircle, AlertCircle, X, Loader2 } from 'lucide-react';
import { api } from '../../services/api';
import { Coupon } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { modalOverlay, modalContent } from '../../animations';

export const AdminPromotionsPage: React.FC = () => {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  const [code, setCode] = useState('');
  const [description, setDescription] = useState('');
  const [discountType, setDiscountType] = useState<'percentage' | 'fixed'>('percentage');
  const [discountValue, setDiscountValue] = useState(10);
  const [minOrderValue, setMinOrderValue] = useState(499);
  const [maxDiscount, setMaxDiscount] = useState<number | undefined>(300);
  const [isSaving, setIsSaving] = useState(false);

  const fetchCoupons = async () => {
    setLoading(true);
    try {
      const data = await api.listCouponsAdmin();
      setCoupons(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCoupons();
  }, []);

  const handleCreateCoupon = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await api.createCoupon({
        code,
        description,
        discount_type: discountType,
        discount_value: discountValue,
        min_order_value: minOrderValue,
        max_discount_amount: maxDiscount || undefined,
        is_active: true
      });
      setShowModal(false);
      setCode('');
      setDescription('');
      await fetchCoupons();
    } catch (err: any) {
      alert(err.message || 'Failed to create coupon');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this coupon?')) return;
    try {
      await api.deleteCoupon(id);
      await fetchCoupons();
    } catch (e: any) {
      alert(e.message || 'Delete failed');
    }
  };

  return (
    <PageTransition className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Discounts & Promotions</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Create percentage discounts, festive coupons, and minimum order rules.
          </p>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => setShowModal(true)}
          className="px-5 py-2.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-md transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>Create Coupon</span>
        </motion.button>
      </div>

      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-ssk-surface text-ssk-text-secondary border-b uppercase font-semibold text-[10px] tracking-wider">
            <tr>
              <th className="py-4 px-6">Coupon Code</th>
              <th className="py-4 px-4">Description</th>
              <th className="py-4 px-4">Discount</th>
              <th className="py-4 px-4">Min Order</th>
              <th className="py-4 px-4">Max Cap</th>
              <th className="py-4 px-4">Times Used</th>
              <th className="py-4 px-6 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ssk-border font-medium">
            {coupons.map((c) => (
              <tr key={c.id} className="hover:bg-ssk-blue-light/30 transition-colors">
                <td className="py-4 px-6 font-mono font-bold text-ssk-navy text-sm">{c.code}</td>
                <td className="py-4 px-4 text-ssk-text max-w-xs">{c.description}</td>
                <td className="py-4 px-4 font-bold text-green-700">
                  {c.discount_type === 'percentage' ? `${c.discount_value}% OFF` : `₹${c.discount_value} FLAT`}
                </td>
                <td className="py-4 px-4 font-semibold">₹{c.min_order_value}</td>
                <td className="py-4 px-4 text-ssk-text-secondary">{c.max_discount_amount ? `₹${c.max_discount_amount}` : 'None'}</td>
                <td className="py-4 px-4 font-bold text-ssk-navy">{c.times_used || 0} times</td>
                <td className="py-4 px-6 text-right">
                  <motion.button
                    whileHover={{ scale: 1.15 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={() => handleDelete(c.id)}
                    className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    aria-label="Delete coupon"
                  >
                    <Trash2 className="w-4 h-4" />
                  </motion.button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Modal with AnimatePresence */}
      <AnimatePresence>
        {showModal && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm text-xs"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border space-y-4"
            >
              <div className="flex items-center justify-between border-b pb-3">
                <h3 className="text-sm font-serif font-bold text-ssk-navy">Create Promo Coupon</h3>
                <button onClick={() => setShowModal(false)} aria-label="Close modal">
                  <X className="w-5 h-5 text-ssk-text-secondary" />
                </button>
              </div>

              <form onSubmit={handleCreateCoupon} className="space-y-4">
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Coupon Code *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. BRIDAL20"
                    value={code}
                    onChange={(e) => setCode(e.target.value.toUpperCase())}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-mono uppercase font-bold focus:outline-none focus:border-ssk-gold"
                  />
                </div>

                <div>
                  <label className="block font-bold text-ssk-text mb-1">Description *</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. 20% discount on bridal jewellery sets"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-bold text-ssk-text mb-1">Discount Type</label>
                    <select
                      value={discountType}
                      onChange={(e: any) => setDiscountType(e.target.value)}
                      className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold"
                    >
                      <option value="percentage">Percentage (%)</option>
                      <option value="fixed">Fixed Amount (₹)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-bold text-ssk-text mb-1">Discount Value *</label>
                    <input
                      type="number"
                      required
                      min={1}
                      value={discountValue}
                      onChange={(e) => setDiscountValue(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold text-ssk-navy focus:outline-none focus:border-ssk-gold"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block font-bold text-ssk-text mb-1">Min Order Value (₹)</label>
                    <input
                      type="number"
                      required
                      min={0}
                      value={minOrderValue}
                      onChange={(e) => setMinOrderValue(Number(e.target.value))}
                      className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold"
                    />
                  </div>
                  <div>
                    <label className="block font-bold text-ssk-text mb-1">Max Discount Cap (₹)</label>
                    <input
                      type="number"
                      value={maxDiscount || ''}
                      onChange={(e) => setMaxDiscount(e.target.value ? Number(e.target.value) : undefined)}
                      placeholder="Optional max cap"
                      className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 border rounded-xl hover:bg-gray-100 transition-colors"
                  >
                    Cancel
                  </button>
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    type="submit"
                    disabled={isSaving}
                    className="px-5 py-2 bg-ssk-navy text-white rounded-xl font-bold hover:bg-ssk-navy-dark transition-colors flex items-center gap-1.5"
                  >
                    {isSaving ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Creating...</span>
                      </>
                    ) : (
                      <span>Publish Coupon</span>
                    )}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
};
