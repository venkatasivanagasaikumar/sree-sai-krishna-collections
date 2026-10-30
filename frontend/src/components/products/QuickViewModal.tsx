import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Star, ShoppingBag, Heart, ShieldCheck, Truck, RefreshCw } from 'lucide-react';
import { Product } from '../../types';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';
import { modalOverlay, modalContent } from '../../animations';

interface QuickViewModalProps {
  product: Product | null;
  onClose: () => void;
}

export const QuickViewModal: React.FC<QuickViewModalProps> = ({ product, onClose }) => {
  const { addToCart } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const [selectedImage, setSelectedImage] = useState<string>('');
  const [quantity, setQuantity] = useState(1);
  const [selectedVariant, setSelectedVariant] = useState<string>('');
  const [isAdding, setIsAdding] = useState(false);

  const currentImg = selectedImage || product?.images[0] || '/logo.svg';
  const isLiked = product ? isInWishlist(product.id) : false;

  const handleAdd = async () => {
    if (!product) return;
    setIsAdding(true);
    try {
      await addToCart(product.id, quantity, selectedVariant || undefined);
      onClose();
    } finally {
      setIsAdding(false);
    }
  };

  return (
    <AnimatePresence>
      {product && (
        <motion.div
          variants={modalOverlay}
          initial="hidden"
          animate="visible"
          exit="exit"
          onClick={onClose}
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            variants={modalContent}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-3xl max-w-3xl w-full overflow-hidden shadow-2xl relative border border-ssk-border max-h-[90vh] flex flex-col md:flex-row"
          >
            {/* Close Button */}
            <motion.button
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              onClick={onClose}
              className="absolute top-4 right-4 z-20 p-2 rounded-full bg-white/80 hover:bg-white text-ssk-text hover:text-black shadow-md transition-colors"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </motion.button>

            {/* Left: Images */}
            <div className="md:w-1/2 p-6 flex flex-col justify-between bg-ssk-surface">
              <div className="aspect-square w-full rounded-2xl overflow-hidden bg-white border border-ssk-border mb-4">
                <motion.img
                  key={currentImg}
                  initial={{ opacity: 0, scale: 0.98 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.25 }}
                  src={currentImg}
                  alt={product.name}
                  className="w-full h-full object-cover"
                />
              </div>
              {product.images.length > 1 && (
                <div className="flex gap-2 overflow-x-auto pb-1">
                  {product.images.map((img, i) => (
                    <motion.button
                      key={i}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => setSelectedImage(img)}
                      className={`w-14 h-14 rounded-xl overflow-hidden border-2 flex-shrink-0 transition-all ${
                        currentImg === img ? 'border-ssk-gold ring-2 ring-ssk-gold/30' : 'border-transparent opacity-70 hover:opacity-100'
                      }`}
                    >
                      <img src={img} alt="thumbnail" className="w-full h-full object-cover" />
                    </motion.button>
                  ))}
                </div>
              )}
            </div>

            {/* Right: Info & Actions */}
            <div className="md:w-1/2 p-6 overflow-y-auto flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-bold text-ssk-gold uppercase tracking-wider px-2 py-0.5 bg-ssk-gold/10 rounded-full">
                    {product.jewelry_type}
                  </span>
                  <span className="text-xs text-ssk-text-secondary font-mono">SKU: {product.sku}</span>
                </div>

                <h2 className="text-lg font-bold text-ssk-text leading-snug mb-2 font-serif">{product.name}</h2>

                {/* Rating */}
                <div className="flex items-center gap-2 mb-3">
                  <div className="flex text-amber-400">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-3.5 h-3.5 fill-amber-400" />
                    ))}
                  </div>
                  <span className="text-xs font-bold text-ssk-navy">{product.rating?.toFixed(1) || '5.0'}</span>
                  <span className="text-xs text-ssk-text-secondary">({product.rating_count || 12} reviews)</span>
                </div>

                {/* Price */}
                <div className="flex items-baseline gap-2 mb-4">
                  <span className="text-2xl font-bold text-ssk-navy">₹{product.price.toLocaleString('en-IN')}</span>
                  {product.mrp > product.price && (
                    <span className="text-sm text-ssk-text-secondary line-through">₹{product.mrp.toLocaleString('en-IN')}</span>
                  )}
                  {product.discount_percent && product.discount_percent > 0 && (
                    <span className="text-xs font-bold text-ssk-success">Save {product.discount_percent}%</span>
                  )}
                </div>

                {/* Materials & Care */}
                <div className="p-3 bg-ssk-blue-light/60 rounded-xl mb-4 text-xs text-ssk-text space-y-1 border border-ssk-border">
                  <p><strong>Material:</strong> {product.materials_and_finish}</p>
                  <p className="text-[11px] text-ssk-text-secondary">{product.genuine_gold_disclaimer}</p>
                </div>

                {/* Variants if any */}
                {product.variants && product.variants.length > 0 && (
                  <div className="mb-4">
                    <label className="block text-xs font-semibold text-ssk-text mb-2">Choose Variant:</label>
                    <div className="flex flex-wrap gap-2">
                      {product.variants.map((v) => (
                        <motion.button
                          key={v.variant_id}
                          whileHover={{ scale: 1.03 }}
                          whileTap={{ scale: 0.97 }}
                          onClick={() => setSelectedVariant(v.variant_id)}
                          className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                            selectedVariant === v.variant_id
                              ? 'border-ssk-navy bg-ssk-navy text-white shadow-sm'
                              : 'border-ssk-border bg-white text-ssk-text hover:border-ssk-navy'
                          }`}
                        >
                          {v.name} (₹{v.price})
                        </motion.button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quantity */}
                <div className="flex items-center gap-4 mb-6">
                  <label className="text-xs font-semibold text-ssk-text">Qty:</label>
                  <div className="flex items-center border border-ssk-border rounded-xl overflow-hidden bg-white">
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setQuantity(Math.max(1, quantity - 1))}
                      className="px-3 py-1.5 hover:bg-gray-100 text-sm font-bold"
                    >
                      -
                    </motion.button>
                    <span className="px-4 py-1.5 text-xs font-bold">{quantity}</span>
                    <motion.button
                      whileTap={{ scale: 0.9 }}
                      onClick={() => setQuantity(quantity + 1)}
                      className="px-3 py-1.5 hover:bg-gray-100 text-sm font-bold"
                    >
                      +
                    </motion.button>
                  </div>
                  <span className="text-xs text-ssk-success font-medium">In Stock ({product.stock} available)</span>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center gap-3">
                <motion.button
                  whileTap={{ scale: 0.97 }}
                  onClick={handleAdd}
                  disabled={isAdding || product.stock <= 0}
                  className="flex-1 py-3 bg-ssk-navy text-white font-bold text-xs rounded-xl hover:bg-ssk-navy-dark shadow-md flex items-center justify-center gap-2 transition-colors"
                >
                  <ShoppingBag className="w-4 h-4" />
                  {isAdding ? 'Adding...' : 'Add to Bag'}
                </motion.button>
                <motion.button
                  whileTap={{ scale: 0.9 }}
                  onClick={() => toggleWishlist(product)}
                  className={`p-3 rounded-xl border transition-colors ${
                    isLiked ? 'border-red-200 bg-red-50 text-red-500' : 'border-ssk-border hover:bg-gray-50 text-ssk-text'
                  }`}
                  aria-label="Toggle Wishlist"
                >
                  <Heart className={`w-4 h-4 ${isLiked ? 'fill-red-500' : ''}`} />
                </motion.button>
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
