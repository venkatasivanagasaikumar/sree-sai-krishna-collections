import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare, Mail, RefreshCw, Send, CheckCircle2,
  AlertCircle, Clock, Search, Filter, Shield, Phone,
  FileText, Download, Check, ExternalLink, RotateCcw
} from 'lucide-react';
import { api } from '../../services/api';
import { PageTransition } from '../../components/animations/PageTransition';

interface CommStatus {
  email: {
    is_configured: boolean;
    smtp_host: string;
    smtp_port: number;
    from_email: string;
    from_name: string;
    mode: string;
    stats: Record<string, number>;
  };
  whatsapp: {
    is_configured: boolean;
    phone_number_id: string;
    business_account_id: string;
    mode: string;
    verified_templates: string[];
    stats: Record<string, number>;
  };
  system_time: string;
}

export const AdminCommunicationsPage: React.FC = () => {
  const [statusData, setStatusData] = useState<CommStatus | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [totalLogs, setTotalLogs] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  // Filters
  const [channelFilter, setChannelFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [orderSearch, setOrderSearch] = useState('');
  const [recipientSearch, setRecipientSearch] = useState('');

  // Test Modals / States
  const [testEmailAddr, setTestEmailAddr] = useState('');
  const [testPhone, setTestPhone] = useState('');
  const [testTemplate, setTestTemplate] = useState('order_placed');
  const [testingEmail, setTestingEmail] = useState(false);
  const [testingWhatsApp, setTestingWhatsApp] = useState(false);
  const [actionFeedback, setActionFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [retryingId, setRetryingId] = useState<string | null>(null);

  const loadStatusAndLogs = async () => {
    setLoading(true);
    try {
      const [statusRes, logsRes] = await Promise.all([
        api.getCommunicationsStatus(),
        api.getNotificationLogs({
          channel: channelFilter || undefined,
          status: statusFilter || undefined,
          order_id: orderSearch || undefined,
          recipient: recipientSearch || undefined,
          page,
          limit: 20
        })
      ]);
      setStatusData(statusRes);
      setLogs(logsRes.items || []);
      setTotalLogs(logsRes.total || 0);
    } catch (err: any) {
      console.error('Failed to load communication metrics:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadStatusAndLogs();
  }, [page, channelFilter, statusFilter]);

  const handleRefresh = () => {
    setRefreshing(true);
    loadStatusAndLogs();
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadStatusAndLogs();
  };

  const handleSendTestEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testEmailAddr) return;
    setTestingEmail(true);
    setActionFeedback(null);
    try {
      const res = await api.testEmail(testEmailAddr);
      setActionFeedback({
        type: 'success',
        message: `Test email dispatched! Status: ${res.status || 'Success'} (Mode: ${res.mode || 'dispatched'})`
      });
      loadStatusAndLogs();
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.message || 'Failed to dispatch test email' });
    } finally {
      setTestingEmail(false);
    }
  };

  const handleSendTestWhatsApp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!testPhone) return;
    setTestingWhatsApp(true);
    setActionFeedback(null);
    try {
      const res = await api.testWhatsApp(testPhone, testTemplate);
      setActionFeedback({
        type: 'success',
        message: `WhatsApp template '${testTemplate}' triggered! Status: ${res.status} (Recipient: ${res.recipient})`
      });
      loadStatusAndLogs();
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.message || 'Failed to dispatch test WhatsApp' });
    } finally {
      setTestingWhatsApp(false);
    }
  };

  const handleRetryNotification = async (notificationId: string) => {
    setRetryingId(notificationId);
    try {
      await api.retryNotification(notificationId);
      setActionFeedback({ type: 'success', message: 'Notification retry initiated successfully.' });
      loadStatusAndLogs();
    } catch (err: any) {
      setActionFeedback({ type: 'error', message: err.message || 'Retry failed' });
    } finally {
      setRetryingId(null);
    }
  };

  return (
    <PageTransition className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">
            Order Communications & Invoicing Hub
          </h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Real-time management for official WhatsApp Business notifications, transactional SMTP emails, and GST Tax Invoices.
          </p>
        </div>

        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="px-4 py-2 bg-white border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-sm transition-colors self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh Feeds</span>
        </button>
      </div>

      {actionFeedback && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className={`p-4 rounded-xl text-xs flex items-center justify-between gap-3 ${
            actionFeedback.type === 'success'
              ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
              : 'bg-red-50 border border-red-200 text-red-800'
          }`}
        >
          <div className="flex items-center gap-2">
            {actionFeedback.type === 'success' ? (
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-4 h-4 text-red-600 flex-shrink-0" />
            )}
            <span>{actionFeedback.message}</span>
          </div>
          <button
            onClick={() => setActionFeedback(null)}
            className="text-xs font-bold opacity-60 hover:opacity-100"
          >
            &times;
          </button>
        </motion.div>
      )}

      {/* Connectivity & Channel Health Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* WhatsApp Card */}
        <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ssk-border">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
                <MessageSquare className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-ssk-navy">WhatsApp Business Cloud API</h3>
                <span className="text-[10px] text-ssk-text-secondary">Official Meta Cloud API (v19.0)</span>
              </div>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                statusData?.whatsapp.is_configured
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {statusData?.whatsapp.is_configured ? 'Live API Active' : 'Simulation Mode'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-3 bg-ssk-surface rounded-xl">
              <span className="text-[10px] text-ssk-text-secondary uppercase">Phone Number ID</span>
              <p className="font-mono font-bold text-ssk-navy truncate">
                {statusData?.whatsapp.phone_number_id || 'Not Set'}
              </p>
            </div>
            <div className="p-3 bg-ssk-surface rounded-xl">
              <span className="text-[10px] text-ssk-text-secondary uppercase">Delivered Messages</span>
              <p className="font-bold text-emerald-700 text-sm">
                {(statusData?.whatsapp.stats.delivered || 0) + (statusData?.whatsapp.stats.sent || 0) + (statusData?.whatsapp.stats.simulated || 0)}
              </p>
            </div>
          </div>

          {/* WhatsApp Test Form */}
          <form onSubmit={handleSendTestWhatsApp} className="pt-2 space-y-2">
            <span className="text-[11px] font-bold text-ssk-navy uppercase tracking-wider block">
              Send Test Template
            </span>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="tel"
                placeholder="Mobile (e.g. 9848022338)"
                value={testPhone}
                onChange={(e) => setTestPhone(e.target.value)}
                className="px-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-mono focus:outline-none focus:border-ssk-navy flex-1"
              />
              <select
                value={testTemplate}
                onChange={(e) => setTestTemplate(e.target.value)}
                className="px-2 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none"
              >
                <option value="order_placed">order_placed</option>
                <option value="payment_confirmed">payment_confirmed</option>
                <option value="order_packed">order_packed</option>
                <option value="order_shipped">order_shipped</option>
                <option value="order_delivered">order_delivered</option>
              </select>
              <button
                type="submit"
                disabled={testingWhatsApp || !testPhone}
                className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl flex items-center justify-center gap-1 transition-colors disabled:opacity-50"
              >
                <Send className="w-3 h-3" />
                <span>Dispatch</span>
              </button>
            </div>
          </form>
        </div>

        {/* Email Card */}
        <div className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-ssk-border">
            <div className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-ssk-blue-light text-ssk-navy flex items-center justify-center">
                <Mail className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-ssk-navy">Transactional Email (SMTP)</h3>
                <span className="text-[10px] text-ssk-text-secondary">Official Invoices & PDF Attachments</span>
              </div>
            </div>
            <span
              className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase ${
                statusData?.email.is_configured
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              {statusData?.email.is_configured ? 'Live SMTP Active' : 'Simulation Mode'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-3 bg-ssk-surface rounded-xl">
              <span className="text-[10px] text-ssk-text-secondary uppercase">From Address</span>
              <p className="font-mono font-bold text-ssk-navy truncate">
                {statusData?.email.from_email || 'Not Set'}
              </p>
            </div>
            <div className="p-3 bg-ssk-surface rounded-xl">
              <span className="text-[10px] text-ssk-text-secondary uppercase">Dispatched Emails</span>
              <p className="font-bold text-ssk-navy text-sm">
                {(statusData?.email.stats.sent || 0) + (statusData?.email.stats.delivered || 0) + (statusData?.email.stats.simulated || 0)}
              </p>
            </div>
          </div>

          {/* Email Test Form */}
          <form onSubmit={handleSendTestEmail} className="pt-2 space-y-2">
            <span className="text-[11px] font-bold text-ssk-navy uppercase tracking-wider block">
              Send Test Transactional Email
            </span>
            <div className="flex gap-2">
              <input
                type="email"
                placeholder="Recipient Email (e.g. customer@example.com)"
                value={testEmailAddr}
                onChange={(e) => setTestEmailAddr(e.target.value)}
                className="px-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-navy flex-1"
              />
              <button
                type="submit"
                disabled={testingEmail || !testEmailAddr}
                className="px-4 py-1.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl flex items-center gap-1 transition-colors disabled:opacity-50"
              >
                <Send className="w-3 h-3" />
                <span>Send</span>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-2xl border border-ssk-border shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap items-center gap-2 flex-1">
          <div className="relative flex-1 min-w-[180px]">
            <Search className="w-3.5 h-3.5 text-ssk-text-secondary absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search Order ID..."
              value={orderSearch}
              onChange={(e) => setOrderSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-navy"
            />
          </div>
          <input
            type="text"
            placeholder="Search phone or email..."
            value={recipientSearch}
            onChange={(e) => setRecipientSearch(e.target.value)}
            className="px-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-navy min-w-[180px]"
          />
          <button
            type="submit"
            className="px-3 py-1.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark transition-colors"
          >
            Filter
          </button>
        </form>

        <div className="flex items-center gap-2">
          <select
            value={channelFilter}
            onChange={(e) => setChannelFilter(e.target.value)}
            className="px-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none"
          >
            <option value="">All Channels</option>
            <option value="whatsapp">WhatsApp</option>
            <option value="email">Email</option>
          </select>

          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-3 py-1.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="sent">Sent</option>
            <option value="delivered">Delivered</option>
            <option value="read">Read</option>
            <option value="simulated">Simulated</option>
            <option value="failed">Failed</option>
          </select>
        </div>
      </div>

      {/* Outbox & Notification Logs Table */}
      <div className="bg-white rounded-2xl border border-ssk-border shadow-sm overflow-hidden">
        <div className="p-4 border-b border-ssk-border flex items-center justify-between">
          <h3 className="text-sm font-bold text-ssk-navy">
            Real-Time Notification Audit Log ({totalLogs})
          </h3>
          <span className="text-[10px] text-ssk-text-secondary">
            Page {page} &bull; Showing recent 20
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-ssk-surface text-ssk-navy font-bold border-b border-ssk-border">
              <tr>
                <th className="p-3.5">Timestamp</th>
                <th className="p-3.5">Channel</th>
                <th className="p-3.5">Event / Template</th>
                <th className="p-3.5">Recipient</th>
                <th className="p-3.5">Order ID</th>
                <th className="p-3.5">Delivery Status</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ssk-border">
              {loading ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-ssk-text-secondary">
                    Loading notifications...
                  </td>
                </tr>
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-ssk-text-secondary">
                    No notification records found matching criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => {
                  const isWhatsApp = log.channel === 'whatsapp';
                  const isSuccess = ['delivered', 'read', 'sent', 'simulated'].includes(log.status);

                  return (
                    <tr key={log.id || log.notification_id} className="hover:bg-ssk-blue-light/30 transition-colors">
                      <td className="p-3.5 font-mono text-[11px] text-ssk-text-secondary">
                        {log.created_at ? new Date(log.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            isWhatsApp
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-ssk-blue-light text-ssk-navy'
                          }`}
                        >
                          {isWhatsApp ? <MessageSquare className="w-3 h-3" /> : <Mail className="w-3 h-3" />}
                          <span>{isWhatsApp ? 'WhatsApp' : 'Email'}</span>
                        </span>
                      </td>
                      <td className="p-3.5 font-mono text-[11px] font-semibold text-ssk-navy">
                        {log.template_name || log.subject || 'Order Event'}
                      </td>
                      <td className="p-3.5 font-mono text-ssk-text">
                        {log.recipient}
                      </td>
                      <td className="p-3.5 font-mono font-bold text-ssk-navy">
                        {log.order_id || '—'}
                      </td>
                      <td className="p-3.5">
                        <span
                          className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            log.status === 'read'
                              ? 'bg-blue-100 text-blue-800'
                              : log.status === 'delivered'
                              ? 'bg-emerald-100 text-emerald-800'
                              : log.status === 'sent'
                              ? 'bg-slate-100 text-slate-800'
                              : log.status === 'simulated'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-red-100 text-red-800'
                          }`}
                        >
                          {log.status}
                        </span>
                      </td>
                      <td className="p-3.5 text-right">
                        <button
                          onClick={() => handleRetryNotification(log.notification_id || log.id)}
                          disabled={retryingId === (log.notification_id || log.id)}
                          title="Retry Notification"
                          className="px-2.5 py-1 border border-ssk-border hover:bg-ssk-surface rounded-lg text-[11px] font-semibold text-ssk-navy inline-flex items-center gap-1 transition-colors disabled:opacity-50"
                        >
                          <RotateCcw className={`w-3 h-3 ${retryingId === (log.notification_id || log.id) ? 'animate-spin' : ''}`} />
                          <span>Resend</span>
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalLogs > 20 && (
          <div className="p-4 border-t border-ssk-border flex items-center justify-between text-xs">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 border border-ssk-border rounded-lg disabled:opacity-40"
            >
              Previous
            </button>
            <span className="text-ssk-text-secondary">
              Page {page} of {Math.ceil(totalLogs / 20)}
            </span>
            <button
              disabled={page >= Math.ceil(totalLogs / 20)}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 border border-ssk-border rounded-lg disabled:opacity-40"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </PageTransition>
  );
};
