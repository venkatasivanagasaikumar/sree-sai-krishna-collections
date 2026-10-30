import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowRight, ShieldCheck, Gem, Award, Clock, Star, Copy, Check } from 'lucide-react';
import { ProductCard } from '../../components/products/ProductCard';
import { QuickViewModal } from '../../components/products/QuickViewModal';
import { api } from '../../services/api';
import { Product, Category, Coupon } from '../../types';
import { ScrollReveal } from '../../components/animations/ScrollReveal';
import { StaggerContainer } from '../../components/animations/StaggerContainer';
import { FadeIn } from '../../components/animations/FadeIn';
import { AnimatedCounter } from '../../components/animations/AnimatedCounter';
import {
  heroContainer,
  heroChild,
  imageReveal,
  fadeUp,
  scaleIn,
  floatSlow,
  floatMedium,
} from '../../animations';

export const HomePage: React.FC = () => {
  const [featuredProducts, setFeaturedProducts] = useState<Product[]>([]);
  const [bestsellerProducts, setBestsellerProducts] = useState<Product[]>([]);
  const [trendingProducts, setTrendingProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);
  const [copiedCoupon, setCopiedCoupon] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [featured, bestsellers, trending, cats, activeCoupons] = await Promise.all([
          api.getFeaturedProducts(),
          api.getBestsellerProducts(),
          api.getTrendingProducts(),
          api.getCategories(),
          api.getActiveCoupons(),
        ]);
        setFeaturedProducts(featured);
        setBestsellerProducts(bestsellers);
        setTrendingProducts(trending);
        setCategories(cats);
        setCoupons(activeCoupons);
      } catch (err) {
        console.error('Error fetching homepage data:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleCopyCoupon = (code: string) => {
    navigator.clipboard.writeText(code);
    setCopiedCoupon(code);
    setTimeout(() => setCopiedCoupon(null), 2500);
  };

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-r from-ssk-navy-dark via-ssk-navy to-ssk-navy-dark text-white py-16 sm:py-24 px-4 sm:px-6 lg:px-8 border-b-4 border-ssk-gold">
        {/* Subtle decorative background watermarks & floating gold particles */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#C89A43_1px,transparent_1px)] [background-size:24px_24px] pointer-events-none" />
        
        {/* Gentle floating ambient glow circles */}
        <motion.div
          animate={floatSlow}
          className="absolute -top-24 -right-24 w-96 h-96 rounded-full bg-ssk-gold/15 blur-3xl pointer-events-none"
        />
        <motion.div
          animate={floatMedium}
          className="absolute -bottom-24 -left-24 w-96 h-96 rounded-full bg-ssk-blue-royal/20 blur-3xl pointer-events-none"
        />

        <div className="max-w-7xl mx-auto relative z-10 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          {/* Hero Left Content with Staggered Entrance */}
          <motion.div
            variants={heroContainer}
            initial="hidden"
            animate="visible"
            className="lg:col-span-7 space-y-6 text-center lg:text-left"
          >
            <motion.div variants={heroChild}>
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 border border-ssk-gold/40 text-ssk-gold-light text-xs font-semibold backdrop-blur-sm shadow-sm">
                <Sparkles className="w-4 h-4 text-ssk-gold" />
                <span>Royal South-Indian Heritage Collection 2026</span>
              </div>
            </motion.div>

            <motion.h1
              variants={heroChild}
              className="text-3xl sm:text-5xl lg:text-6xl font-bold font-serif tracking-tight leading-tight"
            >
              Grace in Every Detail, <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-ssk-gold-light via-ssk-gold to-amber-200">
                Royalty in Every Touch.
              </span>
            </motion.h1>

            <motion.p
              variants={heroChild}
              className="text-gray-200 text-sm sm:text-base max-w-2xl leading-relaxed"
            >
              Explore exquisite 1-gram gold finish temple chokers, handcrafted antique jhumkas, kada bangles,
              and premium Korean hair accessories crafted for weddings, festivals, and unforgettable moments.
            </motion.p>

            <motion.div
              variants={heroChild}
              className="flex flex-wrap items-center justify-center lg:justify-start gap-4 pt-2"
            >
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                <Link
                  to="/shop"
                  className="px-8 py-3.5 bg-gradient-to-r from-ssk-gold to-ssk-gold-dark hover:from-ssk-gold-light hover:to-ssk-gold text-white font-bold text-sm rounded-xl shadow-lg hover:shadow-xl transition-all flex items-center gap-2"
                >
                  <span>Shop All Collections</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </motion.div>

              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                <Link
                  to="/shop?category=1-Gram+Gold+Jewellery"
                  className="px-8 py-3.5 bg-white/10 hover:bg-white/20 border border-white/20 text-white font-semibold text-sm rounded-xl backdrop-blur-sm transition-all"
                >
                  Explore 1-Gram Gold
                </Link>
              </motion.div>
            </motion.div>

            {/* Quick Highlights with Animated Counters */}
            <motion.div
              variants={heroChild}
              className="grid grid-cols-3 gap-4 pt-6 border-t border-white/15 text-center sm:text-left"
            >
              <div>
                <p className="text-2xl font-bold text-ssk-gold-light font-serif">
                  <AnimatedCounter value={100} duration={1.2} suffix="%" />
                </p>
                <p className="text-[11px] text-gray-300">Authentic Finish</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-ssk-gold-light font-serif">
                  <AnimatedCounter value={5000} duration={1.5} suffix="+" />
                </p>
                <p className="text-[11px] text-gray-300">Happy Customers</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-ssk-gold-light font-serif">
                  <AnimatedCounter value={4.9} duration={1.2} decimals={1} suffix=" ★" />
                </p>
                <p className="text-[11px] text-gray-300">Product Ratings</p>
              </div>
            </motion.div>
          </motion.div>

          {/* Hero Featured Image with Image Reveal Motion */}
          <div className="lg:col-span-5 relative">
            <motion.div
              variants={imageReveal}
              initial="hidden"
              animate="visible"
              className="relative mx-auto max-w-sm sm:max-w-md aspect-square rounded-3xl overflow-hidden shadow-2xl border-4 border-ssk-gold/50 group"
            >
              <img
                src="https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80"
                alt="SSK Bridal Collection"
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent flex flex-col justify-end p-6">
                <span className="text-xs font-semibold text-ssk-gold uppercase tracking-wider">Spotlight Creation</span>
                <h3 className="text-lg font-serif font-bold text-white">Royal Lakshmi Temple Choker Set</h3>
                <p className="text-xs text-gray-300 mt-1">Starting from ₹1,899 • Free Express Delivery</p>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Active Promotional Coupons Bar */}
      {coupons.length > 0 && (
        <ScrollReveal className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="bg-ssk-blue-light/70 border border-ssk-border rounded-2xl p-4 sm:p-6 shadow-sm">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-ssk-navy text-ssk-gold flex items-center justify-center flex-shrink-0 shadow-sm">
                  <Award className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-ssk-navy">Exclusive Launch Discounts</h3>
                  <p className="text-xs text-ssk-text-secondary">Tap any code below to instantly copy and apply at checkout.</p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                {coupons.map((c) => (
                  <motion.button
                    key={c.id}
                    whileHover={{ scale: 1.04 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleCopyCoupon(c.code)}
                    className="flex items-center gap-2 px-3.5 py-2 bg-white border border-ssk-gold rounded-xl text-xs font-bold text-ssk-navy hover:bg-ssk-gold/10 transition-all shadow-sm"
                    title={c.description}
                  >
                    <span className="tracking-wider">{c.code}</span>
                    <span className="text-[10px] text-ssk-gold-dark font-semibold">
                      ({c.discount_type === 'percentage' ? `${c.discount_value}% OFF` : `₹${c.discount_value} OFF`})
                    </span>
                    {copiedCoupon === c.code ? (
                      <Check className="w-3.5 h-3.5 text-ssk-success" />
                    ) : (
                      <Copy className="w-3.5 h-3.5 text-ssk-text-secondary" />
                    )}
                  </motion.button>
                ))}
              </div>
            </div>
          </div>
        </ScrollReveal>
      )}

      {/* Shop by Category */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">Shop by Category</h2>
              <p className="text-xs sm:text-sm text-ssk-text-secondary mt-1">Curated jewellery and accessories for every occasion</p>
            </div>
            <Link to="/shop" className="text-xs font-bold text-ssk-navy hover:text-ssk-gold flex items-center gap-1 group">
              <span>View All</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </ScrollReveal>

        <StaggerContainer className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-4 sm:gap-6">
          {categories.map((cat) => (
            <motion.div
              key={cat.id}
              variants={fadeUp}
              whileHover={{ y: -6 }}
              transition={{ duration: 0.2 }}
            >
              <Link
                to={`/shop?category=${encodeURIComponent(cat.name)}`}
                className="group flex flex-col items-center bg-white rounded-2xl p-4 border border-ssk-border hover:border-ssk-gold shadow-sm hover:shadow-lg transition-all duration-300 h-full"
              >
                <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-full overflow-hidden bg-ssk-surface mb-3 border-2 border-ssk-border group-hover:border-ssk-gold transition-colors">
                  <img
                    src={cat.image_url || '/logo.svg'}
                    alt={cat.name}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                </div>
                <h3 className="text-xs sm:text-sm font-semibold text-ssk-text group-hover:text-ssk-navy text-center line-clamp-1">
                  {cat.name}
                </h3>
                <span className="text-[10px] text-ssk-text-secondary uppercase mt-0.5">{cat.parent_category || 'Collection'}</span>
              </Link>
            </motion.div>
          ))}
        </StaggerContainer>
      </section>

      {/* Featured Collections / Bestsellers */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="flex items-center gap-2 text-ssk-gold text-xs font-bold uppercase tracking-wider mb-1">
                <Sparkles className="w-4 h-4" />
                <span>Customer Favorites</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">Best Selling Jewellery</h2>
            </div>
            <Link to="/shop?sort_by=popularity" className="text-xs font-bold text-ssk-navy hover:text-ssk-gold flex items-center gap-1 group">
              <span>See More</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </ScrollReveal>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {bestsellerProducts.slice(0, 4).map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onQuickView={(p) => setQuickViewProduct(p)}
            />
          ))}
        </StaggerContainer>
      </section>

      {/* 1-Gram Gold Highlight Banner */}
      <ScrollReveal variants={scaleIn} className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-gradient-to-r from-[#082B55] to-[#123F7A] text-white rounded-3xl p-8 sm:p-12 relative overflow-hidden shadow-xl border-2 border-ssk-gold/40">
          <div className="relative z-10 max-w-2xl space-y-4">
            <span className="text-xs font-bold text-ssk-gold-light uppercase tracking-widest px-3 py-1 bg-white/10 rounded-full border border-ssk-gold/30">
              Heritage Craftsmanship
            </span>
            <h2 className="text-2xl sm:text-4xl font-serif font-bold leading-tight">
              The Beauty of Real Gold, <br />
              Without the Extravagant Price.
            </h2>
            <p className="text-xs sm:text-sm text-gray-200 leading-relaxed">
              Our 1-gram gold tone pieces use multi-layer micron plating over durable brass alloys to achieve
              the exact luster, weight, and intricate detail of 22k bridal jewellery. Ideal for destination weddings,
              family ceremonies, and festival pujas.
            </p>
            <div className="pt-2">
              <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="inline-block">
                <Link
                  to="/shop?jewelry_type=1-Gram+Gold+Finish"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-ssk-gold hover:bg-ssk-gold-light text-white font-bold text-xs rounded-xl shadow-md transition-all"
                >
                  <span>Browse 1-Gram Gold Pieces</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </motion.div>
            </div>
          </div>
          <div className="hidden lg:block absolute right-8 top-1/2 -translate-y-1/2 w-80 h-80 rounded-2xl overflow-hidden border-2 border-ssk-gold/40 shadow-2xl">
            <img
              src="https://images.unsplash.com/photo-1601121141461-9d6647bca1ed?auto=format&fit=crop&w=600&q=80"
              alt="1-Gram Gold Bridal"
              className="w-full h-full object-cover hover:scale-105 transition-transform duration-700"
            />
          </div>
        </div>
      </ScrollReveal>

      {/* Trending Accessories Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal>
          <div className="flex items-center justify-between mb-8">
            <div>
              <div className="flex items-center gap-2 text-ssk-gold text-xs font-bold uppercase tracking-wider mb-1">
                <Gem className="w-4 h-4" />
                <span>Chic Hair & Women's Accessories</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">Trending Accessories</h2>
            </div>
            <Link to="/shop?category=Claw+Clips" className="text-xs font-bold text-ssk-navy hover:text-ssk-gold flex items-center gap-1 group">
              <span>Explore All</span>
              <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </ScrollReveal>

        <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {trendingProducts.slice(0, 4).map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              onQuickView={(p) => setQuickViewProduct(p)}
            />
          ))}
        </StaggerContainer>
      </section>

      {/* Verified Customer Reviews Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <ScrollReveal>
          <div className="text-center max-w-xl mx-auto mb-10">
            <h2 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">Loved by Brides & Jewellery Lovers</h2>
            <p className="text-xs sm:text-sm text-ssk-text-secondary mt-1">Real experiences from our customers across Hyderabad, Bangalore, and across India.</p>
          </div>
        </ScrollReveal>

        <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <motion.div variants={fadeUp} whileHover={{ y: -4 }} className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm flex flex-col justify-between transition-shadow hover:shadow-md">
            <div className="space-y-3">
              <div className="flex text-amber-400">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="w-4 h-4 fill-amber-400" />
                ))}
              </div>
              <h4 className="text-sm font-bold text-ssk-navy font-serif">"Looks exactly like 22k pure gold!"</h4>
              <p className="text-xs text-ssk-text-secondary leading-relaxed">
                "Ordered the Royal Lakshmi Choker Set for my sister's engagement. The weight and micro gold finish are incredible. Everyone assumed it came straight from our family goldsmith!"
              </p>
            </div>
            <div className="pt-4 border-t border-ssk-border mt-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-ssk-text">Ananya Reddy</p>
                <p className="text-[10px] text-ssk-text-secondary">Secunderabad • Verified Buyer</p>
              </div>
              <ShieldCheck className="w-4 h-4 text-ssk-success" />
            </div>
          </motion.div>

          <motion.div variants={fadeUp} whileHover={{ y: -4 }} className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm flex flex-col justify-between transition-shadow hover:shadow-md">
            <div className="space-y-3">
              <div className="flex text-amber-400">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="w-4 h-4 fill-amber-400" />
                ))}
              </div>
              <h4 className="text-sm font-bold text-ssk-navy font-serif">"Lightweight jhumkas, zero ear pain"</h4>
              <p className="text-xs text-ssk-text-secondary leading-relaxed">
                "Antique peacock jhumkas usually stretch my earlobes, but SSK made these hollow and so light. Wore them for 8 hours without irritation. Delivery to Bangalore was under 3 days."
              </p>
            </div>
            <div className="pt-4 border-t border-ssk-border mt-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-ssk-text">Kavitha M.</p>
                <p className="text-[10px] text-ssk-text-secondary">Bengaluru • Verified Buyer</p>
              </div>
              <ShieldCheck className="w-4 h-4 text-ssk-success" />
            </div>
          </motion.div>

          <motion.div variants={fadeUp} whileHover={{ y: -4 }} className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm flex flex-col justify-between transition-shadow hover:shadow-md">
            <div className="space-y-3">
              <div className="flex text-amber-400">
                {[1, 2, 3, 4, 5].map((s) => (
                  <Star key={s} className="w-4 h-4 fill-amber-400" />
                ))}
              </div>
              <h4 className="text-sm font-bold text-ssk-navy font-serif">"Pure mulberry silk scrunchies"</h4>
              <p className="text-xs text-ssk-text-secondary leading-relaxed">
                "The claw clips and mulberry silk scrunchies in Royal Navy are top notch. Hair has zero crease marks and the grip lasts the entire workday. Excellent packaging too."
              </p>
            </div>
            <div className="pt-4 border-t border-ssk-border mt-4 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-ssk-text">Divya S.</p>
                <p className="text-[10px] text-ssk-text-secondary">Chennai • Verified Buyer</p>
              </div>
              <ShieldCheck className="w-4 h-4 text-ssk-success" />
            </div>
          </motion.div>
        </StaggerContainer>
      </section>

      {/* Quick View Modal */}
      <QuickViewModal
        product={quickViewProduct}
        onClose={() => setQuickViewProduct(null)}
      />
    </div>
  );
};
