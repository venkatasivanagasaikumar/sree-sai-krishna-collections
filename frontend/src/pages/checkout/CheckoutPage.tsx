import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Truck, CreditCard, Banknote, ArrowRight, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { api } from '../../services/api';
import { Address } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { modalOverlay, modalContent, fadeDown } from '../../animations';

export const CheckoutPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();
  const { cart, clearCart } = useCart();

  const [address, setAddress] = useState<Address>({
    name: user?.full_name || '',
    phone: user?.phone || '',
    address_line1: '',
    address_line2: '',
    landmark: '',
    city: 'Hyderabad',
    state: 'Telangana',
    pincode: '',
    is_default: true,
    type: 'Home'
  });

  const [guestEmail, setGuestEmail] = useState(user?.email || '');
  const [paymentMethod, setPaymentMethod] = useState<'Razorpay' | 'COD'>('Razorpay');
  const [orderNotes, setOrderNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Razorpay Modal state
  const [showRazorpayModal, setShowRazorpayModal] = useState(false);
  const [razorpayOrderData, setRazorpayOrderData] = useState<any>(null);
  const [isProcessingPayment, setIsProcessingPayment] = useState(false);

  // Pre-fill user details if logged in
  useEffect(() => {
    if (user) {
      setGuestEmail(user.email);
      if (user.addresses && user.addresses.length > 0) {
        const def = user.addresses.find(a => a.is_default) || user.addresses[0];
        setAddress(def);
      } else {
        setAddress(prev => ({ ...prev, name: user.full_name, phone: user.phone || '' }));
      }
    }
  }, [user]);

  if (cart.items.length === 0) {
    navigate('/cart');
    return null;
  }

  const handlePlaceOrder = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    // Basic Validation
    if (!address.name || !address.phone || !address.address_line1 || !address.city || !address.state || !address.pincode) {
      setErrorMessage('Please fill in all mandatory shipping address fields.');
      return;
    }
    if (!/^\d{6}$/.test(address.pincode)) {
      setErrorMessage('Please enter a valid 6-digit PIN code.');
      return;
    }
    if (!guestEmail || !guestEmail.includes('@')) {
      setErrorMessage('Please provide a valid email address for order confirmation.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Create Order on Server
      const orderPayload = {
        shipping_address: address,
        payment_method: paymentMethod,
        coupon_code: cart.coupon_code || undefined,
        notes: orderNotes || undefined,
        guest_email: guestEmail,
        guest_name: address.name,
        guest_phone: address.phone,
        cart_items: !isAuthenticated ? cart.items.map(i => ({ product_id: i.product_id, quantity: i.quantity, variant_id: i.variant_id })) : undefined
      };

      const orderResult = await api.createOrder(orderPayload);
      const createdOrderId = orderResult.order_id;
      if (orderResult.guest_token) {
        sessionStorage.setItem(`guest_token_${createdOrderId}`, orderResult.guest_token);
      }

      if (paymentMethod === 'COD') {
        clearCart();
        navigate(`/order-success/${createdOrderId}`);
      } else {
        // Trigger Razorpay Order Creation on server
        const rzpOrder = await api.createRazorpayOrder(createdOrderId);
        const rzpWindow = (window as any).Razorpay;

        if (rzpWindow && rzpOrder.key_id && !rzpOrder.key_id.includes('Demo') && !rzpOrder.key_id.includes('mock')) {
          const rzp = new rzpWindow({
            key: rzpOrder.key_id,
            amount: rzpOrder.amount_in_paise,
            currency: rzpOrder.currency || 'INR',
            name: rzpOrder.business_name || 'Sree Sai Krishna Collections',
            description: `Jewellery Order ${rzpOrder.order_id}`,
            order_id: rzpOrder.razorpay_order_id,
            prefill: rzpOrder.prefill,
            theme: { color: '#123F7A' },
            handler: async (response: any) => {
              try {
                const verifyRes = await api.verifyRazorpayPayment({
                  order_id: rzpOrder.order_id,
                  razorpay_order_id: response.razorpay_order_id,
                  razorpay_payment_id: response.razorpay_payment_id,
                  razorpay_signature: response.razorpay_signature
                });
                if (verifyRes.success) {
                  clearCart();
                  navigate(`/order-success/${rzpOrder.order_id}`);
                } else {
                  setErrorMessage('Payment verification rejected by backend.');
                }
              } catch (err: any) {
                setErrorMessage(err.message || 'Payment signature verification failed.');
              }
            },
            modal: {
              ondismiss: () => {
                setErrorMessage('Payment cancelled. You can retry payment or select Cash on Delivery.');
              }
            }
          });
          rzp.open();
        } else {
          // Open interactive sandbox payment simulator modal for local/test mode
          setRazorpayOrderData(rzpOrder);
          setShowRazorpayModal(true);
        }
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to place order. Please review your details.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCompleteRazorpayPayment = async () => {
    if (!razorpayOrderData) return;
    setIsProcessingPayment(true);
    try {
      // Simulate real gateway capture and verify signature on backend
      const mockPaymentId = `pay_${Date.now().toString(36)}`;
      const verifyRes = await api.verifyRazorpayPayment({
        order_id: razorpayOrderData.order_id,
        razorpay_order_id: razorpayOrderData.razorpay_order_id,
        razorpay_payment_id: mockPaymentId,
        razorpay_signature: 'sandbox_success'
      });

      if (verifyRes.success) {
        clearCart();
        navigate(`/order-success/${razorpayOrderData.order_id}`);
      } else {
        setErrorMessage('Payment verification rejected by backend.');
      }
    } catch (err: any) {
      setErrorMessage(err.message || 'Payment verification failed.');
    } finally {
      setIsProcessingPayment(false);
      setShowRazorpayModal(false);
    }
  };

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy mb-8">
        Secure Checkout
      </h1>

      <AnimatePresence>
        {errorMessage && (
          <motion.div
            variants={fadeDown}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="mb-6 p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-2xl flex items-center gap-3"
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{errorMessage}</span>
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handlePlaceOrder} className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: Contact, Address & Payment */}
        <div className="lg:col-span-8 space-y-6">
          
          {/* Step 1: Customer Contact */}
          <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
            <h2 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ssk-navy text-white text-xs flex items-center justify-center font-sans">1</span>
              <span>Contact Information</span>
            </h2>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  value={guestEmail}
                  onChange={(e) => setGuestEmail(e.target.value)}
                  placeholder="For order tracking & invoice"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Mobile Phone *</label>
                <input
                  type="tel"
                  required
                  value={address.phone}
                  onChange={(e) => setAddress({ ...address, phone: e.target.value })}
                  placeholder="+91 98480 22338"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>
            </div>
          </div>

          {/* Step 2: Delivery Address */}
          <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
            <h2 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ssk-navy text-white text-xs flex items-center justify-center font-sans">2</span>
              <span>Delivery Address</span>
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Full Name (Recipient) *</label>
                <input
                  type="text"
                  required
                  value={address.name}
                  onChange={(e) => setAddress({ ...address, name: e.target.value })}
                  placeholder="e.g. Priya Sharma"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Flat, House no., Building, Apartment *</label>
                <input
                  type="text"
                  required
                  value={address.address_line1}
                  onChange={(e) => setAddress({ ...address, address_line1: e.target.value })}
                  placeholder="Flat 402, Sai Balaji Residency"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ssk-text mb-1">Area, Street, Sector, Village</label>
                  <input
                    type="text"
                    value={address.address_line2 || ''}
                    onChange={(e) => setAddress({ ...address, address_line2: e.target.value })}
                    placeholder="Road No. 3, Banjara Hills"
                    className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ssk-text mb-1">Landmark (Optional)</label>
                  <input
                    type="text"
                    value={address.landmark || ''}
                    onChange={(e) => setAddress({ ...address, landmark: e.target.value })}
                    placeholder="Near Clock Tower / Temple"
                    className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-ssk-text mb-1">PIN Code *</label>
                  <input
                    type="text"
                    required
                    maxLength={6}
                    value={address.pincode}
                    onChange={(e) => setAddress({ ...address, pincode: e.target.value })}
                    placeholder="500034"
                    className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-mono focus:outline-none focus:border-ssk-gold transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ssk-text mb-1">City / Town *</label>
                  <input
                    type="text"
                    required
                    value={address.city}
                    onChange={(e) => setAddress({ ...address, city: e.target.value })}
                    placeholder="Hyderabad"
                    className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-ssk-text mb-1">State *</label>
                  <input
                    type="text"
                    required
                    value={address.state}
                    onChange={(e) => setAddress({ ...address, state: e.target.value })}
                    placeholder="Telangana"
                    className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Step 3: Payment Method */}
          <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
            <h2 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ssk-navy text-white text-xs flex items-center justify-center font-sans">3</span>
              <span>Payment Option</span>
            </h2>

            <div className="space-y-3">
              {/* Razorpay Online */}
              <label
                className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                  paymentMethod === 'Razorpay'
                    ? 'border-ssk-navy bg-ssk-blue-light/50 ring-2 ring-ssk-navy/10'
                    : 'border-ssk-border hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="payment_method"
                  value="Razorpay"
                  checked={paymentMethod === 'Razorpay'}
                  onChange={() => setPaymentMethod('Razorpay')}
                  className="mt-1 accent-ssk-navy"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-ssk-navy" />
                    <span className="text-xs font-bold text-ssk-navy">Razorpay Secure Online Payment</span>
                    <span className="text-[10px] bg-green-100 text-green-800 font-bold px-2 py-0.5 rounded-full">Recommended</span>
                  </div>
                  <p className="text-[11px] text-ssk-text-secondary mt-1">
                    UPI (Google Pay, PhonePe, Paytm), Credit & Debit Cards, NetBanking. Fast dispatch.
                  </p>
                </div>
              </label>

              {/* Cash on Delivery */}
              <label
                className={`flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-all ${
                  paymentMethod === 'COD'
                    ? 'border-ssk-navy bg-ssk-blue-light/50 ring-2 ring-ssk-navy/10'
                    : 'border-ssk-border hover:bg-gray-50'
                }`}
              >
                <input
                  type="radio"
                  name="payment_method"
                  value="COD"
                  checked={paymentMethod === 'COD'}
                  onChange={() => setPaymentMethod('COD')}
                  className="mt-1 accent-ssk-navy"
                />
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <Banknote className="w-4 h-4 text-ssk-gold" />
                    <span className="text-xs font-bold text-ssk-text">Cash on Delivery (COD)</span>
                  </div>
                  <p className="text-[11px] text-ssk-text-secondary mt-1">
                    Pay in cash upon physical delivery at your doorstep. Verified Indian PIN codes only.
                  </p>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Right Column: Order Review & Submit */}
        <div className="lg:col-span-4 space-y-4 sticky top-28">
          <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
            <h3 className="text-sm font-serif font-bold text-ssk-navy border-b border-ssk-border pb-3">
              Items in Bag ({cart.items.length})
            </h3>

            <div className="max-h-56 overflow-y-auto space-y-3 pr-1 divide-y divide-ssk-border">
              {cart.items.map((item) => (
                <div key={item.product_id} className="pt-2 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 min-w-0 pr-2">
                    <img src={item.image || '/logo.svg'} alt={item.name} className="w-10 h-10 object-cover rounded-lg border border-ssk-border flex-shrink-0" />
                    <div className="truncate">
                      <p className="font-semibold text-ssk-text truncate">{item.name}</p>
                      <span className="text-ssk-text-secondary text-[10px]">Qty: {item.quantity}</span>
                    </div>
                  </div>
                  <span className="font-bold text-ssk-navy whitespace-nowrap">₹{item.total_price}</span>
                </div>
              ))}
            </div>

            <div className="pt-4 border-t border-ssk-border space-y-2 text-xs">
              <div className="flex justify-between text-ssk-text">
                <span>Subtotal</span>
                <span>₹{cart.subtotal.toLocaleString('en-IN')}</span>
              </div>
              {cart.discount_amount > 0 && (
                <div className="flex justify-between text-ssk-success font-medium">
                  <span>Discount ({cart.coupon_code})</span>
                  <span>-₹{cart.discount_amount.toLocaleString('en-IN')}</span>
                </div>
              )}
              <div className="flex justify-between text-ssk-text">
                <span>Delivery</span>
                <span className="font-semibold text-ssk-success">
                  {cart.shipping_fee === 0 ? 'FREE' : `₹${cart.shipping_fee}`}
                </span>
              </div>
              <div className="pt-3 border-t border-ssk-border flex justify-between items-baseline text-base font-bold text-ssk-navy">
                <span>Payable Amount</span>
                <span className="text-xl font-serif">₹{cart.final_amount.toLocaleString('en-IN')}</span>
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isSubmitting}
              className="w-full py-4 bg-gradient-to-r from-ssk-gold to-ssk-gold-dark hover:from-ssk-gold-light hover:to-ssk-gold text-white font-bold text-xs uppercase tracking-wider rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Validating Order...</span>
                </>
              ) : (
                <>
                  <span>{paymentMethod === 'COD' ? 'Confirm COD Order' : 'Proceed to Razorpay'}</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>

            <div className="text-[10px] text-center text-ssk-text-secondary">
              By placing your order, you agree to SSK Collections' Terms of Service and Privacy Policy.
            </div>
          </div>
        </div>
      </form>

      {/* Razorpay Payment Simulator Modal with AnimatePresence */}
      <AnimatePresence>
        {showRazorpayModal && razorpayOrderData && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
          >
            <motion.div
              variants={modalContent}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border relative space-y-4"
            >
              <div className="text-center space-y-2">
                <div className="w-12 h-12 bg-ssk-navy text-white rounded-2xl flex items-center justify-center mx-auto shadow-md">
                  <CreditCard className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-serif font-bold text-ssk-navy">Razorpay Payment Gateway</h3>
                <p className="text-xs text-ssk-text-secondary">Order Reference: {razorpayOrderData.order_id}</p>
              </div>

              <div className="p-4 bg-ssk-surface rounded-2xl border border-ssk-border text-center space-y-1">
                <span className="text-xs text-ssk-text-secondary block">Amount to Pay</span>
                <span className="text-3xl font-serif font-bold text-ssk-navy">
                  ₹{(razorpayOrderData.amount_in_paise / 100).toLocaleString('en-IN')}
                </span>
                <span className="text-[11px] text-ssk-success font-semibold block">256-bit Bank Grade Encryption</span>
              </div>

              <div className="space-y-2 text-xs">
                <div className="p-3 bg-white border border-ssk-border rounded-xl flex items-center justify-between">
                  <span className="font-semibold text-ssk-text">UPI (GPay, PhonePe, Paytm)</span>
                  <CheckCircle2 className="w-4 h-4 text-ssk-success" />
                </div>
                <div className="p-3 bg-white border border-ssk-border rounded-xl flex items-center justify-between opacity-70">
                  <span className="font-semibold text-ssk-text">Debit / Credit Card (Visa, RuPay)</span>
                  <span className="text-[10px] text-ssk-text-secondary">Supported</span>
                </div>
              </div>

              <div className="pt-2 space-y-2">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleCompleteRazorpayPayment}
                  disabled={isProcessingPayment}
                  className="w-full py-3.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white font-bold text-xs rounded-xl shadow-lg transition-all flex items-center justify-center gap-2"
                >
                  {isProcessingPayment ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Verifying Gateway Signature...</span>
                    </>
                  ) : (
                    <span>Simulate Successful Payment</span>
                  )}
                </motion.button>
                <button
                  onClick={() => setShowRazorpayModal(false)}
                  className="w-full py-2.5 text-xs text-ssk-text-secondary hover:text-black font-semibold transition-colors"
                >
                  Cancel Transaction
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageTransition>
  );
};
