import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package, Clock, CheckCircle2, Truck, AlertTriangle, Printer,
  RotateCcw, XCircle, ArrowLeft, ShieldCheck, MapPin, Loader2
} from 'lucide-react';
import { api } from '../../services/api';
import { Order } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { modalOverlay, modalContent, fadeUp } from '../../animations';

export const OrderTrackingPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Cancellation and return modals
  const [showCancelModal, setShowCancelModal] = useState(false);
  const [cancelReason, setCancelReason] = useState('Found another alternative');
  const [cancelling, setCancelling] = useState(false);

  const [showReturnModal, setShowReturnModal] = useState(false);
  const [returnReason, setReturnReason] = useState('Item size does not fit');
  const [returnComments, setReturnComments] = useState('');
  const [submittingReturn, setSubmittingReturn] = useState(false);

  const [showInvoiceModal, setShowInvoiceModal] = useState(false);
  const [packingSlipData, setPackingSlipData] = useState<any>(null);

  const [guestVerificationInput, setGuestVerificationInput] = useState('');

  const loadOrder = async (verificationCode?: string) => {
    if (!orderId) return;
    setLoading(true);
    try {
      const storedToken = sessionStorage.getItem(`guest_token_${orderId}`) || undefined;
      const urlParams = new URLSearchParams(window.location.search);
      const urlVerification = urlParams.get('verify') || urlParams.get('email') || urlParams.get('phone') || undefined;
      const data = await api.getOrderById(orderId, verificationCode || urlVerification || storedToken);
      setOrder(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Could not find order details');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadOrder();
  }, [orderId]);

  const handleCancelOrder = async () => {
    if (!order) return;
    setCancelling(true);
    try {
      await api.cancelOrder(order.order_id, cancelReason);
      setShowCancelModal(false);
      await loadOrder();
    } catch (err: any) {
      alert(err.message || 'Failed to cancel order');
    } finally {
      setCancelling(false);
    }
  };

  const handleReturnOrder = async () => {
    if (!order) return;
    setSubmittingReturn(true);
    try {
      await api.requestReturn(order.order_id, {
        reason: returnReason,
        comments: returnComments,
        images: []
      });
      setShowReturnModal(false);
      await loadOrder();
    } catch (err: any) {
      alert(err.message || 'Failed to request return');
    } finally {
      setSubmittingReturn(false);
    }
  };

  const handleOpenInvoice = async () => {
    if (!order) return;
    try {
      const slip = await api.getPackingSlip(order.order_id);
      setPackingSlipData(slip);
      setShowInvoiceModal(true);
    } catch (e) {
      console.error(e);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 space-y-6">
        <div className="h-6 bg-gray-200 rounded w-1/3 animate-pulse" />
        <div className="h-48 bg-gray-200 rounded-3xl animate-pulse" />
      </div>
    );
  }

  if (error || !order) {
    return (
      <div className="max-w-md mx-auto text-center py-20 px-4 space-y-4">
        <AlertTriangle className="w-12 h-12 text-ssk-gold mx-auto" />
        <h2 className="text-xl font-serif font-bold text-ssk-navy">Order Verification Required</h2>
        <p className="text-xs text-ssk-text-secondary">
          {error || 'To protect customer privacy, please verify your email or phone number associated with this order.'}
        </p>
        
        <form
          onSubmit={(e) => {
            e.preventDefault();
            if (guestVerificationInput.trim()) {
              loadOrder(guestVerificationInput.trim());
            }
          }}
          className="space-y-3 pt-2"
        >
          <input
            type="text"
            required
            placeholder="Enter Order Email or Phone (+91...)"
            value={guestVerificationInput}
            onChange={(e) => setGuestVerificationInput(e.target.value)}
            className="w-full px-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
          />
          <button
            type="submit"
            className="w-full py-2.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl transition-all shadow-sm"
          >
            Verify & Track Order
          </button>
        </form>

        <div className="pt-2">
          <Link to="/shop" className="text-xs text-ssk-royal hover:underline font-medium">
            &larr; Back to Shop
          </Link>
        </div>
      </div>
    );
  }

  const canCancel = ['ORDER_PLACED', 'PAYMENT_PENDING', 'PAYMENT_CONFIRMED', 'PROCESSING'].includes(order.order_status);
  const canReturn = order.order_status === 'DELIVERED';

  return (
    <PageTransition className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Top Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link to="/account/orders" className="text-xs text-ssk-text-secondary hover:text-ssk-navy flex items-center gap-1 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Orders</span>
          </Link>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">
            Track Order #{order.order_id}
          </h1>
          <p className="text-xs text-ssk-text-secondary">
            Placed on {new Date(order.created_at).toLocaleDateString()} &bull; Total: ₹{order.final_amount}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={handleOpenInvoice}
            className="px-4 py-2 border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-sm transition-colors"
          >
            <Printer className="w-3.5 h-3.5" />
            <span>Invoice / Slip</span>
          </motion.button>
          {canCancel && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowCancelModal(true)}
              className="px-4 py-2 border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold rounded-xl transition-colors"
            >
              Cancel Order
            </motion.button>
          )}
          {canReturn && (
            <motion.button
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowReturnModal(true)}
              className="px-4 py-2 bg-ssk-gold hover:bg-ssk-gold-dark text-white text-xs font-semibold rounded-xl transition-colors flex items-center gap-1.5 shadow-sm"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Request Return</span>
            </motion.button>
          )}
        </div>
      </div>

      {/* Shipment & Tracking Details Card */}
      {order.tracking_number && (
        <div className="p-5 bg-ssk-blue-light/70 rounded-2xl border border-ssk-border flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-ssk-navy text-white flex items-center justify-center flex-shrink-0">
              <Truck className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[10px] text-ssk-text-secondary uppercase font-bold">Courier Partner</span>
              <p className="text-sm font-bold text-ssk-navy">{order.carrier_name || 'Standard Courier'}</p>
            </div>
          </div>
          <div>
            <span className="text-[10px] text-ssk-text-secondary uppercase font-bold">AWB / Tracking Number</span>
            <p className="text-sm font-mono font-bold text-ssk-navy">{order.tracking_number}</p>
          </div>
        </div>
      )}

      {/* Step Progress Bar */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border shadow-sm">
        <h3 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider mb-6">
          Fulfilment Journey
        </h3>

        <div className="relative">
          <div className="space-y-6">
            {order.timeline.map((event, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: i * 0.08 }}
                className="flex items-start gap-4"
              >
                <div className="relative flex flex-col items-center">
                  <div className="w-8 h-8 rounded-full bg-ssk-navy text-white flex items-center justify-center shadow-sm z-10">
                    <CheckCircle2 className="w-4 h-4 text-ssk-gold" />
                  </div>
                  {i < order.timeline.length - 1 && (
                    <div className="w-0.5 h-12 bg-ssk-border" />
                  )}
                </div>
                <div className="flex-1 pt-1">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1">
                    <h4 className="text-xs font-bold text-ssk-navy">{event.message}</h4>
                    <span className="text-[10px] text-ssk-text-secondary font-mono">
                      {new Date(event.timestamp).toLocaleString()}
                    </span>
                  </div>
                  {event.performed_by && (
                    <p className="text-[10px] text-ssk-text-secondary mt-0.5">By: {event.performed_by}</p>
                  )}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Ordered Items Summary */}
      <div className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm space-y-4">
        <h3 className="text-sm font-serif font-bold text-ssk-navy border-b border-ssk-border pb-3">
          Package Contents
        </h3>
        <div className="divide-y divide-ssk-border">
          {order.items.map((item, idx) => (
            <div key={idx} className="py-3 flex items-center justify-between text-xs">
              <div className="flex items-center gap-3">
                <img src={item.image || '/logo.svg'} alt={item.name} className="w-12 h-12 object-cover rounded-xl border border-ssk-border" />
                <div>
                  <p className="font-semibold text-ssk-text">{item.name}</p>
                  <span className="text-ssk-text-secondary text-[11px]">Qty: {item.quantity} &bull; Unit: ₹{item.unit_price}</span>
                </div>
              </div>
              <span className="font-bold text-ssk-navy">₹{item.total_price}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Cancel Modal with AnimatePresence */}
      <AnimatePresence>
        {showCancelModal && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border space-y-4"
            >
              <h3 className="text-base font-serif font-bold text-ssk-navy">Cancel Order #{order.order_id}</h3>
              <p className="text-xs text-ssk-text-secondary">
                Cancelling this order will release the reserved inventory back to our stock and stop packaging.
              </p>
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Reason for cancellation</label>
                <select
                  value={cancelReason}
                  onChange={(e) => setCancelReason(e.target.value)}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                >
                  <option value="Found another alternative">Found another alternative</option>
                  <option value="Ordered by mistake">Ordered by mistake</option>
                  <option value="Need to change shipping address">Need to change shipping address</option>
                  <option value="Change in festival dates">Change in festival dates</option>
                </select>
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowCancelModal(false)}
                  className="flex-1 py-2.5 border border-ssk-border rounded-xl text-xs font-semibold text-ssk-text"
                >
                  Keep Order
                </button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleCancelOrder}
                  disabled={cancelling}
                  className="flex-1 py-2.5 bg-red-600 text-white text-xs font-semibold rounded-xl hover:bg-red-700 shadow-sm transition-colors flex items-center justify-center gap-1.5"
                >
                  {cancelling ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Cancelling...</span>
                    </>
                  ) : (
                    <span>Confirm Cancellation</span>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Return Modal with AnimatePresence */}
      <AnimatePresence>
        {showReturnModal && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border space-y-4"
            >
              <h3 className="text-base font-serif font-bold text-ssk-navy">Request 7-Day Return</h3>
              <p className="text-xs text-ssk-text-secondary">
                Our quality team will review your request and arrange a free pickup within 24-48 hours.
              </p>
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Reason for Return</label>
                <select
                  value={returnReason}
                  onChange={(e) => setReturnReason(e.target.value)}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                >
                  <option value="Item size does not fit">Item size does not fit</option>
                  <option value="Color or stone looks different than expected">Color or stone looks different than expected</option>
                  <option value="Received damaged or broken piece">Received damaged or broken piece</option>
                  <option value="Quality not as expected">Quality not as expected</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Additional Comments</label>
                <textarea
                  rows={3}
                  value={returnComments}
                  onChange={(e) => setReturnComments(e.target.value)}
                  placeholder="Describe any issues..."
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                />
              </div>
              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => setShowReturnModal(false)}
                  className="flex-1 py-2.5 border border-ssk-border rounded-xl text-xs font-semibold text-ssk-text"
                >
                  Cancel
                </button>
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={handleReturnOrder}
                  disabled={submittingReturn}
                  className="flex-1 py-2.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm transition-colors flex items-center justify-center gap-1.5"
                >
                  {submittingReturn ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Submitting...</span>
                    </>
                  ) : (
                    <span>Submit Request</span>
                  )}
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Invoice / Packing Slip Modal with AnimatePresence */}
      <AnimatePresence>
        {showInvoiceModal && packingSlipData && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="bg-white rounded-3xl max-w-2xl w-full p-8 shadow-2xl border border-ssk-border space-y-6 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between border-b border-ssk-border pb-4">
                <div>
                  <h3 className="text-xl font-serif font-bold text-ssk-navy">{packingSlipData.brand_name}</h3>
                  <p className="text-xs text-ssk-text-secondary">{packingSlipData.business_address}</p>
                  <p className="text-xs text-ssk-text-secondary">GSTIN: 36AAECR9988C1Z4 • Phone: {packingSlipData.support_phone}</p>
                </div>
                <div className="text-right">
                  <span className="text-xs font-bold text-ssk-gold uppercase block">Tax Invoice / Packing Slip</span>
                  <span className="text-xs font-mono font-bold text-ssk-navy">#{order.order_id}</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-ssk-text-secondary uppercase font-bold text-[10px]">Billed & Shipped To:</span>
                  <p className="font-bold text-ssk-text mt-1">{order.shipping_address.name}</p>
                  <p className="text-ssk-text-secondary">{order.shipping_address.address_line1}</p>
                  <p className="text-ssk-text-secondary">{order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}</p>
                  <p className="text-ssk-text-secondary">Phone: {order.shipping_address.phone}</p>
                </div>
                <div className="text-right space-y-1">
                  <p><span className="text-ssk-text-secondary">Order Date:</span> {new Date(order.created_at).toLocaleDateString()}</p>
                  <p><span className="text-ssk-text-secondary">Payment Method:</span> {order.payment_method}</p>
                  <p><span className="text-ssk-text-secondary">Payment Status:</span> <strong className="text-ssk-success">{order.payment_status}</strong></p>
                </div>
              </div>

              <table className="w-full text-xs text-left border-collapse border border-ssk-border">
                <thead>
                  <tr className="bg-ssk-surface border-b border-ssk-border">
                    <th className="p-2.5">Item Description</th>
                    <th className="p-2.5">SKU</th>
                    <th className="p-2.5 text-center">Qty</th>
                    <th className="p-2.5 text-right">Unit Price</th>
                    <th className="p-2.5 text-right">Total</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-ssk-border">
                  {order.items.map((item, idx) => (
                    <tr key={idx}>
                      <td className="p-2.5 font-semibold">{item.name}</td>
                      <td className="p-2.5 font-mono">{item.sku}</td>
                      <td className="p-2.5 text-center">{item.quantity}</td>
                      <td className="p-2.5 text-right">₹{item.unit_price}</td>
                      <td className="p-2.5 text-right font-bold">₹{item.total_price}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex justify-end text-xs">
                <div className="w-64 space-y-1.5 border-t border-ssk-border pt-2">
                  <div className="flex justify-between">
                    <span>Subtotal:</span>
                    <span>₹{order.subtotal}</span>
                  </div>
                  {order.discount_amount > 0 && (
                    <div className="flex justify-between text-ssk-success">
                      <span>Discount:</span>
                      <span>-₹{order.discount_amount}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span>Shipping:</span>
                    <span>{order.shipping_fee === 0 ? 'FREE' : `₹${order.shipping_fee}`}</span>
                  </div>
                  <div className="flex justify-between text-sm font-bold text-ssk-navy pt-2 border-t border-ssk-border">
                    <span>Grand Total:</span>
                    <span>₹{order.final_amount}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-ssk-border">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => window.print()}
                  className="px-5 py-2 bg-ssk-navy text-white text-xs font-bold rounded-xl shadow-sm flex items-center gap-1.5"
                >
                  <Printer className="w-4 h-4" />
                  <span>Print Document</span>
                </motion.button>
                <button
                  onClick={() => setShowInvoiceModal(false)}
                  className="px-5 py-2 border border-ssk-border text-xs font-semibold rounded-xl hover:bg-gray-100 transition-colors"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
};
