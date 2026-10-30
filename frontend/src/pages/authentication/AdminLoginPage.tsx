import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Lock, Mail, ArrowRight, AlertCircle, KeyRound, Loader2 } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { PageTransition } from '../../components/animations/PageTransition';
import { fadeDown } from '../../animations';

export const AdminLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await login({ email: email.trim(), password });
      const role = res.user.role;
      if (!['Super Admin', 'Admin', 'Order Manager', 'Inventory Manager', 'Customer Support'].includes(role)) {
        setError('Access denied. This account does not possess seller or staff permissions.');
        return;
      }
      navigate('/admin/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid administrative credentials');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageTransition className="min-h-screen bg-ssk-navy-dark flex items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#C89A43_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
      <div className="absolute top-0 right-0 w-96 h-96 bg-ssk-gold/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-ssk-blue-royal/20 rounded-full blur-3xl pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4 }}
        className="max-w-md w-full bg-white rounded-3xl p-8 shadow-2xl border-2 border-ssk-gold/40 relative z-10 space-y-6"
      >
        <div className="text-center space-y-2">
          <BrandLogo size="lg" className="justify-center mx-auto" />
          <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-bold mt-2">
            <Shield className="w-3.5 h-3.5 text-ssk-gold-dark" />
            <span>Store Operations & Seller Panel</span>
          </div>
          <h2 className="text-xl font-serif font-bold text-ssk-navy">Staff & Seller Portal</h2>
          <p className="text-xs text-ssk-text-secondary">Authorized personnel portal for product catalog, logistics, and inventory management</p>
        </div>

        <AnimatePresence>
          {error && (
            <motion.div
              variants={fadeDown}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="p-3.5 bg-red-50 border border-red-200 text-red-700 text-xs rounded-xl flex items-center gap-2"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{error}</span>
            </motion.div>
          )}
        </AnimatePresence>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Staff Email Address</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="staff@sreesaikrishnacollections.com"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <Mail className="w-4 h-4 text-ssk-text-muted absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Staff Password</label>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••••••"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <Lock className="w-4 h-4 text-ssk-text-muted absolute left-3 top-3" />
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.01 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3 bg-ssk-navy hover:bg-ssk-navy-dark text-white rounded-xl text-xs font-bold shadow-lg shadow-ssk-navy/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating Staff...</span>
              </>
            ) : (
              <>
                <KeyRound className="w-4 h-4 text-ssk-gold" />
                <span>Log In to Seller Portal</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>

        <div className="text-center pt-2 border-t border-ssk-border">
          <p className="text-[11px] text-ssk-text-muted flex items-center justify-center gap-1.5">
            <Shield className="w-3.5 h-3.5 text-ssk-gold" />
            <span>Encrypted Session • Super Admin & Staff Access Only</span>
          </p>
        </div>
      </motion.div>
    </PageTransition>
  );
};
