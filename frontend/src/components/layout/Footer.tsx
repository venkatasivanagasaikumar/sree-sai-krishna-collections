import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Phone, Mail, MapPin, ShieldCheck, RefreshCw, Truck, Heart } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import { BRAND_CONFIG } from '../../assets/brand.config';
import { ScrollReveal } from '../animations/ScrollReveal';
import { StaggerContainer } from '../animations/StaggerContainer';
import { fadeUp } from '../../animations';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-ssk-navy-dark text-white border-t-2 border-ssk-gold">
      {/* Trust Badges Bar */}
      <div className="border-b border-white/10 py-8 bg-ssk-navy">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <motion.div variants={fadeUp} className="flex items-center gap-4 group">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-ssk-gold flex-shrink-0 group-hover:scale-110 group-hover:bg-ssk-gold/20 transition-all duration-300">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">100% Quality Guaranteed</h4>
                <p className="text-xs text-gray-300">Premium micro-plated finishing</p>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="flex items-center gap-4 group">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-ssk-gold flex-shrink-0 group-hover:scale-110 group-hover:bg-ssk-gold/20 transition-all duration-300">
                <Truck className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Free Express Shipping</h4>
                <p className="text-xs text-gray-300">On all prepaid orders over ₹999</p>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="flex items-center gap-4 group">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-ssk-gold flex-shrink-0 group-hover:scale-110 group-hover:bg-ssk-gold/20 transition-all duration-300">
                <RefreshCw className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">7-Day Easy Returns</h4>
                <p className="text-xs text-gray-300">Hassle-free replacement policy</p>
              </div>
            </motion.div>

            <motion.div variants={fadeUp} className="flex items-center gap-4 group">
              <div className="w-12 h-12 rounded-2xl bg-white/10 flex items-center justify-center text-ssk-gold flex-shrink-0 group-hover:scale-110 group-hover:bg-ssk-gold/20 transition-all duration-300">
                <Phone className="w-6 h-6" />
              </div>
              <div>
                <h4 className="text-sm font-semibold">Dedicated Customer Support</h4>
                <p className="text-xs text-gray-300">+91 98480 22338 (Mon-Sat)</p>
              </div>
            </motion.div>
          </StaggerContainer>
        </div>
      </div>

      {/* Main Footer Links */}
      <ScrollReveal className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
        
        {/* Brand Column */}
        <div className="lg:col-span-2 space-y-4">
          <Link
            to="/"
            title="Go to Home"
            aria-label="Sree Sai Krishna Collections Home"
            className="inline-block transition-opacity hover:opacity-90"
          >
            <BrandLogo size="lg" light />
          </Link>
          <p className="text-xs text-gray-300 leading-relaxed max-w-sm">
            {BRAND_CONFIG.name} ({BRAND_CONFIG.shortName}) brings timeless South-Indian heritage,
            micro 1-gram gold tone perfection, bridal sets, and chic modern hair accessories directly to your doorstep.
          </p>
          <div className="pt-2 text-xs text-ssk-gold-light space-y-1.5">
            <p className="flex items-start gap-2">
              <MapPin className="w-4 h-4 text-ssk-gold flex-shrink-0 mt-0.5" />
              <span>{BRAND_CONFIG.contact.address}</span>
            </p>
            <p className="flex items-center gap-2">
              <Phone className="w-4 h-4 text-ssk-gold flex-shrink-0" />
              <span>{BRAND_CONFIG.contact.phone}</span>
            </p>
            <p className="flex items-center gap-2">
              <Mail className="w-4 h-4 text-ssk-gold flex-shrink-0" />
              <span>{BRAND_CONFIG.contact.email}</span>
            </p>
          </div>
        </div>

        {/* Collections */}
        <div>
          <h3 className="font-serif font-bold text-sm tracking-wider text-ssk-gold uppercase mb-4">
            Jewellery
          </h3>
          <ul className="space-y-2 text-xs text-gray-300">
            <li><Link to="/shop?category=1-Gram+Gold+Jewellery" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">1-Gram Gold Sets</Link></li>
            <li><Link to="/shop?category=Earrings+%26+Jhumkas" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Temple Jhumkas</Link></li>
            <li><Link to="/shop?category=Necklaces+%26+Chains" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Bridal Chokers & Haaram</Link></li>
            <li><Link to="/shop?category=Bangles+%26+Bracelets" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Kada Bangles</Link></li>
            <li><Link to="/shop?category=Traditional+Accessories" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Bridal Vaddanam</Link></li>
          </ul>
        </div>

        {/* Hair Accessories */}
        <div>
          <h3 className="font-serif font-bold text-sm tracking-wider text-ssk-gold uppercase mb-4">
            Hair & Accessories
          </h3>
          <ul className="space-y-2 text-xs text-gray-300">
            <li><Link to="/shop?category=Claw+Clips" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Matte French Claw Clips</Link></li>
            <li><Link to="/shop?category=Scrunchies+%26+Hair+Bands" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Pure Silk Scrunchies</Link></li>
            <li><Link to="/shop?category=Hair+Clips+%26+Pins" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Pearl Bridal Hair Pins</Link></li>
            <li><Link to="/shop" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Festive Gift Boxes</Link></li>
            <li><Link to="/shop?sort_by=newest" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">New Arrivals</Link></li>
          </ul>
        </div>

        {/* Help & Policies */}
        <div>
          <h3 className="font-serif font-bold text-sm tracking-wider text-ssk-gold uppercase mb-4">
            Customer Care
          </h3>
          <ul className="space-y-2 text-xs text-gray-300">
            <li><Link to="/account/orders" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Track Your Order</Link></li>
            <li><Link to="/account" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">My Account</Link></li>
            <li><Link to="/policies" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Returns & Refunds Policy</Link></li>
            <li><Link to="/policies" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Shipping & Delivery Info</Link></li>
            <li><Link to="/contact" className="hover:text-ssk-gold-light transition-colors hover:translate-x-1 inline-block">Contact Support</Link></li>
            <li className="pt-2">
              <Link to="/admin/login" className="text-ssk-gold-light hover:underline font-semibold flex items-center gap-1">
                Meesho Seller Panel &rarr;
              </Link>
            </li>
          </ul>
        </div>
      </ScrollReveal>

      {/* Important Disclaimer & Copyright */}
      <div className="border-t border-white/10 py-6 bg-black/20 text-center px-4">
        <p className="text-[11px] text-gray-400 max-w-4xl mx-auto leading-relaxed mb-3">
          <strong className="text-ssk-gold">Consumer Transparency Note:</strong> Sree Sai Krishna Collections specializes in premium imitation, fashion jewellery, and 1-gram gold tone electroplated finishes. None of our fashion pieces claim or contain solid gold bullion or BIS precious hallmarking unless explicitly verified and stated in supplier technical sheets.
        </p>
        <p className="text-xs text-gray-400 flex items-center justify-center gap-1">
          &copy; {new Date().getFullYear()} {BRAND_CONFIG.name} (SSK). All Rights Reserved. Crafted with <Heart className="w-3.5 h-3.5 text-red-400 fill-red-400" /> for India.
        </p>
      </div>
    </footer>
  );
};
