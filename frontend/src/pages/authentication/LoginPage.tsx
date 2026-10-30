import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, Lock, ArrowRight, ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { PageTransition } from '../../components/animations/PageTransition';
import { fadeDown } from '../../animations';

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const from = (location.state as any)?.from?.pathname || '/account';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await login({ email, password });
      navigate(from, { replace: true });
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageTransition className="min-h-[80vh] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="max-w-md w-full bg-white rounded-3xl p-8 border border-ssk-border shadow-xl space-y-6"
      >
        <div className="text-center space-y-2">
          <BrandLogo size="lg" className="justify-center mx-auto" />
          <h2 className="text-xl font-serif font-bold text-ssk-navy pt-2">Welcome Back</h2>
          <p className="text-xs text-ssk-text-secondary">Sign in to access your orders, saved addresses & bag</p>
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
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Email Address</label>
            <div className="relative">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="priya.sharma@example.com"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <Mail className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label className="text-xs font-semibold text-ssk-text">Password</label>
            </div>
            <div className="relative">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <Lock className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={isSubmitting}
            className="w-full py-3.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white font-bold text-xs rounded-xl shadow-md transition-all flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Signing in...</span>
              </>
            ) : (
              <>
                <span>Sign In</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>

        <div className="text-center space-y-3 pt-2 border-t border-ssk-border">
          <p className="text-xs text-ssk-text-secondary">
            Don't have an account?{' '}
            <Link to="/register" className="font-bold text-ssk-navy hover:underline">
              Create an Account
            </Link>
          </p>

          <Link
            to="/admin/login"
            className="block text-[11px] text-ssk-gold-dark font-medium hover:underline pt-1"
          >
            Are you a seller / administrator? Sign in here &rarr;
          </Link>
        </div>
      </motion.div>
    </PageTransition>
  );
};
