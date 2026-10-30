import React, { useState, useEffect } from 'react';
import { Settings, Save, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { api } from '../../services/api';
import { PageTransition } from '../../components/animations';
import { fadeDown } from '../../animations';

export const AdminSettingsPage: React.FC = () => {
  const [settings, setSettings] = useState<any>({
    brand_name: 'Sree Sai Krishna Collections',
    brand_short_name: 'SSK',
    support_email: 'support@sreesaikrishnacollections.com',
    support_phone: '+91 98480 22338',
    business_address: 'Shop #12, Sri Krishna Temple Street, Near Clock Tower, Secunderabad, Telangana - 500003, India',
    free_shipping_threshold: 999,
    standard_shipping_fee: 79,
    enable_cod: true,
    cod_min_order: 299,
    cod_max_order: 50000,
    maintenance_mode: false
  });
  const [isSaving, setIsSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    api.getPublicSettings().then((res) => {
      if (res) setSettings(res);
    });
  }, []);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    try {
      await api.updateSettingsAdmin(settings);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 3000);
    } catch (err: any) {
      alert(err.message || 'Failed to save settings');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <PageTransition>
      <div className="max-w-3xl space-y-6">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Store & Business Settings</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Configure business details, shipping thresholds, COD boundaries, and store policies.
          </p>
        </div>

        <AnimatePresence>
          {savedSuccess && (
            <motion.div
              variants={fadeDown}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="p-4 bg-green-50 border border-green-200 text-green-800 text-xs rounded-2xl flex items-center gap-2 shadow-sm"
            >
              <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
              <span className="font-medium">Store settings updated successfully!</span>
            </motion.div>
          )}
        </AnimatePresence>

        <form onSubmit={handleSave} className="bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border shadow-sm space-y-6 text-xs">
          <div className="space-y-4">
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider border-b pb-2">Brand Identity</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Official Brand Name</label>
                <input
                  type="text"
                  value={settings.brand_name}
                  onChange={(e) => setSettings({ ...settings, brand_name: e.target.value })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
              <div>
                <label className="block font-bold text-ssk-text mb-1">Brand Short Name</label>
                <input
                  type="text"
                  value={settings.brand_short_name}
                  onChange={(e) => setSettings({ ...settings, brand_short_name: e.target.value })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider border-b pb-2">Contact & Logistics Address</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Support Email</label>
                <input
                  type="email"
                  value={settings.support_email}
                  onChange={(e) => setSettings({ ...settings, support_email: e.target.value })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
              <div>
                <label className="block font-bold text-ssk-text mb-1">Support Phone / WhatsApp</label>
                <input
                  type="text"
                  value={settings.support_phone}
                  onChange={(e) => setSettings({ ...settings, support_phone: e.target.value })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
            </div>
            <div>
              <label className="block font-bold text-ssk-text mb-1">Warehouse & Flagship Address</label>
              <input
                type="text"
                value={settings.business_address}
                onChange={(e) => setSettings({ ...settings, business_address: e.target.value })}
                className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider border-b pb-2">Shipping & COD Rules</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Free Shipping Threshold (₹)</label>
                <input
                  type="number"
                  value={settings.free_shipping_threshold}
                  onChange={(e) => setSettings({ ...settings, free_shipping_threshold: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
              <div>
                <label className="block font-bold text-ssk-text mb-1">Standard Delivery Fee (₹)</label>
                <input
                  type="number"
                  value={settings.standard_shipping_fee}
                  onChange={(e) => setSettings({ ...settings, standard_shipping_fee: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Min COD Order Amount (₹)</label>
                <input
                  type="number"
                  value={settings.cod_min_order}
                  onChange={(e) => setSettings({ ...settings, cod_min_order: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
              <div>
                <label className="block font-bold text-ssk-text mb-1">Max COD Order Limit (₹)</label>
                <input
                  type="number"
                  value={settings.cod_max_order}
                  onChange={(e) => setSettings({ ...settings, cod_max_order: Number(e.target.value) })}
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-royal transition-colors"
                />
              </div>
            </div>
          </div>

          <div className="flex justify-end pt-4 border-t border-ssk-border">
            <motion.button
              type="submit"
              disabled={isSaving}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="px-6 py-2.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white rounded-xl font-bold flex items-center gap-2 shadow-md transition-all disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              <span>{isSaving ? 'Saving Changes...' : 'Save Settings'}</span>
            </motion.button>
          </div>
        </form>
      </div>
    </PageTransition>
  );
};
