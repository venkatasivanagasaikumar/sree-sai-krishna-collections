import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Package, Search, Printer, Truck, CheckCircle2, Clock,
  AlertCircle, ChevronRight, X, ExternalLink, ArrowRight, Loader2,
  FileText, Send
} from 'lucide-react';
import { api } from '../../services/api';
import { Order } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { modalOverlay, modalContent } from '../../animations';

export const AdminOrdersPage: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusTab, setStatusTab] = useState<string>('ALL');
  const [searchTerm, setSearchTerm] = useState('');

  // Status Update Modal
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [nextStatus, setNextStatus] = useState<string>('PACKED');
  const [carrierName, setCarrierName] = useState('Delhivery Express');
  const [trackingNumber, setTrackingNumber] = useState('');
  const [internalNotes, setInternalNotes] = useState('');
  const [isUpdating, setIsUpdating] = useState(false);

  // Packing slip modal
  const [slipData, setSlipData] = useState<any>(null);
  const [showSlipModal, setShowSlipModal] = useState(false);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await api.listOrdersAdmin({
        order_status: statusTab !== 'ALL' ? statusTab : undefined,
        search: searchTerm || undefined,
        limit: 50
      });
      setOrders(res.orders);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, [statusTab, searchTerm]);

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedOrder) return;
    setIsUpdating(true);
    try {
      await api.updateOrderStatusAdmin(selectedOrder.order_id, {
        status: nextStatus,
        carrier_name: nextStatus === 'SHIPPED' ? carrierName : undefined,
        tracking_number: nextStatus === 'SHIPPED' ? trackingNumber : undefined,
        internal_notes: internalNotes || undefined
      });
      setSelectedOrder(null);
      await fetchOrders();
    } catch (err: any) {
      alert(err.message || 'Failed to update order status');
    } finally {
      setIsUpdating(false);
    }
  };

  const openSlip = async (orderId: string) => {
    try {
      const data = await api.getPackingSlip(orderId);
      setSlipData(data);
      setShowSlipModal(true);
    } catch (e) {
      alert('Could not fetch slip');
    }
  };

  const handleDownloadInvoicePdf = async (orderId: string) => {
    try {
      await api.downloadInvoice(orderId, `SSK-INVOICE-${orderId}.pdf`);
    } catch (e: any) {
      alert(e.message || 'Could not download invoice PDF');
    }
  };

  const handleResendInvoice = async (orderId: string) => {
    if (!confirm(`Resend invoice & WhatsApp notification for order #${orderId}?`)) return;
    try {
      await api.resendInvoice(orderId, 'all');
      alert(`Invoice notification resent for order #${orderId}`);
    } catch (e: any) {
      alert(e.message || 'Could not resend invoice');
    }
  };

  const tabs = [
    { key: 'ALL', label: 'All Orders' },
    { key: 'ORDER_PLACED', label: 'Pending Payment / New' },
    { key: 'PROCESSING', label: 'Ready to Pack / Processing' },
    { key: 'SHIPPED', label: 'Dispatched / In Transit' },
    { key: 'DELIVERED', label: 'Delivered' },
    { key: 'CANCELLED', label: 'Cancelled' }
  ];

  return (
    <PageTransition className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Orders & Fulfilment Workflow</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Meesho-inspired seller order management: Pack, assign AWB logistics, dispatch & generate invoices.
          </p>
        </div>
      </div>

      {/* Tabs Bar */}
      <div className="flex gap-2 border-b border-ssk-border overflow-x-auto pb-1 text-xs">
        {tabs.map((tab) => (
          <motion.button
            key={tab.key}
            whileTap={{ scale: 0.95 }}
            onClick={() => setStatusTab(tab.key)}
            className={`px-4 py-2.5 font-bold rounded-xl whitespace-nowrap transition-all ${
              statusTab === tab.key
                ? 'bg-ssk-navy text-white shadow-sm'
                : 'text-ssk-text-secondary hover:text-ssk-navy hover:bg-ssk-blue-light'
            }`}
          >
            {tab.label}
          </motion.button>
        ))}
      </div>

      {/* Search Input */}
      <div className="bg-white p-4 rounded-2xl border border-ssk-border shadow-sm flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <input
            type="text"
            placeholder="Search Order ID, customer name, phone, or tracking..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
          />
          <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-2.5" />
        </div>
      </div>

      {/* Orders Table */}
      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-ssk-surface text-ssk-text-secondary border-b border-ssk-border uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-4 px-6">Order ID & Date</th>
                <th className="py-4 px-4">Customer</th>
                <th className="py-4 px-4">Items</th>
                <th className="py-4 px-4">Payment</th>
                <th className="py-4 px-4">Amount</th>
                <th className="py-4 px-4">Fulfilment Status</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ssk-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ssk-text-secondary">Loading orders...</td>
                </tr>
              ) : orders.length > 0 ? (
                orders.map((order) => (
                  <tr key={order.order_id} className="hover:bg-ssk-blue-light/30 transition-colors">
                    <td className="py-4 px-6">
                      <span className="font-mono font-bold text-ssk-navy block">{order.order_id}</span>
                      <span className="text-[10px] text-ssk-text-secondary">
                        {new Date(order.created_at).toLocaleString()}
                      </span>
                    </td>
                    <td className="py-4 px-4">
                      <p className="font-bold text-ssk-text">{order.customer_name}</p>
                      <p className="text-[11px] text-ssk-text-secondary">{order.customer_phone}</p>
                      <p className="text-[10px] text-ssk-text-secondary truncate max-w-[160px]">{order.shipping_address.city}, {order.shipping_address.state}</p>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold block">{order.items.length} item(s)</span>
                      <span className="text-[10px] text-ssk-text-secondary line-clamp-1">{order.items[0]?.name}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-semibold block">{order.payment_method}</span>
                      <span className="text-[10px] font-bold uppercase text-ssk-success">{order.payment_status}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="font-bold text-ssk-navy text-sm font-serif">₹{order.final_amount}</span>
                    </td>
                    <td className="py-4 px-4">
                      <span className="inline-block px-2.5 py-1 rounded-full text-[10px] font-bold bg-ssk-blue-light text-ssk-navy uppercase">
                        {order.order_status}
                      </span>
                      {order.tracking_number && (
                        <span className="block font-mono text-[9px] text-ssk-text-secondary mt-0.5">
                          AWB: {order.tracking_number}
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right space-x-1.5 whitespace-nowrap">
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleDownloadInvoicePdf(order.order_id)}
                        className="px-2 py-1 border border-ssk-navy/30 bg-ssk-blue-light/50 hover:bg-ssk-blue-light rounded-lg text-ssk-navy text-[11px] font-semibold transition-colors inline-flex items-center gap-1"
                        title="Download GST Tax Invoice (PDF)"
                      >
                        <FileText className="w-3 h-3 text-ssk-gold-dark" />
                        <span>Invoice</span>
                      </motion.button>
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => handleResendInvoice(order.order_id)}
                        className="p-1 border border-ssk-border hover:bg-ssk-surface rounded-lg text-ssk-navy text-[11px] font-semibold transition-colors inline-flex items-center"
                        title="Resend WhatsApp & Email Notifications"
                      >
                        <Send className="w-3 h-3 text-emerald-600" />
                      </motion.button>
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => openSlip(order.order_id)}
                        className="px-2 py-1 border border-ssk-border hover:bg-ssk-blue-light rounded-lg text-ssk-navy text-[11px] font-semibold transition-colors"
                        title="Print Packing Slip"
                      >
                        Slip
                      </motion.button>
                      <motion.button
                        whileTap={{ scale: 0.95 }}
                        onClick={() => {
                          setSelectedOrder(order);
                          setNextStatus(order.order_status === 'ORDER_PLACED' ? 'PACKED' : order.order_status === 'PACKED' ? 'SHIPPED' : 'DELIVERED');
                          setTrackingNumber(order.tracking_number || `DEL-${Date.now().toString().slice(-8)}`);
                        }}
                        className="px-2.5 py-1 bg-ssk-navy hover:bg-ssk-navy-dark text-white rounded-lg text-[11px] font-bold shadow-sm transition-colors"
                      >
                        Update
                      </motion.button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-ssk-text-secondary">No orders found in this tab.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Order Status Update Modal with AnimatePresence */}
      <AnimatePresence>
        {selectedOrder && (
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
              <div className="flex items-center justify-between border-b border-ssk-border pb-3">
                <h3 className="text-sm font-serif font-bold text-ssk-navy">
                  Update Order #{selectedOrder.order_id}
                </h3>
                <button onClick={() => setSelectedOrder(null)} aria-label="Close modal">
                  <X className="w-5 h-5 text-ssk-text-secondary" />
                </button>
              </div>

              <form onSubmit={handleUpdateStatus} className="space-y-4 text-xs">
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Select Next Status *</label>
                  <select
                    value={nextStatus}
                    onChange={(e) => setNextStatus(e.target.value)}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold text-ssk-navy"
                  >
                    <option value="PROCESSING">PROCESSING (Verification Confirmed)</option>
                    <option value="PACKED">PACKED (Quality Inspected & Sealed)</option>
                    <option value="SHIPPED">SHIPPED (Handed Over to Courier)</option>
                    <option value="DELIVERED">DELIVERED (Customer Delivery Complete)</option>
                    <option value="CANCELLED">CANCELLED (Restock items)</option>
                  </select>
                </div>

                {nextStatus === 'SHIPPED' && (
                  <div className="space-y-3 p-3 bg-ssk-blue-light/50 rounded-xl border border-ssk-border">
                    <div>
                      <label className="block font-bold text-ssk-text mb-1">Courier Carrier</label>
                      <select
                        value={carrierName}
                        onChange={(e) => setCarrierName(e.target.value)}
                        className="w-full px-3 py-2 bg-white border border-ssk-border rounded-xl"
                      >
                        <option value="Delhivery Express">Delhivery Express</option>
                        <option value="BlueDart Air">BlueDart Air</option>
                        <option value="DTDC Surface">DTDC Surface</option>
                        <option value="Xpressbees Logistics">Xpressbees Logistics</option>
                      </select>
                    </div>
                    <div>
                      <label className="block font-bold text-ssk-text mb-1">AWB / Airway Bill Tracking # *</label>
                      <input
                        type="text"
                        required
                        value={trackingNumber}
                        onChange={(e) => setTrackingNumber(e.target.value)}
                        placeholder="e.g. DEL-99281726"
                        className="w-full px-3 py-2 bg-white border border-ssk-border rounded-xl font-mono"
                      />
                    </div>
                  </div>
                )}

                <div>
                  <label className="block font-bold text-ssk-text mb-1">Internal Note (Recorded in Audit Timeline)</label>
                  <input
                    type="text"
                    value={internalNotes}
                    onChange={(e) => setInternalNotes(e.target.value)}
                    placeholder="e.g. Inspected anti-tarnish coating before packaging"
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  />
                </div>

                <div className="flex justify-end gap-2 pt-2 border-t border-ssk-border">
                  <button
                    type="button"
                    onClick={() => setSelectedOrder(null)}
                    className="px-4 py-2 border border-ssk-border rounded-xl font-semibold"
                  >
                    Cancel
                  </button>
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    type="submit"
                    disabled={isUpdating}
                    className="px-5 py-2 bg-ssk-navy text-white rounded-xl font-bold shadow-md hover:bg-ssk-navy-dark transition-colors flex items-center gap-1.5"
                  >
                    {isUpdating ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                        <span>Saving...</span>
                      </>
                    ) : (
                      <span>Confirm Update</span>
                    )}
                  </motion.button>
                </div>
              </form>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Slip Modal with AnimatePresence */}
      <AnimatePresence>
        {showSlipModal && slipData && (
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
              className="bg-white rounded-3xl max-w-2xl w-full p-8 shadow-2xl border border-ssk-border space-y-6 max-h-[90vh] overflow-y-auto text-xs"
            >
              <div className="flex justify-between border-b pb-4">
                <div>
                  <h3 className="text-base font-bold text-ssk-navy">{slipData.brand_name}</h3>
                  <p className="text-ssk-text-secondary">{slipData.business_address}</p>
                  <p className="text-ssk-text-secondary">Phone: {slipData.support_phone}</p>
                </div>
                <div className="text-right">
                  <span className="font-bold text-ssk-gold uppercase block">Seller Packing Slip</span>
                  <span className="font-mono font-bold">#{slipData.order.order_id}</span>
                </div>
              </div>

              <div>
                <p className="font-bold">Ship To: {slipData.order.shipping_address.name}</p>
                <p className="text-ssk-text-secondary">{slipData.order.shipping_address.address_line1}, {slipData.order.shipping_address.city} - {slipData.order.shipping_address.pincode}</p>
                <p className="text-ssk-text-secondary">Contact: {slipData.order.shipping_address.phone}</p>
              </div>

              <table className="w-full border-collapse border border-ssk-border">
                <thead>
                  <tr className="bg-ssk-surface border-b">
                    <th className="p-2 text-left">SKU</th>
                    <th className="p-2 text-left">Item Name</th>
                    <th className="p-2 text-center">Qty</th>
                    <th className="p-2 text-right">Price</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {slipData.order.items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td className="p-2 font-mono">{it.sku}</td>
                      <td className="p-2 font-semibold">{it.name}</td>
                      <td className="p-2 text-center font-bold">{it.quantity}</td>
                      <td className="p-2 text-right">₹{it.total_price}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              <div className="flex justify-end gap-2 pt-2">
                <motion.button
                  whileTap={{ scale: 0.95 }}
                  onClick={() => window.print()}
                  className="px-4 py-2 bg-ssk-navy text-white rounded-xl font-bold flex items-center gap-1.5"
                >
                  <Printer className="w-4 h-4" />
                  <span>Print Packing Slip</span>
                </motion.button>
                <button
                  onClick={() => setShowSlipModal(false)}
                  className="px-4 py-2 border rounded-xl hover:bg-gray-100 transition-colors"
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
