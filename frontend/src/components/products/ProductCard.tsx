import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Heart, ShoppingBag, Eye, Star } from 'lucide-react';
import { Product } from '../../types';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';

interface ProductCardProps {
  product: Product;
  onQuickView?: (product: Product) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({ product, onQuickView }) => {
  const navigate = useNavigate();
  const { addToCart, isLoading } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();
  const [isHovered, setIsHovered] = useState(false);
  const [isAdding, setIsAdding] = useState(false);

  const isLiked = isInWishlist(product.id);
  const primaryImage = product.images[0] || '/logo.svg';
  const secondaryImage = product.images[1] || primaryImage;

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsAdding(true);
    try {
      await addToCart(product.id, 1);
    } finally {
      setIsAdding(false);
    }
  };

  const handleWishlist = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    toggleWishlist(product);
  };

  const handleQuickViewClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (onQuickView) onQuickView(product);
  };

  const isOutOfStock = product.stock <= 0;

  return (
    <div
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group bg-white rounded-2xl border border-ssk-border hover:border-ssk-gold/50 shadow-sm hover:shadow-xl transition-all duration-300 flex flex-col overflow-hidden relative"
    >
      {/* Product Image Container */}
      <div className="relative aspect-square w-full overflow-hidden bg-ssk-surface">
        <Link to={`/product/${product.sku}`}>
          <img
            src={isHovered ? secondaryImage : primaryImage}
            alt={product.name}
            className="w-full h-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
            loading="lazy"
          />
        </Link>

        {/* Badges */}
        <div className="absolute top-2.5 left-2.5 flex flex-col gap-1.5 z-10">
          {product.discount_percent && product.discount_percent > 0 && (
            <span className="bg-ssk-gold text-white font-bold text-[10px] tracking-wider px-2 py-0.5 rounded-full shadow-sm">
              {product.discount_percent}% OFF
            </span>
          )}
          {product.is_bestseller && (
            <span className="bg-ssk-navy text-white font-semibold text-[10px] tracking-wider px-2 py-0.5 rounded-full shadow-sm">
              BESTSELLER
            </span>
          )}
          {isOutOfStock && (
            <span className="bg-red-600 text-white font-bold text-[10px] tracking-wider px-2 py-0.5 rounded-full shadow-sm">
              SOLD OUT
            </span>
          )}
        </div>

        {/* Wishlist Button */}
        <button
          onClick={handleWishlist}
          className={`absolute top-2.5 right-2.5 w-8 h-8 rounded-full flex items-center justify-center transition-all duration-200 z-10 shadow-sm ${
            isLiked
              ? 'bg-red-50 text-red-500 hover:bg-red-100'
              : 'bg-white/80 backdrop-blur-sm text-ssk-text hover:bg-white hover:text-red-500'
          }`}
          title={isLiked ? 'Remove from wishlist' : 'Add to wishlist'}
        >
          <Heart className={`w-4 h-4 ${isLiked ? 'fill-red-500' : ''}`} />
        </button>

        {/* Quick View Button on Hover */}
        {onQuickView && (
          <button
            onClick={handleQuickViewClick}
            className="hidden md:flex absolute bottom-3 left-1/2 -translate-x-1/2 items-center gap-1.5 px-3 py-1.5 bg-white/95 backdrop-blur-sm text-ssk-navy text-xs font-semibold rounded-full shadow-md hover:bg-ssk-navy hover:text-white transition-all opacity-0 group-hover:opacity-100 duration-200 z-10"
          >
            <Eye className="w-3.5 h-3.5" />
            Quick View
          </button>
        )}
      </div>

      {/* Product Info */}
      <div className="p-4 flex-1 flex flex-col justify-between">
        <div>
          {/* Category / Type Tag */}
          <div className="flex items-center justify-between gap-2 mb-1.5">
            <span className="text-[10px] font-semibold text-ssk-text-secondary uppercase tracking-wider truncate">
              {product.jewelry_type || product.category}
            </span>
            {product.rating && (
              <div className="flex items-center gap-1 text-[11px] font-bold text-ssk-navy">
                <Star className="w-3 h-3 text-amber-400 fill-amber-400" />
                <span>{product.rating.toFixed(1)}</span>
                {product.rating_count ? (
                  <span className="text-ssk-text-secondary text-[10px] font-normal">({product.rating_count})</span>
                ) : null}
              </div>
            )}
          </div>

          {/* Product Name */}
          <Link
            to={`/product/${product.sku}`}
            className="block text-xs sm:text-sm font-semibold text-ssk-text hover:text-ssk-navy line-clamp-2 transition-colors mb-2 leading-snug"
            title={product.name}
          >
            {product.name}
          </Link>
        </div>

        <div>
          {/* Price & MRP */}
          <div className="flex items-baseline gap-2 mb-3">
            <span className="text-base sm:text-lg font-bold text-ssk-navy">
              ₹{product.price.toLocaleString('en-IN')}
            </span>
            {product.mrp > product.price && (
              <span className="text-xs text-ssk-text-secondary line-through">
                ₹{product.mrp.toLocaleString('en-IN')}
              </span>
            )}
            {product.discount_percent && product.discount_percent > 0 && (
              <span className="text-[10px] font-bold text-ssk-success">
                ({product.discount_percent}% off)
              </span>
            )}
          </div>

          {/* Add to Bag Button */}
          <button
            onClick={handleAddToCart}
            disabled={isOutOfStock || isAdding}
            className={`w-full py-2.5 px-4 rounded-xl text-xs font-bold tracking-wide flex items-center justify-center gap-2 transition-all duration-200 ${
              isOutOfStock
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-ssk-navy text-white hover:bg-ssk-navy-dark active:scale-[0.98] shadow-sm hover:shadow'
            }`}
          >
            <ShoppingBag className="w-3.5 h-3.5" />
            {isAdding ? 'Adding...' : isOutOfStock ? 'Out of Stock' : 'Add to Bag'}
          </button>
        </div>
      </div>
    </div>
  );
};
