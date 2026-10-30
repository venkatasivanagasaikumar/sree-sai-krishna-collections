import React from 'react';
import { Outlet } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { AnnouncementBar } from './AnnouncementBar';
import { Navbar } from './Navbar';
import { Footer } from './Footer';
import { useCart } from '../../context/CartContext';
import { CheckCircle2, X } from 'lucide-react';
import { toastEnter } from '../../animations';

export const StorefrontLayout: React.FC = () => {
  const { toastMessage, clearToast } = useCart();

  return (
    <div className="min-h-screen flex flex-col bg-white">
      <AnnouncementBar />
      <Navbar />

      <main className="flex-1">
        <Outlet />
      </main>

      <Footer />

      {/* Floating Animated Toast Notification */}
      <AnimatePresence>
        {toastMessage && (
          <motion.div
            variants={toastEnter}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="fixed bottom-6 right-6 z-50 flex items-center gap-3 bg-ssk-navy text-white px-5 py-3.5 rounded-2xl shadow-2xl border border-ssk-gold/40"
          >
            <CheckCircle2 className="w-5 h-5 text-ssk-gold flex-shrink-0" />
            <span className="text-xs font-semibold">{toastMessage}</span>
            <motion.button
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              onClick={clearToast}
              className="ml-2 p-1 hover:bg-white/10 rounded-full transition-colors"
              aria-label="Dismiss message"
            >
              <X className="w-4 h-4 text-gray-300" />
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
