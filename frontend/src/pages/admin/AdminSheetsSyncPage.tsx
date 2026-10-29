import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet, RefreshCw, Send, CheckCircle2, AlertCircle,
  Copy, ExternalLink, Download, ArrowUpRight, ShieldCheck, Database
} from 'lucide-react';
import { api } from '../../services/api';

export const AdminSheetsSyncPage: React.FC = () => {
  const [config, setConfig] = useState({
    webhook_url: '',
    auto_sync_on_order: true,
    auto_sync_on_product: true,
    last_synced_at: null as string | null,
    status: 'not_configured'
  });
  const [appScript, setAppScript] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [pushing, setPushing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [cfg, scriptRes] = await Promise.all([
        api.getSheetsConfig(),
        api.getAppScriptTemplate()
      ]);
      setConfig(cfg);
      setAppScript(scriptRes.script);
    } catch (e: any) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);
    try {
      const res = await api.saveSheetsConfig(config);
      setConfig(res.config);
      setStatusMessage({ type: 'success', text: 'Google Sheet configuration saved successfully.' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to save configuration.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.webhook_url) {
      setStatusMessage({ type: 'error', text: 'Please enter a Google Apps Script Web App URL first.' });
      return;
    }
    setTesting(true);
    setStatusMessage(null);
    try {
      const res = await api.testSheetsConnection(config.webhook_url);
      setStatusMessage({ type: 'success', text: res.message || 'Connected to Google Sheet successfully!' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Connection test failed. Check your Web App URL.' });
    } finally {
      setTesting(false);
    }
  };

  const handlePushAllData = async () => {
    if (!config.webhook_url) {
      setStatusMessage({ type: 'error', text: 'Please configure and save your Google Apps Script URL before syncing.' });
      return;
    }
    setPushing(true);
    setStatusMessage(null);
    try {
      const res = await api.pushAllToSheets();
      setConfig((prev) => ({
        ...prev,
        last_synced_at: res.last_synced_at,
        status: 'synced'
      }));
      setStatusMessage({ type: 'success', text: res.message || 'All data synchronized to Google Sheet!' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Sync failed.' });
    } finally {
      setPushing(false);
    }
  };

  const handleDownloadJsonBackup = async () => {
    try {
      const data = await api.exportAllForSheets();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ssk_database_export_${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      alert('Failed to export data: ' + e.message);
    }
  };

  const copyAppScript = () => {
    navigator.clipboard.writeText(appScript);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-serif font-bold text-ssk-navy">Google Sheets & Excel Database Sync</h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-green-100 text-green-800">
              Live Two-Way Ready
            </span>
          </div>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Connect your store to a Google Sheet so products, orders, inventory logs, and customer records update in real time like an Excel spreadsheet.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleDownloadJsonBackup}
            className="px-4 py-2.5 border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-all shadow-sm"
          >
            <Download className="w-4 h-4" />
            <span>Download All Data (JSON)</span>
          </button>
          <button
            onClick={handlePushAllData}
            disabled={pushing || !config.webhook_url}
            className={`px-5 py-2.5 text-xs font-bold rounded-xl flex items-center gap-2 shadow-md transition-all ${
              pushing || !config.webhook_url
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-ssk-gold hover:bg-ssk-gold-dark text-white'
            }`}
          >
            <RefreshCw className={`w-4 h-4 ${pushing ? 'animate-spin' : ''}`} />
            <span>{pushing ? 'Syncing...' : 'Push All Data to Sheet Now'}</span>
          </button>
        </div>
      </div>

      {statusMessage && (
        <div
          className={`p-4 rounded-2xl border text-xs flex items-center gap-3 ${
            statusMessage.type === 'success'
              ? 'bg-green-50 border-green-200 text-green-800'
              : 'bg-red-50 border-red-200 text-red-800'
          }`}
        >
          {statusMessage.type === 'success' ? (
            <CheckCircle2 className="w-5 h-5 flex-shrink-0 text-green-600" />
          ) : (
            <AlertCircle className="w-5 h-5 flex-shrink-0 text-red-600" />
          )}
          <span className="font-medium">{statusMessage.text}</span>
        </div>
      )}

      {/* Main Grid: Settings & Apps Script Instructions */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Connection Setup Form */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-white rounded-3xl border border-ssk-border p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-ssk-border mb-5">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-ssk-navy/10 flex items-center justify-center text-ssk-navy">
                  <FileSpreadsheet className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-ssk-navy">Google Apps Script Webhook</h3>
                  <p className="text-[11px] text-ssk-text-secondary">Enter the deployed Web App URL from your Google Sheet</p>
                </div>
              </div>
              <span
                className={`text-[10px] font-bold px-2.5 py-1 rounded-full ${
                  config.status === 'synced' || config.status === 'connected'
                    ? 'bg-green-100 text-green-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                {config.status === 'synced'
                  ? 'Active & Synced'
                  : config.status === 'connected'
                  ? 'URL Configured'
                  : 'Not Connected'}
              </span>
            </div>

            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-ssk-text mb-1">
                  Google Apps Script Web App URL *
                </label>
                <input
                  type="url"
                  placeholder="https://script.google.com/macros/s/AKfycb.../exec"
                  value={config.webhook_url}
                  onChange={(e) => setConfig({ ...config, webhook_url: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-mono text-ssk-text focus:outline-none focus:border-ssk-gold"
                  required
                />
                <p className="text-[10px] text-ssk-text-secondary mt-1">
                  Get this by clicking <strong>Deploy &rarr; New deployment &rarr; Web app</strong> inside your Google Sheet.
                </p>
              </div>

              <div className="space-y-3 pt-2">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.auto_sync_on_order}
                    onChange={(e) => setConfig({ ...config, auto_sync_on_order: e.target.checked })}
                    className="w-4 h-4 text-ssk-navy rounded border-ssk-border focus:ring-ssk-gold"
                  />
                  <span className="text-xs font-medium text-ssk-text">
                    Automatically push new orders and status updates to Sheet
                  </span>
                </label>

                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={config.auto_sync_on_product}
                    onChange={(e) => setConfig({ ...config, auto_sync_on_product: e.target.checked })}
                    className="w-4 h-4 text-ssk-navy rounded border-ssk-border focus:ring-ssk-gold"
                  />
                  <span className="text-xs font-medium text-ssk-text">
                    Automatically sync catalog modifications and inventory movements
                  </span>
                </label>
              </div>

              {config.last_synced_at && (
                <div className="p-3 bg-ssk-blue-light/50 rounded-xl text-[11px] text-ssk-navy flex items-center justify-between">
                  <span>Last Full Synchronization:</span>
                  <span className="font-mono font-bold">
                    {new Date(config.last_synced_at).toLocaleString()}
                  </span>
                </div>
              )}

              <div className="flex items-center justify-between pt-4 border-t border-ssk-border">
                <button
                  type="button"
                  onClick={handleTestConnection}
                  disabled={testing || !config.webhook_url}
                  className="px-4 py-2 border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-all"
                >
                  <Send className={`w-3.5 h-3.5 ${testing ? 'animate-pulse' : ''}`} />
                  <span>{testing ? 'Testing...' : 'Test Connection'}</span>
                </button>

                <button
                  type="submit"
                  disabled={saving}
                  className="px-5 py-2 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl transition-all shadow-sm"
                >
                  {saving ? 'Saving...' : 'Save Configuration'}
                </button>
              </div>
            </form>
          </div>

          {/* Sync Architecture Card */}
          <div className="bg-gradient-to-br from-ssk-navy to-ssk-navy-dark text-white rounded-3xl p-6 shadow-md">
            <h4 className="text-sm font-bold flex items-center gap-2">
              <Database className="w-4 h-4 text-ssk-gold" />
              <span>Multi-Sheet Tab Structure</span>
            </h4>
            <p className="text-xs text-blue-100/80 mt-1">
              When synced, the Google Apps Script automatically creates and formats 4 separate tabs inside your spreadsheet:
            </p>
            <div className="grid grid-cols-2 gap-3 mt-4 text-xs">
              <div className="p-3 bg-white/10 rounded-xl border border-white/10">
                <span className="font-bold text-ssk-gold block">1. Products Tab</span>
                <span className="text-[11px] text-blue-100/70">SKU, Name, Category, Price, MRP, Stock, Finish</span>
              </div>
              <div className="p-3 bg-white/10 rounded-xl border border-white/10">
                <span className="font-bold text-ssk-gold block">2. Orders Tab</span>
                <span className="text-[11px] text-blue-100/70">Order ID, Customer, Phone, Total, Status, AWB</span>
              </div>
              <div className="p-3 bg-white/10 rounded-xl border border-white/10">
                <span className="font-bold text-ssk-gold block">3. Customers Tab</span>
                <span className="text-[11px] text-blue-100/70">Customer Name, Email, Phone, Order History</span>
              </div>
              <div className="p-3 bg-white/10 rounded-xl border border-white/10">
                <span className="font-bold text-ssk-gold block">4. Inventory Log</span>
                <span className="text-[11px] text-blue-100/70">SKU, Movement, Change Qty, Reason, Auditor</span>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Google Apps Script Code & Copy */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-white rounded-3xl border border-ssk-border p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-ssk-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-ssk-navy">Google Apps Script Code</h3>
                <p className="text-[11px] text-ssk-text-secondary">Copy and paste this into your Google Sheet's Apps Script</p>
              </div>
              <button
                onClick={copyAppScript}
                className="px-3.5 py-1.5 bg-ssk-navy text-white text-xs font-bold rounded-xl flex items-center gap-1.5 shadow-sm hover:bg-ssk-navy-dark transition-all"
              >
                {copied ? <CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copied ? 'Copied to Clipboard!' : 'Copy Code'}</span>
              </button>
            </div>

            {/* Quick 3-step Instructions */}
            <ol className="text-xs space-y-1.5 text-ssk-text mb-4 bg-ssk-surface p-3.5 rounded-2xl border border-ssk-border">
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-ssk-navy text-white font-bold flex items-center justify-center text-[10px]">1</span>
                <span>Open Google Sheets &rarr; click <strong>Extensions &rarr; Apps Script</strong>.</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-ssk-navy text-white font-bold flex items-center justify-center text-[10px]">2</span>
                <span>Delete default code, paste this script, and click <strong>Deploy &rarr; New deployment</strong>.</span>
              </li>
              <li className="flex items-center gap-2">
                <span className="w-5 h-5 rounded-full bg-ssk-navy text-white font-bold flex items-center justify-center text-[10px]">3</span>
                <span>Set type: <strong>Web app</strong>, Who has access: <strong>Anyone</strong>, and copy the Web App URL!</span>
              </li>
            </ol>

            <div className="relative">
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-2xl text-[11px] font-mono overflow-x-auto max-h-[380px] leading-relaxed">
                {appScript}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};