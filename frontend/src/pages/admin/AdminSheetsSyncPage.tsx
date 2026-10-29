import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet, RefreshCw, Send, CheckCircle2, AlertCircle,
  Copy, ExternalLink, Download, ArrowUpRight, ShieldCheck, Database,
  Lock, KeyRound, UserCheck
} from 'lucide-react';
import { api } from '../../services/api';

export const AdminSheetsSyncPage: React.FC = () => {
  const [config, setConfig] = useState({
    webhook_url: '',
    secret_key: '',
    owner_email: 'saikumaryenduri7@gmail.com',
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
  const [copiedScript, setCopiedScript] = useState(false);
  const [copiedKey, setCopiedKey] = useState(false);

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
      // Reload template with new secret
      const scriptRes = await api.getAppScriptTemplate();
      setAppScript(scriptRes.script);
      setStatusMessage({ type: 'success', text: 'Private security credentials and Webhook URL saved successfully.' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Failed to save configuration.' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async () => {
    if (!config.webhook_url) {
      setStatusMessage({ type: 'error', text: 'Please enter your Google Apps Script Web App URL first.' });
      return;
    }
    setTesting(true);
    setStatusMessage(null);
    try {
      const res = await api.testSheetsConnection(config.webhook_url, config.secret_key);
      setStatusMessage({ type: 'success', text: res.message || 'Private connection authenticated successfully!' });
    } catch (err: any) {
      setStatusMessage({ type: 'error', text: err.message || 'Connection test failed. Check your Web App URL and Secret Key.' });
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
      setStatusMessage({ type: 'success', text: res.message || 'All database records securely synced to your Google Sheet!' });
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
    setCopiedScript(true);
    setTimeout(() => setCopiedScript(false), 2500);
  };

  const copySecretKey = () => {
    navigator.clipboard.writeText(config.secret_key);
    setCopiedKey(true);
    setTimeout(() => setCopiedKey(false), 2500);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-serif font-bold text-ssk-navy">Owner-Only Google Sheets & Excel Database</h1>
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-100 text-amber-900 flex items-center gap-1 border border-amber-300">
              <Lock className="w-3 h-3 text-amber-700" />
              <span>Restricted & Encrypted Access</span>
            </span>
          </div>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Maintain your store database in a private Google Sheet that <strong>only you</strong> can view or edit, secured by your personal secret token.
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

      {/* Security Banner: How Privacy is Guaranteed */}
      <div className="bg-gradient-to-r from-slate-900 to-ssk-navy text-white p-4 rounded-2xl border border-ssk-gold/30 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-ssk-gold/20 flex items-center justify-center text-ssk-gold flex-shrink-0">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-white block">Strict Privacy Guarantee: Only You Have Access</span>
            <span className="text-blue-100/80 text-[11px]">
              Keep your Google Sheet sharing setting set to <strong>"Restricted"</strong> (Private to {config.owner_email}).
              No one else on the web or in your store staff can see or open your spreadsheet.
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-[11px] font-mono bg-white/10 px-2.5 py-1 rounded-lg border border-white/20">
            Owner: {config.owner_email}
          </span>
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
                  <KeyRound className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-ssk-navy">Owner Security Configuration</h3>
                  <p className="text-[11px] text-ssk-text-secondary">Secret key authentication for Google Apps Script</p>
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
                  ? 'Private & Synced'
                  : config.status === 'connected'
                  ? 'URL Configured'
                  : 'Not Connected'}
              </span>
            </div>

            <form onSubmit={handleSaveConfig} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-ssk-text mb-1">
                  Owner Email Address
                </label>
                <input
                  type="email"
                  value={config.owner_email}
                  onChange={(e) => setConfig({ ...config, owner_email: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-medium text-ssk-text focus:outline-none focus:border-ssk-gold"
                  required
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="block text-xs font-bold text-ssk-text">
                    Unique Secret Security Token
                  </label>
                  <button
                    type="button"
                    onClick={copySecretKey}
                    className="text-[10px] text-ssk-navy font-bold hover:underline flex items-center gap-1"
                  >
                    {copiedKey ? 'Copied Token!' : 'Copy Token'}
                  </button>
                </div>
                <input
                  type="text"
                  value={config.secret_key}
                  onChange={(e) => setConfig({ ...config, secret_key: e.target.value })}
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-mono text-ssk-navy font-bold focus:outline-none focus:border-ssk-gold"
                  required
                />
                <p className="text-[10px] text-ssk-text-secondary mt-1">
                  The Google Apps Script rejects any sync payload that does not match this secret key.
                </p>
              </div>

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
                    Automatically update your private sheet when new orders arrive
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
                    Automatically update your sheet on product and stock modifications
                  </span>
                </label>
              </div>

              {config.last_synced_at && (
                <div className="p-3 bg-ssk-blue-light/50 rounded-xl text-[11px] text-ssk-navy flex items-center justify-between">
                  <span>Last Synchronization:</span>
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

          {/* Sheet Security Checklist */}
          <div className="bg-white rounded-3xl border border-ssk-border p-6 shadow-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-ssk-navy mb-3 flex items-center gap-2">
              <Lock className="w-4 h-4 text-ssk-gold" />
              <span>Google Sheet Privacy Settings Checklist</span>
            </h4>
            <div className="space-y-2.5 text-xs text-ssk-text">
              <div className="flex items-start gap-2.5 p-2.5 bg-ssk-surface rounded-xl border border-ssk-border">
                <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-ssk-navy">Spreadsheet Sharing:</strong> Keep it set to <strong>"Restricted"</strong> in Google Sheets. Do not share the link with anyone.
                </div>
              </div>
              <div className="flex items-start gap-2.5 p-2.5 bg-ssk-surface rounded-xl border border-ssk-border">
                <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-ssk-navy">Apps Script Execution:</strong> Set <em>"Execute as: Me"</em> during deployment so it uses your personal permissions.
                </div>
              </div>
              <div className="flex items-start gap-2.5 p-2.5 bg-ssk-surface rounded-xl border border-ssk-border">
                <CheckCircle2 className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="text-ssk-navy">Payload Token:</strong> Every data packet sent by this site carries your unique secret token. Any unauthorized ping is immediately rejected with 401.
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column: Google Apps Script Code & Copy */}
        <div className="lg:col-span-6 space-y-6">
          <div className="bg-white rounded-3xl border border-ssk-border p-6 shadow-sm">
            <div className="flex items-center justify-between pb-4 border-b border-ssk-border mb-4">
              <div>
                <h3 className="text-sm font-bold text-ssk-navy">Owner-Secured Google Apps Script</h3>
                <p className="text-[11px] text-ssk-text-secondary">Pre-configured with your private security token</p>
              </div>
              <button
                onClick={copyAppScript}
                className="px-3.5 py-1.5 bg-ssk-navy text-white text-xs font-bold rounded-xl flex items-center gap-1.5 shadow-sm hover:bg-ssk-navy-dark transition-all"
              >
                {copiedScript ? <CheckCircle2 className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedScript ? 'Copied to Clipboard!' : 'Copy Code'}</span>
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
                <span>Set type: <strong>Web app</strong>, Execute as: <strong>Me</strong>, and paste the URL on the left!</span>
              </li>
            </ol>

            <div className="relative">
              <pre className="p-4 bg-slate-900 text-slate-100 rounded-2xl text-[11px] font-mono overflow-x-auto max-h-[460px] leading-relaxed">
                {appScript}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};