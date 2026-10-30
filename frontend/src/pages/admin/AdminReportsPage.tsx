import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { BarChart3, ShieldCheck, Download, History } from 'lucide-react';
import { api } from '../../services/api';
import { PageTransition } from '../../components/animations/PageTransition';

export const AdminReportsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAuditLogs(100)
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownloadLogs = () => {
    const csvContent = "data:text/csv;charset=utf-8," 
      + ["Action,Resource_Type,Resource_ID,User,Status,Timestamp"].join(",") + "\n"
      + logs.map(l => `"${l.action}","${l.resource_type}","${l.resource_id || ''}","${l.user_email || ''}","${l.status}","${l.created_at}"`).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `ssk_audit_logs_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <PageTransition className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Audit Logs & Security Trail</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Immutable log of all administrative actions, stock adjustments, order state changes, and logins.
          </p>
        </div>

        <motion.button
          whileTap={{ scale: 0.95 }}
          onClick={handleDownloadLogs}
          className="px-4 py-2 border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-sm transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export Audit Log</span>
        </motion.button>
      </div>

      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <table className="w-full text-xs text-left">
          <thead className="bg-ssk-surface text-ssk-text-secondary border-b uppercase font-semibold text-[10px] tracking-wider">
            <tr>
              <th className="py-4 px-6">Timestamp</th>
              <th className="py-4 px-4">Action Event</th>
              <th className="py-4 px-4">Resource</th>
              <th className="py-4 px-4">Actor</th>
              <th className="py-4 px-4">Details</th>
              <th className="py-4 px-6 text-right">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-ssk-border font-medium">
            {logs.length > 0 ? (
              logs.map((log, i) => (
                <tr key={i} className="hover:bg-ssk-blue-light/30 transition-colors">
                  <td className="py-3 px-6 text-[11px] text-ssk-text-secondary">
                    {new Date(log.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-4 font-mono font-bold text-ssk-navy">{log.action}</td>
                  <td className="py-3 px-4 font-semibold text-ssk-text">{log.resource_type} ({log.resource_id || '-'})</td>
                  <td className="py-3 px-4 text-ssk-text-secondary">{log.user_email || 'System'}</td>
                  <td className="py-3 px-4 text-ssk-text-secondary max-w-xs truncate">
                    {JSON.stringify(log.details || {})}
                  </td>
                  <td className="py-3 px-6 text-right">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-[9px] font-bold ${
                      log.status === 'SUCCESS' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                    }`}>
                      {log.status}
                    </span>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="py-8 text-center text-ssk-text-secondary">No audit records recorded yet.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </PageTransition>
  );
};
