import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Truck, ShieldCheck } from 'lucide-react';
import { fadeDown } from '../../animations';

export const AnnouncementBar: React.FC = () => {
  return (
    <motion.div
      variants={fadeDown}
      initial="hidden"
      animate="visible"
      className="bg-ssk-navy-dark text-white text-xs py-2 px-4 border-b border-ssk-gold/30 relative overflow-hidden"
    >
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2 text-center sm:text-left relative z-10">
        <div className="flex items-center justify-center gap-2 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-ssk-gold animate-pulse flex-shrink-0" />
          <span>
            Festive Launch Celebration: Use coupon <span className="text-ssk-gold-light font-bold tracking-wider px-1.5 py-0.5 bg-white/10 rounded border border-ssk-gold/30">SSKFIRST10</span> for 10% OFF
          </span>
        </div>
        <div className="hidden md:flex items-center gap-6 text-[11px] text-gray-300">
          <span className="flex items-center gap-1.5 transition-colors hover:text-white">
            <Truck className="w-3.5 h-3.5 text-ssk-gold" />
            Free Express Delivery above ₹999
          </span>
          <span className="flex items-center gap-1.5 transition-colors hover:text-white">
            <ShieldCheck className="w-3.5 h-3.5 text-ssk-gold" />
            Authentic South-Indian Craftsmanship
          </span>
        </div>
      </div>
    </motion.div>
  );
};
