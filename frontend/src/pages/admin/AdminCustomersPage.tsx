import React, { useState, useEffect } from 'react';
import { Users, Search, ShoppingBag, Mail, Phone, Calendar } from 'lucide-react';
import { api } from '../../services/api';
import { CustomerSummary } from '../../types';

export const AdminCustomersPage: React.FC = () => {
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await api.listCustomersAdmin({ search: searchTerm });
      setCustomers(res.customers);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, [searchTerm]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Customer Directory</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            View customer order volumes, total lifetime spend, and address records.
          </p>
        </div>
      </div>

      <div className="bg-white p-4 rounded-2xl border border-ssk-border shadow-sm">
        <div className="relative max-w-md">
          <input
            type="text"
            placeholder="Search customer name, email, or phone..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
          />
          <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-2.5" />
        </div>
      </div>

      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-ssk-surface text-ssk-text-secondary border-b uppercase font-semibold text-[10px] tracking-wider">
            <tr>
              <th className="py-4 px-6">Customer Name</th>
              <th className="py-4 px-4">Contact Details</th>
              <th className="py-4 px-4">Saved Addresses</th>
              <th className="py-4 px-4">Orders Placed</th>
              <th className="py-4 px-4">Lifetime Spend</th>
              <th className="py-4 px-6 text-right">Registered</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ssk-border font-medium">
            {customers.map((c) => (
              <tr key={c.id} className="hover:bg-ssk-blue-light/30">
                <td className="py-4 px-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-ssk-navy text-white flex items-center justify-center font-bold text-xs">
                      {c.full_name?.charAt(0).toUpperCase()}
                    </div>
                    <span className="font-bold text-ssk-text">{c.full_name}</span>
                  </div>
                </td>
                <td className="py-4 px-4">
                  <p className="text-ssk-text flex items-center gap-1.5"><Mail className="w-3 h-3 text-ssk-text-secondary" /> {c.email}</p>
                  {c.phone && <p className="text-ssk-text-secondary flex items-center gap-1.5"><Phone className="w-3 h-3 text-ssk-text-secondary" /> {c.phone}</p>}
                </td>
                <td className="py-4 px-4 font-semibold">{c.addresses_count} address(es)</td>
                <td className="py-4 px-4 font-bold text-ssk-navy">{c.total_orders} orders</td>
                <td className="py-4 px-4 font-bold text-ssk-navy font-serif">₹{c.total_spent.toLocaleString('en-IN')}</td>
                <td className="py-4 px-6 text-right text-ssk-text-secondary">
                  {new Date(c.created_at).toLocaleDateString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
