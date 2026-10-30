import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Mail, ArrowRight, ArrowLeft, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { BrandLogo } from '../../components/common/BrandLogo';
import { PageTransition } from '../../components/animations/PageTransition';
import { fadeDown } from '../../animations';
import { api } from '../../services/api';

export const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.forgotPassword(email);
      setIsSuccess(true);
    } catch (err: any) {
      setError(err?.message || 'Failed to submit password reset request');
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
          <h2 className="text-xl font-serif font-bold text-ssk-navy pt-2">Recover Your Password</h2>
          <p className="text-xs text-ssk-text-secondary">
            Enter the email associated with your account and we'll send you a secure link to reset your password.
          </p>
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

          {isSuccess && (
            <motion.div
              variants={fadeDown}
              initial="hidden"
              animate="visible"
              exit="exit"
              className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs rounded-xl flex flex-col gap-2"
            >
              <div className="flex items-center gap-2 font-semibold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span>Reset Instructions Sent</span>
              </div>
              <p className="text-[11px] text-emerald-700 leading-relaxed">
                If an account with that email exists, we've sent password reset instructions. Please check your inbox and spam folder. The link expires in 15 minutes.
              </p>
            </motion.div>
          )}
        </AnimatePresence>

        {!isSuccess ? (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-ssk-text mb-1.5">Registered Email</label>
              <div className="relative">
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your.email@example.com"
                  className="w-full pl-9 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold transition-colors"
                />
                <Mail className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
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
                  <span>Sending Instructions...</span>
                </>
              ) : (
                <>
                  <span>Send Reset Link</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </motion.button>
          </form>
        ) : (
          <div className="space-y-3 pt-2">
            <Link
              to="/login"
              className="w-full py-3 bg-ssk-navy text-white font-bold text-xs rounded-xl shadow-md flex items-center justify-center gap-2 hover:bg-ssk-navy-dark transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Sign In</span>
            </Link>
          </div>
        )}

        <div className="text-center pt-2 border-t border-ssk-border">
          <Link
            to="/login"
            className="inline-flex items-center gap-1.5 text-xs text-ssk-text-secondary hover:text-ssk-navy font-semibold transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Sign In</span>
          </Link>
        </div>
      </motion.div>
    </PageTransition>
  );
};
