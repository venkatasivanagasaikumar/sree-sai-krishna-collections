import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  TrendingUp, Package, ShoppingCart, Clock, CheckCircle2,
  AlertTriangle, DollarSign, Layers, ArrowUpRight, ArrowRight,
  Sparkles, RefreshCw
} from 'lucide-react';
import { api } from '../../services/api';
import { DashboardKPIs } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { StaggerContainer } from '../../components/animations/StaggerContainer';
import { AnimatedCounter } from '../../components/animations/AnimatedCounter';
import { fadeUp } from '../../animations';

export const AdminDashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardKPIs | null>(null);
  const [loading, setLoading] = useState(true);
  const [daysFilter, setDaysFilter] = useState(30);

  const fetchDashboard = async () => {
    setLoading(true);
    try {
      const res = await api.getDashboardAnalytics(daysFilter);
      setData(res);
    } catch (err) {
      console.error('Failed to load admin analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [daysFilter]);

  if (loading || !data) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded w-1/4 animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-2xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  const { kpis, sales_trend, top_selling_products, recent_orders, order_status_distribution } = data;

  return (
    <PageTransition className="space-y-8">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">Seller Overview</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Real-time sales, order fulfilment pipelines, and inventory movements.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={daysFilter}
            onChange={(e) => setDaysFilter(Number(e.target.value))}
            className="bg-white border border-ssk-border rounded-xl px-3 py-2 text-xs font-semibold text-ssk-navy focus:outline-none focus:border-ssk-gold shadow-sm transition-colors"
          >
            <option value={7}>Last 7 Days</option>
            <option value={30}>Last 30 Days</option>
            <option value={90}>Last 90 Days</option>
          </select>
          <motion.button
            whileTap={{ rotate: 180 }}
            transition={{ duration: 0.3 }}
            onClick={fetchDashboard}
            className="p-2 border border-ssk-border rounded-xl text-ssk-navy hover:bg-ssk-blue-light transition-colors"
            title="Refresh Data"
            aria-label="Refresh Data"
          >
            <RefreshCw className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Urgent Attention Alerts (Meesho style) */}
      {(kpis.orders_awaiting_processing > 0 || kpis.low_stock_products > 0 || kpis.return_requests > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {kpis.orders_awaiting_processing > 0 && (
            <motion.div whileHover={{ y: -2 }} className="p-4 bg-blue-50 border border-blue-200 rounded-2xl flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-blue-700" />
                <div>
                  <h4 className="text-xs font-bold text-blue-900">{kpis.orders_awaiting_processing} Orders Awaiting Packing</h4>
                  <p className="text-[11px] text-blue-700">Dispatch today to avoid SLA penalties</p>
                </div>
              </div>
              <Link to="/admin/orders" className="text-xs font-bold text-blue-800 hover:underline">
                View &rarr;
              </Link>
            </motion.div>
          )}

          {kpis.low_stock_products > 0 && (
            <motion.div whileHover={{ y: -2 }} className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <AlertTriangle className="w-5 h-5 text-amber-700" />
                <div>
                  <h4 className="text-xs font-bold text-amber-900">{kpis.low_stock_products} Low Stock Alert</h4>
                  <p className="text-[11px] text-amber-700">Stock &le; 5 units remaining</p>
                </div>
              </div>
              <Link to="/admin/inventory" className="text-xs font-bold text-amber-800 hover:underline">
                Restock &rarr;
              </Link>
            </motion.div>
          )}

          {kpis.return_requests > 0 && (
            <motion.div whileHover={{ y: -2 }} className="p-4 bg-rose-50 border border-rose-200 rounded-2xl flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-3">
                <Clock className="w-5 h-5 text-rose-700" />
                <div>
                  <h4 className="text-xs font-bold text-rose-900">{kpis.return_requests} Return Requests</h4>
                  <p className="text-[11px] text-rose-700">Review within 24 hours</p>
                </div>
              </div>
              <Link to="/admin/returns" className="text-xs font-bold text-rose-800 hover:underline">
                Review &rarr;
              </Link>
            </motion.div>
          )}
        </div>
      )}

      {/* Main KPI Cards Grid with Animated Counters and Stagger */}
      <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Net Sales */}
        <motion.div
          variants={fadeUp}
          whileHover={{ y: -4, boxShadow: '0 12px 24px rgba(18,63,122,0.08)' }}
          className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm flex flex-col justify-between space-y-3 transition-shadow"
        >
          <div className="flex items-center justify-between text-ssk-text-secondary">
            <span className="text-xs font-bold uppercase tracking-wider">Net Sales</span>
            <div className="w-9 h-9 rounded-xl bg-ssk-blue-light text-ssk-navy flex items-center justify-center">
              <TrendingUp className="w-5 h-5" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold font-serif text-ssk-navy">
              <AnimatedCounter value={kpis.net_sales} duration={1.5} prefix="₹" />
            </span>
            <p className="text-[11px] text-ssk-text-secondary mt-1">
              Gross: ₹{kpis.gross_sales} &bull; Disc: ₹{kpis.total_discounts}
            </p>
          </div>
        </motion.div>

        {/* Total Orders */}
        <motion.div
          variants={fadeUp}
          whileHover={{ y: -4, boxShadow: '0 12px 24px rgba(18,63,122,0.08)' }}
          className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm flex flex-col justify-between space-y-3 transition-shadow"
        >
          <div className="flex items-center justify-between text-ssk-text-secondary">
            <span className="text-xs font-bold uppercase tracking-wider">Total Orders</span>
            <div className="w-9 h-9 rounded-xl bg-ssk-gold/15 text-ssk-gold-dark flex items-center justify-center">
              <Package className="w-5 h-5" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold font-serif text-ssk-navy">
              <AnimatedCounter value={kpis.total_orders} duration={1.2} />
            </span>
            <p className="text-[11px] text-ssk-success font-semibold mt-1">
              {kpis.today_orders} orders received today
            </p>
          </div>
        </motion.div>

        {/* Delivered Orders */}
        <motion.div
          variants={fadeUp}
          whileHover={{ y: -4, boxShadow: '0 12px 24px rgba(18,63,122,0.08)' }}
          className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm flex flex-col justify-between space-y-3 transition-shadow"
        >
          <div className="flex items-center justify-between text-ssk-text-secondary">
            <span className="text-xs font-bold uppercase tracking-wider">Delivered</span>
            <div className="w-9 h-9 rounded-xl bg-green-50 text-ssk-success flex items-center justify-center">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold font-serif text-ssk-navy">
              <AnimatedCounter value={kpis.delivered_orders} duration={1.2} />
            </span>
            <p className="text-[11px] text-ssk-text-secondary mt-1">
              Successful customer deliveries
            </p>
          </div>
        </motion.div>

        {/* Active Catalog & Inventory */}
        <motion.div
          variants={fadeUp}
          whileHover={{ y: -4, boxShadow: '0 12px 24px rgba(18,63,122,0.08)' }}
          className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm flex flex-col justify-between space-y-3 transition-shadow"
        >
          <div className="flex items-center justify-between text-ssk-text-secondary">
            <span className="text-xs font-bold uppercase tracking-wider">Active Catalog</span>
            <div className="w-9 h-9 rounded-xl bg-purple-50 text-purple-700 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
          </div>
          <div>
            <span className="text-2xl font-bold font-serif text-ssk-navy">
              <AnimatedCounter value={kpis.active_products} duration={1} suffix=" SKUs" />
            </span>
            <p className="text-[11px] text-ssk-text-secondary mt-1">
              {kpis.low_stock_products} requiring re-order
            </p>
          </div>
        </motion.div>
      </StaggerContainer>

      {/* Visual Sales Trend Bar Chart with Animated Bars */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-ssk-border pb-4">
          <div>
            <h3 className="text-base font-serif font-bold text-ssk-navy">7-Day Sales Performance (INR)</h3>
            <p className="text-xs text-ssk-text-secondary">Calculated directly from captured orders and paid transactions</p>
          </div>
        </div>

        <div className="h-48 flex items-end justify-between gap-2 sm:gap-4 pt-6 px-2">
          {sales_trend.map((point, idx) => {
            const maxVal = Math.max(...sales_trend.map(p => p.sales), 1000);
            const heightPct = Math.max(10, Math.round((point.sales / maxVal) * 100));
            return (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2 group">
                <span className="text-[10px] font-bold text-ssk-navy opacity-0 group-hover:opacity-100 transition-opacity">
                  ₹{point.sales}
                </span>
                <div className="w-full max-w-[48px] bg-ssk-surface rounded-xl overflow-hidden h-36 flex items-end">
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPct}%` }}
                    transition={{ duration: 0.6, delay: idx * 0.08, ease: 'easeOut' }}
                    className="w-full bg-gradient-to-t from-ssk-navy to-ssk-gold rounded-xl group-hover:brightness-110"
                  />
                </div>
                <span className="text-[11px] font-medium text-ssk-text-secondary">{point.date}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Tables: Top Selling Products & Recent Orders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Top Selling Products */}
        <div className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-ssk-border pb-3">
            <h3 className="text-sm font-serif font-bold text-ssk-navy">Top Selling Products</h3>
            <Link to="/admin/products" className="text-xs font-semibold text-ssk-navy hover:underline">
              View Catalog
            </Link>
          </div>

          <div className="divide-y divide-ssk-border">
            {top_selling_products.map((p) => (
              <div key={p.id} className="py-3 flex items-center justify-between text-xs hover:bg-ssk-blue-light/30 px-2 rounded-xl transition-colors">
                <div className="space-y-0.5 max-w-[240px]">
                  <p className="font-semibold text-ssk-text truncate">{p.name}</p>
                  <p className="font-mono text-[10px] text-ssk-text-secondary">SKU: {p.sku}</p>
                </div>
                <div className="text-right">
                  <span className="font-bold text-ssk-navy block">₹{p.price}</span>
                  <span className="text-[10px] text-ssk-success font-semibold">{p.sales_count} units sold</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Orders */}
        <div className="bg-white p-6 rounded-3xl border border-ssk-border shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-ssk-border pb-3">
            <h3 className="text-sm font-serif font-bold text-ssk-navy">Recent Customer Orders</h3>
            <Link to="/admin/orders" className="text-xs font-semibold text-ssk-navy hover:underline">
              Manage All
            </Link>
          </div>

          <div className="divide-y divide-ssk-border">
            {recent_orders.map((o) => (
              <div key={o.order_id} className="py-3 flex items-center justify-between text-xs hover:bg-ssk-blue-light/30 px-2 rounded-xl transition-colors">
                <div className="space-y-0.5">
                  <Link to={`/admin/orders`} className="font-mono font-bold text-ssk-navy hover:underline block">
                    {o.order_id}
                  </Link>
                  <p className="text-ssk-text-secondary text-[11px]">{o.customer_name} &bull; {o.payment_method}</p>
                </div>
                <div className="text-right space-y-0.5">
                  <span className="font-bold text-ssk-navy block">₹{o.final_amount}</span>
                  <span className="inline-block px-2 py-0.5 text-[9px] font-bold bg-ssk-blue-light text-ssk-navy rounded-full uppercase">
                    {o.order_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PageTransition>
  );
};
