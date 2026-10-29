import React, { useState, useEffect } from 'react';
import { Layers, Search, AlertTriangle, ArrowUpDown, History, Plus, X, Check } from 'lucide-react';
import { api } from '../../services/api';
import { Product, InventoryMovement } from '../../types';

export const AdminInventoryPage: React.FC = () => {
  const [items, setItems] = useState<Product[]>([]);
  const [movements, setMovements] = useState<InventoryMovement[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [lowStockOnly, setLowStockOnly] = useState(false);
  const [activeTab, setActiveTab] = useState<'stock' | 'movements'>('stock');

  // Adjustment Modal
  const [adjustItem, setAdjustItem] = useState<Product | null>(null);
  const [adjustType, setAdjustType] = useState('RESTOCK');
  const [qtyChange, setQtyChange] = useState(10);
  const [reason, setReason] = useState('Restock shipment from factory');
  const [isAdjusting, setIsAdjusting] = useState(false);

  const fetchInventory = async () => {
    setLoading(true);
    try {
      const [res, movs] = await Promise.all([
        api.getInventory({ search: searchTerm, low_stock_only: lowStockOnly }),
        api.getMovements()
      ]);
      setItems(res.items);
      setMovements(movs);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventory();
  }, [searchTerm, lowStockOnly]);

  const handleAdjustStock = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!adjustItem) return;
    setIsAdjusting(true);
    try {
      const change = adjustType === 'DAMAGED' || adjustType === 'AUDIT_CORRECTION' && qtyChange < 0
        ? -Math.abs(qtyChange)
        : Math.abs(qtyChange);

      await api.adjustStock({
        product_id: adjustItem.id,
        sku: adjustItem.sku,
        adjustment_type: adjustType,
        quantity_change: change,
        reason: reason
      });
      setAdjustItem(null);
      await fetchInventory();
    } catch (err: any) {
      alert(err.message || 'Failed to adjust stock');
    } finally {
      setIsAdjusting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Inventory & Stock Adjustments</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Auditable stock management: Prevent overselling, track damage allowances, and log restocks.
          </p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('stock')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              activeTab === 'stock' ? 'bg-ssk-navy text-white shadow-sm' : 'border border-ssk-border hover:bg-ssk-blue-light'
            }`}
          >
            SKU Stock Levels
          </button>
          <button
            onClick={() => setActiveTab('movements')}
            className={`px-4 py-2 text-xs font-bold rounded-xl transition-all ${
              activeTab === 'movements' ? 'bg-ssk-navy text-white shadow-sm' : 'border border-ssk-border hover:bg-ssk-blue-light'
            }`}
          >
            Movement Audit History
          </button>
        </div>
      </div>

      {activeTab === 'stock' ? (
        <>
          {/* Controls */}
          <div className="bg-white p-4 rounded-2xl border border-ssk-border shadow-sm flex flex-col sm:flex-row gap-4 items-center justify-between">
            <div className="relative w-full sm:w-80">
              <input
                type="text"
                placeholder="Search SKU or name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
              />
              <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-2.5" />
            </div>

            <label className="flex items-center gap-2 text-xs text-ssk-text cursor-pointer">
              <input
                type="checkbox"
                checked={lowStockOnly}
                onChange={(e) => setLowStockOnly(e.target.checked)}
                className="accent-ssk-navy rounded"
              />
              <span className="font-semibold text-amber-800">Show Low-Stock Only (&le; 5 units)</span>
            </label>
          </div>

          {/* Inventory Table */}
          <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
            <table className="w-full text-xs text-left">
              <thead className="bg-ssk-surface text-ssk-text-secondary border-b border-ssk-border uppercase font-semibold text-[10px] tracking-wider">
                <tr>
                  <th className="py-4 px-6">SKU</th>
                  <th className="py-4 px-4">Design Name</th>
                  <th className="py-4 px-4">Category</th>
                  <th className="py-4 px-4">Available Stock</th>
                  <th className="py-4 px-4">Status Indicator</th>
                  <th className="py-4 px-6 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-ssk-border font-medium">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-ssk-blue-light/30 transition-colors">
                    <td className="py-4 px-6 font-mono font-bold text-ssk-navy">{item.sku}</td>
                    <td className="py-4 px-4 font-bold text-ssk-text max-w-xs truncate">{item.name}</td>
                    <td className="py-4 px-4 text-ssk-text-secondary">{item.category}</td>
                    <td className="py-4 px-4">
                      <span className="text-base font-bold font-serif text-ssk-navy">{item.stock}</span>
                      <span className="text-[10px] text-ssk-text-secondary ml-1">units</span>
                    </td>
                    <td className="py-4 px-4">
                      {item.stock <= 5 ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-100 text-amber-800">
                          <AlertTriangle className="w-3 h-3" />
                          Low Stock Alert
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[10px] font-bold bg-green-100 text-green-800">
                          <Check className="w-3 h-3" />
                          Optimal Level
                        </span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => {
                          setAdjustItem(item);
                          setQtyChange(10);
                          setAdjustType('RESTOCK');
                          setReason('Supplier restock batch received');
                        }}
                        className="px-3 py-1.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white rounded-xl text-[11px] font-bold shadow-sm"
                      >
                        Adjust Stock
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        /* Movements Table */
        <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
          <table className="w-full text-xs text-left">
            <thead className="bg-ssk-surface text-ssk-text-secondary border-b border-ssk-border uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-4 px-6">Timestamp</th>
                <th className="py-4 px-4">SKU</th>
                <th className="py-4 px-4">Product Name</th>
                <th className="py-4 px-4">Change</th>
                <th className="py-4 px-4">New Stock</th>
                <th className="py-4 px-4">Type</th>
                <th className="py-4 px-6">Reason / Authorized By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ssk-border font-medium">
              {movements.map((m, i) => (
                <tr key={i} className="hover:bg-ssk-blue-light/30">
                  <td className="py-3 px-6 text-[11px] text-ssk-text-secondary">
                    {new Date(m.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-ssk-navy">{m.sku}</td>
                  <td className="py-3 px-4 truncate max-w-xs">{m.product_name}</td>
                  <td className="py-3 px-4 font-bold">
                    <span className={m.quantity_change > 0 ? 'text-green-600' : 'text-red-600'}>
                      {m.quantity_change > 0 ? `+${m.quantity_change}` : m.quantity_change}
                    </span>
                  </td>
                  <td className="py-3 px-4 font-bold">{m.new_stock}</td>
                  <td className="py-3 px-4">
                    <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-ssk-blue-light text-ssk-navy uppercase">
                      {m.adjustment_type}
                    </span>
                  </td>
                  <td className="py-3 px-6">
                    <p className="font-semibold text-ssk-text">{m.reason}</p>
                    <span className="text-[10px] text-ssk-text-secondary">By: {m.performed_by}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Adjust Stock Modal */}
      {adjustItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border space-y-4 text-xs">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-sm font-serif font-bold text-ssk-navy">Adjust Stock: {adjustItem.sku}</h3>
              <button onClick={() => setAdjustItem(null)}><X className="w-5 h-5 text-ssk-text-secondary" /></button>
            </div>

            <form onSubmit={handleAdjustStock} className="space-y-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Adjustment Type *</label>
                <select
                  value={adjustType}
                  onChange={(e) => setAdjustType(e.target.value)}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold"
                >
                  <option value="RESTOCK">RESTOCK (Warehouse Intake / New Units)</option>
                  <option value="DAMAGED">DAMAGED (Scrap / Defective / Return Damaged)</option>
                  <option value="AUDIT_CORRECTION">AUDIT_CORRECTION (Physical Count Discrepancy)</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-ssk-text mb-1">Quantity *</label>
                <input
                  type="number"
                  required
                  min={1}
                  value={qtyChange}
                  onChange={(e) => setQtyChange(Number(e.target.value))}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold text-base"
                />
              </div>

              <div>
                <label className="block font-bold text-ssk-text mb-1">Mandatory Audit Reason *</label>
                <input
                  type="text"
                  required
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Factory shipment batch invoice #889"
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t">
                <button
                  type="button"
                  onClick={() => setAdjustItem(null)}
                  className="px-4 py-2 border rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isAdjusting}
                  className="px-5 py-2 bg-ssk-navy text-white font-bold rounded-xl"
                >
                  {isAdjusting ? 'Recording...' : 'Commit Stock Adjustment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
