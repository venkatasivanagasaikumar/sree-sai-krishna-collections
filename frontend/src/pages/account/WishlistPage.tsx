import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Heart, ArrowRight } from 'lucide-react';
import { useWishlist } from '../../context/WishlistContext';
import { ProductCard } from '../../components/products/ProductCard';
import { PageTransition } from '../../components/animations/PageTransition';
import { StaggerContainer } from '../../components/animations/StaggerContainer';

export const WishlistPage: React.FC = () => {
  const { wishlist, wishlistCount } = useWishlist();

  if (wishlistCount === 0) {
    return (
      <PageTransition className="max-w-2xl mx-auto text-center py-24 px-4">
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="w-16 h-16 bg-red-50 text-red-400 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <Heart className="w-8 h-8" />
        </motion.div>
        <h2 className="text-2xl font-serif font-bold text-ssk-navy mb-2">Your Wishlist is Empty</h2>
        <p className="text-xs sm:text-sm text-ssk-text-secondary max-w-sm mx-auto mb-6">
          Save your favorite temple chokers, kada bangles, and hair accessories here to purchase later.
        </p>
        <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }} className="inline-block">
          <Link
            to="/shop"
            className="inline-flex items-center gap-2 px-8 py-3.5 bg-ssk-navy text-white text-xs font-bold rounded-xl shadow-md transition-colors hover:bg-ssk-navy-dark"
          >
            <span>Explore Jewellery</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        </motion.div>
      </PageTransition>
    );
  }

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="flex items-center justify-between pb-4 border-b border-ssk-border">
        <h1 className="text-2xl font-serif font-bold text-ssk-navy">
          My Saved Wishlist ({wishlistCount} items)
        </h1>
        <Link to="/shop" className="text-xs font-bold text-ssk-navy hover:text-ssk-gold transition-colors">
          + Add more items
        </Link>
      </div>

      <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {wishlist.map((item) => (
          <ProductCard key={item.id} product={item} />
        ))}
      </StaggerContainer>
    </PageTransition>
  );
};
