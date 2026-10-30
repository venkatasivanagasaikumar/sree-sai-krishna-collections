import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Mail, Lock, Phone, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { PageTransition } from '../../components/animations/PageTransition';
import { fadeDown } from '../../animations';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      return;
    }
    setIsSubmitting(true);
    try {
      await register({
        full_name: fullName,
        email,
        phone,
        password
      });
      navigate('/account');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageTransition className="min-h-[85vh] flex items-center justify-center px-4 py-12">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
        className="max-w-md w-full bg-white rounded-3xl p-8 border border-ssk-border shadow-xl space-y-6"
      >
        <div className="text-center space-y-2">
          <BrandLogo size="lg" className="justify-center mx-auto" />
          <h2 className="text-xl font-serif font-bold text-ssk-navy pt-2">Join SSK Collections</h2>
          <p className="text-xs text-ssk-text-secondary">Create an account for exclusive offers, tracking & instant checkout</p>
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
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Full Name</label>
            <div className="relative">
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="e.g. Priya Sharma"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <User className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

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
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Mobile Phone</label>
            <div className="relative">
              <input
                type="tel"
                required
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                placeholder="+91 98765 43210"
                className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
              />
              <Phone className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-ssk-text mb-1.5">Password</label>
            <div className="relative">
              <input
                type="password"
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Minimum 6 characters"
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
                <span>Creating Account...</span>
              </>
            ) : (
              <>
                <span>Register Account</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </motion.button>
        </form>

        <div className="text-center pt-2 border-t border-ssk-border">
          <p className="text-xs text-ssk-text-secondary">
            Already have an account?{' '}
            <Link to="/login" className="font-bold text-ssk-navy hover:underline">
              Sign In
            </Link>
          </p>
        </div>
      </motion.div>
    </PageTransition>
  );
};
