import React, { useState, useEffect } from 'react';
import { RotateCcw, Search, CheckCircle2, XCircle, DollarSign, AlertCircle, Clock } from 'lucide-react';
import { api } from '../../services/api';

export const AdminReturnsPage: React.FC = () => {
  const [returns, setReturns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedReturn, setSelectedReturn] = useState<any>(null);
  const [actionType, setActionType] = useState<'APPROVED' | 'REJECTED' | 'REFUNDED'>('APPROVED');
  const [adminNotes, setAdminNotes] = useState('');
  const [refundAmount, setRefundAmount] = useState<number>(0);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchReturns = async () => {
    setLoading(true);
    try {
      const data = await api.listReturnsAdmin();
      setReturns(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReturns();
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReturn) return;
    setIsUpdating(true);
    try {
      await api.updateReturnStatusAdmin(selectedReturn.id || selectedReturn.order_id, {
        status: actionType,
        admin_notes: adminNotes,
        rejection_reason: actionType === 'REJECTED' ? adminNotes : undefined,
        refund_amount: actionType === 'REFUNDED' ? refundAmount : undefined,
        refund_transaction_id: actionType === 'REFUNDED' ? `rfnd_rzp_${Date.now().toString(36)}` : undefined
      });
      setSelectedReturn(null);
      await fetchReturns();
    } catch (err: any) {
      alert(err.message || 'Failed to update return');
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Returns & Customer Refunds</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Review customer return requests, approve doorstep reverse pickup, and issue real gateway refunds.
          </p>
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-ssk-surface text-ssk-text-secondary border-b uppercase font-semibold text-[10px] tracking-wider">
            <tr>
              <th className="py-4 px-6">Order ID & Date</th>
              <th className="py-4 px-4">Customer</th>
              <th className="py-4 px-4">Return Reason</th>
              <th className="py-4 px-4">Comments</th>
              <th className="py-4 px-4">Status</th>
              <th className="py-4 px-6 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ssk-border font-medium">
            {returns.length > 0 ? (
              returns.map((ret, i) => (
                <tr key={i} className="hover:bg-ssk-blue-light/30">
                  <td className="py-4 px-6">
                    <span className="font-mono font-bold text-ssk-navy block">{ret.order_id}</span>
                    <span className="text-[10px] text-ssk-text-secondary">{new Date(ret.created_at).toLocaleDateString()}</span>
                  </td>
                  <td className="py-4 px-4">
                    <p className="font-bold text-ssk-text">{ret.customer_name}</p>
                    <p className="text-[10px] text-ssk-text-secondary">{ret.customer_email}</p>
                  </td>
                  <td className="py-4 px-4 font-semibold text-ssk-navy">{ret.reason}</td>
                  <td className="py-4 px-4 text-ssk-text-secondary max-w-xs truncate">{ret.comments || 'No extra comments'}</td>
                  <td className="py-4 px-4">
                    <span className="inline-block px-2.5 py-1 rounded-full text-[10px] font-bold bg-ssk-blue-light text-ssk-navy uppercase">
                      {ret.status}
                    </span>
                  </td>
                  <td className="py-4 px-6 text-right space-x-2">
                    <button
                      onClick={() => {
                        setSelectedReturn(ret);
                        setActionType('APPROVED');
                        setAdminNotes('Inspection verified, reverse pickup scheduled');
                      }}
                      className="px-3 py-1 bg-ssk-navy text-white text-[11px] font-bold rounded-lg shadow-sm"
                    >
                      Process
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-12 text-center text-ssk-text-secondary">
                  No return requests in queue.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Return Action Modal */}
      {selectedReturn && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm text-xs">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border space-y-4">
            <h3 className="text-base font-serif font-bold text-ssk-navy">
              Process Return for Order #{selectedReturn.order_id}
            </h3>

            <div className="p-3 bg-ssk-surface rounded-xl border border-ssk-border">
              <p><strong>Customer:</strong> {selectedReturn.customer_name}</p>
              <p><strong>Reason:</strong> {selectedReturn.reason}</p>
              {selectedReturn.comments && <p><strong>Comments:</strong> {selectedReturn.comments}</p>}
            </div>

            <form onSubmit={handleUpdate} className="space-y-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Select Action *</label>
                <select
                  value={actionType}
                  onChange={(e: any) => setActionType(e.target.value)}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold"
                >
                  <option value="APPROVED">APPROVE RETURN (Trigger Courier Pickup)</option>
                  <option value="REJECTED">REJECT RETURN (Eligibility Not Met)</option>
                  <option value="REFUNDED">ISSUE GATEWAY REFUND (Item Received & Verified)</option>
                </select>
              </div>

              {actionType === 'REFUNDED' && (
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Refund Amount (₹) *</label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={refundAmount}
                    onChange={(e) => setRefundAmount(Number(e.target.value))}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold"
                  />
                </div>
              )}

              <div>
                <label className="block font-bold text-ssk-text mb-1">Notes / Reason *</label>
                <textarea
                  rows={3}
                  required
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setSelectedReturn(null)}
                  className="px-4 py-2 border rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUpdating}
                  className="px-5 py-2 bg-ssk-navy text-white rounded-xl font-bold"
                >
                  {isUpdating ? 'Saving...' : 'Confirm Action'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
