import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { CheckCircle2, Package, ArrowRight, Printer, Clock, Truck, ShieldCheck } from 'lucide-react';
import { api } from '../../services/api';
import { Order } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { FadeIn } from '../../components/animations/FadeIn';

export const OrderSuccessPage: React.FC = () => {
  const { orderId } = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (orderId) {
      api.getOrderById(orderId)
        .then(setOrder)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [orderId]);

  return (
    <PageTransition className="max-w-3xl mx-auto px-4 py-16 text-center space-y-8">
      {/* Success Badge with Spring Entrance */}
      <motion.div
        initial={{ scale: 0.3, opacity: 0 }}
        animate={{ scale: [0.3, 1.15, 1], opacity: 1 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="w-20 h-20 bg-green-50 text-ssk-success rounded-full flex items-center justify-center mx-auto border-4 border-green-100 shadow-md"
      >
        <CheckCircle2 className="w-10 h-10" />
      </motion.div>

      <div className="space-y-2">
        <span className="text-xs font-bold text-ssk-gold uppercase tracking-widest px-3 py-1 bg-ssk-gold/10 rounded-full">
          Order Confirmed
        </span>
        <h1 className="text-3xl font-serif font-bold text-ssk-navy">
          Thank you for choosing SSK Collections!
        </h1>
        <p className="text-xs sm:text-sm text-ssk-text-secondary max-w-md mx-auto">
          We have received your order <strong className="text-ssk-navy">{orderId}</strong>. A confirmation has been logged and sent to your email.
        </p>
      </div>

      {order && (
        <FadeIn direction="up" delay={0.2} className="bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border text-left shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-ssk-border">
            <div>
              <span className="text-xs text-ssk-text-secondary">Order ID</span>
              <p className="text-base font-bold text-ssk-navy font-mono">{order.order_id}</p>
            </div>
            <div>
              <span className="text-xs text-ssk-text-secondary">Payment Status</span>
              <p className="text-xs font-bold text-ssk-success uppercase">{order.payment_status}</p>
            </div>
            <div>
              <span className="text-xs text-ssk-text-secondary">Total Amount</span>
              <p className="text-base font-bold text-ssk-navy font-serif">₹{order.final_amount.toLocaleString('en-IN')}</p>
            </div>
          </div>

          {/* Delivery Details */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 text-xs">
            <div>
              <span className="text-[10px] font-bold text-ssk-text-secondary uppercase">Shipping To</span>
              <p className="font-bold text-ssk-text mt-1">{order.shipping_address.name}</p>
              <p className="text-ssk-text-secondary">{order.shipping_address.address_line1}</p>
              {order.shipping_address.address_line2 && <p className="text-ssk-text-secondary">{order.shipping_address.address_line2}</p>}
              <p className="text-ssk-text-secondary">{order.shipping_address.city}, {order.shipping_address.state} - {order.shipping_address.pincode}</p>
              <p className="text-ssk-text-secondary mt-1">Phone: {order.shipping_address.phone}</p>
            </div>

            <div>
              <span className="text-[10px] font-bold text-ssk-text-secondary uppercase">Estimated Delivery</span>
              <p className="font-bold text-ssk-navy mt-1 flex items-center gap-1.5">
                <Truck className="w-4 h-4 text-ssk-gold" />
                <span>2-4 Business Days</span>
              </p>
              <p className="text-ssk-text-secondary mt-1">
                Carrier details and AWB tracking code will be updated once our inspection team packs your jewellery.
              </p>
            </div>
          </div>

          {/* Items Summary */}
          <div className="space-y-3 pt-4 border-t border-ssk-border">
            <span className="text-[10px] font-bold text-ssk-text-secondary uppercase">Items Ordered</span>
            <div className="space-y-2">
              {order.items.map((item, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3">
                    <img src={item.image || '/logo.svg'} alt={item.name} className="w-10 h-10 object-cover rounded-lg border border-ssk-border" />
                    <div>
                      <p className="font-semibold text-ssk-text">{item.name}</p>
                      <span className="text-ssk-text-secondary text-[10px]">Qty: {item.quantity} &bull; SKU: {item.sku}</span>
                    </div>
                  </div>
                  <span className="font-bold text-ssk-navy">₹{item.total_price}</span>
                </div>
              ))}
            </div>
          </div>
        </FadeIn>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-4">
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
          <Link
            to={`/account/orders/${orderId}`}
            className="px-6 py-3 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl shadow-md flex items-center gap-2 transition-colors"
          >
            <Package className="w-4 h-4" />
            <span>Track Order Timeline</span>
          </Link>
        </motion.div>
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
          <Link
            to="/shop"
            className="px-6 py-3 border border-ssk-border text-ssk-text hover:bg-ssk-blue-light text-xs font-semibold rounded-xl transition-colors inline-block"
          >
            Continue Shopping
          </Link>
        </motion.div>
      </div>
    </PageTransition>
  );
};
