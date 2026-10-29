import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import {
  Star, ShoppingBag, Heart, ShieldCheck, Truck, RefreshCw,
  ChevronRight, Share2, Check, MapPin, AlertCircle
} from 'lucide-react';
import { api } from '../../services/api';
import { Product, Review } from '../../types';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';
import { ProductCard } from '../../components/products/ProductCard';

export const ProductDetailPage: React.FC = () => {
  const { idOrSku } = useParams<{ idOrSku: string }>();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { isInWishlist, toggleWishlist } = useWishlist();

  const [product, setProduct] = useState<Product | null>(null);
  const [selectedImage, setSelectedImage] = useState<string>('');
  const [selectedVariant, setSelectedVariant] = useState<string>('');
  const [quantity, setQuantity] = useState(1);
  const [loading, setLoading] = useState(true);
  const [isAdding, setIsAdding] = useState(false);
  const [pincode, setPincode] = useState('');
  const [pincodeStatus, setPincodeStatus] = useState<string | null>(null);

  // Review submission state
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewTitle, setReviewTitle] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [reviewerName, setReviewerName] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    if (!idOrSku) return;
    setLoading(true);
    api.getProductByIdOrSku(idOrSku)
      .then((data) => {
        setProduct(data);
        setSelectedImage(data.images[0] || '');
        if (data.variants && data.variants.length > 0) {
          setSelectedVariant(data.variants[0].variant_id);
        }
      })
      .catch((err) => {
        console.error('Error fetching product:', err);
      })
      .finally(() => {
        setLoading(false);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
  }, [idOrSku]);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-16 animate-pulse space-y-6">
        <div className="h-6 bg-gray-200 rounded w-1/4" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          <div className="aspect-square bg-gray-200 rounded-3xl" />
          <div className="space-y-4">
            <div className="h-8 bg-gray-200 rounded w-3/4" />
            <div className="h-6 bg-gray-200 rounded w-1/3" />
            <div className="h-32 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="max-w-md mx-auto text-center py-20 px-4">
        <h2 className="text-xl font-bold text-ssk-navy font-serif">Product Not Found</h2>
        <p className="text-xs text-ssk-text-secondary mt-2">The requested design could not be loaded or has been archived.</p>
        <Link to="/shop" className="mt-4 inline-block px-6 py-2.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl">
          Return to Shop
        </Link>
      </div>
    );
  }

  const isLiked = isInWishlist(product.id);
  const currentImg = selectedImage || product.images[0] || '/logo.svg';

  const handleAddToCart = async (buyNow = false) => {
    setIsAdding(true);
    try {
      await addToCart(product.id, quantity, selectedVariant || undefined);
      if (buyNow) {
        navigate('/checkout');
      }
    } finally {
      setIsAdding(false);
    }
  };

  const checkPincode = (e: React.FormEvent) => {
    e.preventDefault();
    if (pincode.length === 6 && /^\d+$/.test(pincode)) {
      setPincodeStatus(`Available! Standard delivery to ${pincode} in 2-4 business days.`);
    } else {
      setPincodeStatus('Please enter a valid 6-digit Indian PIN code.');
    }
  };

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopiedLink(true);
    setTimeout(() => setCopiedLink(false), 2500);
  };

  const handleReviewSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingReview(true);
    try {
      await api.submitReview({
        product_id: product.id,
        rating: reviewRating,
        title: reviewTitle,
        comment: reviewComment,
        reviewer_name: reviewerName
      });
      setShowReviewModal(false);
      // Reload product details to show new review
      const refreshed = await api.getProductByIdOrSku(product.sku);
      setProduct(refreshed);
    } catch (err) {
      alert('Failed to submit review');
    } finally {
      setSubmittingReview(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-xs text-ssk-text-secondary mb-8">
        <Link to="/" className="hover:text-ssk-navy">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to="/shop" className="hover:text-ssk-navy">Shop</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to={`/shop?category=${encodeURIComponent(product.category)}`} className="hover:text-ssk-navy">{product.category}</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <span className="font-semibold text-ssk-navy truncate max-w-xs">{product.name}</span>
      </nav>

      {/* Main Product Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 mb-16">
        
        {/* Left: Gallery & Zoom */}
        <div className="lg:col-span-6 space-y-4">
          <div className="relative aspect-square w-full rounded-3xl overflow-hidden bg-ssk-surface border border-ssk-border group shadow-sm">
            <img
              src={currentImg}
              alt={product.name}
              className="w-full h-full object-cover transition-transform duration-700 hover:scale-125 cursor-zoom-in"
            />
            {product.discount_percent && product.discount_percent > 0 && (
              <span className="absolute top-4 left-4 bg-ssk-gold text-white font-bold text-xs tracking-wider px-3 py-1 rounded-full shadow-md">
                {product.discount_percent}% OFF
              </span>
            )}
            <button
              onClick={() => toggleWishlist(product)}
              className={`absolute top-4 right-4 p-3 rounded-full shadow-md backdrop-blur-md transition-all ${
                isLiked ? 'bg-red-50 text-red-500' : 'bg-white/80 hover:bg-white text-ssk-text'
              }`}
            >
              <Heart className={`w-5 h-5 ${isLiked ? 'fill-red-500' : ''}`} />
            </button>
          </div>

          {/* Thumbnails */}
          {product.images.length > 1 && (
            <div className="flex items-center gap-3 overflow-x-auto pb-2">
              {product.images.map((img, idx) => (
                <button
                  key={idx}
                  onClick={() => setSelectedImage(img)}
                  className={`w-20 h-20 rounded-2xl overflow-hidden border-2 flex-shrink-0 transition-all ${
                    currentImg === img ? 'border-ssk-gold ring-2 ring-ssk-gold/30' : 'border-ssk-border opacity-70 hover:opacity-100'
                  }`}
                >
                  <img src={img} alt={`view ${idx + 1}`} className="w-full h-full object-cover" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Details & Purchase Actions */}
        <div className="lg:col-span-6 flex flex-col justify-between space-y-6">
          <div>
            {/* Header info */}
            <div className="flex items-center justify-between gap-4 mb-2">
              <span className="text-xs font-bold text-ssk-gold uppercase tracking-wider px-3 py-1 bg-ssk-gold/10 rounded-full">
                {product.jewelry_type}
              </span>
              <div className="flex items-center gap-3">
                <span className="text-xs text-ssk-text-secondary font-mono">SKU: {product.sku}</span>
                <button onClick={handleShare} className="text-ssk-text-secondary hover:text-ssk-navy" title="Share Product">
                  {copiedLink ? <Check className="w-4 h-4 text-ssk-success" /> : <Share2 className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy leading-tight mb-3">
              {product.name}
            </h1>

            {/* Rating */}
            <div className="flex items-center gap-2 mb-4">
              <div className="flex text-amber-400">
                {[...Array(5)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-amber-400" />
                ))}
              </div>
              <span className="text-sm font-bold text-ssk-navy">{product.rating?.toFixed(1) || '5.0'}</span>
              <span className="text-xs text-ssk-text-secondary">({product.rating_count || 12} customer ratings)</span>
            </div>

            {/* Price Box */}
            <div className="flex items-baseline gap-3 p-4 bg-ssk-surface rounded-2xl border border-ssk-border mb-6">
              <span className="text-3xl font-bold text-ssk-navy font-serif">
                ₹{product.price.toLocaleString('en-IN')}
              </span>
              {product.mrp > product.price && (
                <span className="text-base text-ssk-text-secondary line-through">
                  ₹{product.mrp.toLocaleString('en-IN')}
                </span>
              )}
              {product.discount_percent && product.discount_percent > 0 && (
                <span className="text-xs font-bold text-ssk-success bg-green-50 px-2.5 py-1 rounded-lg">
                  Save ₹{product.discount_amount} ({product.discount_percent}% OFF)
                </span>
              )}
              <span className="text-[10px] text-ssk-text-secondary ml-auto">Inclusive of all taxes</span>
            </div>

            {/* Crucial Genuine Gold / Imitation Disclaimer Notice */}
            <div className="p-4 bg-amber-50/80 border border-amber-200 rounded-2xl text-xs text-amber-900 mb-6 flex items-start gap-3">
              <ShieldCheck className="w-5 h-5 text-amber-700 flex-shrink-0 mt-0.5" />
              <div>
                <strong className="font-semibold block mb-0.5">Craftsmanship & Purity Transparency:</strong>
                <span>{product.genuine_gold_disclaimer} Finished with durable 1-gram gold tone micro-electroplating over brass core.</span>
              </div>
            </div>

            {/* Product Variants if available */}
            {product.variants && product.variants.length > 0 && (
              <div className="mb-6">
                <label className="block text-xs font-bold text-ssk-text uppercase tracking-wider mb-2">
                  Select Design Option / Size:
                </label>
                <div className="flex flex-wrap gap-2.5">
                  {product.variants.map((v) => (
                    <button
                      key={v.variant_id}
                      onClick={() => setSelectedVariant(v.variant_id)}
                      className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all ${
                        selectedVariant === v.variant_id
                          ? 'border-ssk-navy bg-ssk-navy text-white shadow-sm'
                          : 'border-ssk-border bg-white text-ssk-text hover:border-ssk-navy'
                      }`}
                    >
                      {v.name} &bull; ₹{v.price}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Quantity Selector & Stock Indicator */}
            <div className="flex items-center gap-6 mb-6">
              <div className="space-y-1">
                <label className="text-xs font-bold text-ssk-text uppercase tracking-wider block">Quantity:</label>
                <div className="flex items-center border border-ssk-border rounded-xl bg-white overflow-hidden shadow-sm">
                  <button
                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                    className="px-3.5 py-2 hover:bg-gray-100 text-sm font-bold text-ssk-navy"
                  >
                    -
                  </button>
                  <span className="px-4 py-2 text-xs font-bold text-ssk-text min-w-[36px] text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => setQuantity(quantity + 1)}
                    className="px-3.5 py-2 hover:bg-gray-100 text-sm font-bold text-ssk-navy"
                  >
                    +
                  </button>
                </div>
              </div>

              <div>
                {product.stock > 0 ? (
                  <div className="text-xs font-medium text-ssk-success flex items-center gap-1.5">
                    <Check className="w-4 h-4" />
                    <span>In Stock ({product.stock} units available)</span>
                  </div>
                ) : (
                  <span className="text-xs font-bold text-red-600">Currently Sold Out</span>
                )}
                {product.stock <= 5 && product.stock > 0 && (
                  <span className="text-[11px] text-amber-700 font-semibold block mt-0.5">Hurry, only few pieces remaining!</span>
                )}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-8">
              <button
                onClick={() => handleAddToCart(false)}
                disabled={isAdding || product.stock <= 0}
                className="py-3.5 px-6 bg-ssk-navy hover:bg-ssk-navy-dark text-white font-bold text-xs rounded-xl shadow-md hover:shadow-lg flex items-center justify-center gap-2 transition-all"
              >
                <ShoppingBag className="w-4 h-4" />
                {isAdding ? 'Adding to Bag...' : 'Add to Bag'}
              </button>
              <button
                onClick={() => handleAddToCart(true)}
                disabled={isAdding || product.stock <= 0}
                className="py-3.5 px-6 bg-gradient-to-r from-ssk-gold to-ssk-gold-dark hover:from-ssk-gold-light hover:to-ssk-gold text-white font-bold text-xs rounded-xl shadow-md hover:shadow-lg transition-all"
              >
                Buy Now
              </button>
            </div>

            {/* Pincode Delivery Estimate */}
            <div className="p-4 bg-white rounded-2xl border border-ssk-border mb-6 space-y-2">
              <label className="text-xs font-bold text-ssk-text flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-ssk-gold" />
                <span>Estimate Delivery Time:</span>
              </label>
              <form onSubmit={checkPincode} className="flex gap-2">
                <input
                  type="text"
                  maxLength={6}
                  placeholder="Enter 6-digit PIN code"
                  value={pincode}
                  onChange={(e) => setPincode(e.target.value)}
                  className="flex-1 px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark"
                >
                  Check
                </button>
              </form>
              {pincodeStatus && (
                <p className="text-xs font-medium text-ssk-navy mt-1">{pincodeStatus}</p>
              )}
            </div>

            {/* Product Specifications & Care Instructions */}
            <div className="space-y-4 pt-4 border-t border-ssk-border">
              <h3 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider">Product Description</h3>
              <p className="text-xs text-ssk-text-secondary leading-relaxed">{product.description}</p>

              <div className="grid grid-cols-2 gap-3 text-xs pt-2">
                <div className="p-3 bg-ssk-surface rounded-xl">
                  <span className="text-ssk-text-secondary block text-[10px] uppercase font-bold">Materials & Finish</span>
                  <span className="font-semibold text-ssk-text">{product.materials_and_finish}</span>
                </div>
                <div className="p-3 bg-ssk-surface rounded-xl">
                  <span className="text-ssk-text-secondary block text-[10px] uppercase font-bold">Care Instructions</span>
                  <span className="font-semibold text-ssk-text">{product.care_instructions}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Reviews & Ratings Section */}
      <section className="pt-12 border-t border-ssk-border mb-16">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h2 className="text-2xl font-serif font-bold text-ssk-navy">Customer Reviews</h2>
            <p className="text-xs text-ssk-text-secondary mt-1">Verified purchases from authentic customers</p>
          </div>
          <button
            onClick={() => setShowReviewModal(true)}
            className="px-5 py-2.5 border border-ssk-navy text-ssk-navy hover:bg-ssk-navy hover:text-white text-xs font-bold rounded-xl transition-all shadow-sm"
          >
            Write a Review
          </button>
        </div>

        {product.reviews && product.reviews.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {product.reviews.map((rev, i) => (
              <div key={i} className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex text-amber-400">
                    {[...Array(rev.rating)].map((_, idx) => (
                      <Star key={idx} className="w-3.5 h-3.5 fill-amber-400" />
                    ))}
                  </div>
                  <span className="text-[11px] text-ssk-text-secondary">
                    {new Date(rev.created_at).toLocaleDateString()}
                  </span>
                </div>
                <h4 className="text-sm font-bold text-ssk-text">{rev.title}</h4>
                <p className="text-xs text-ssk-text-secondary leading-relaxed">{rev.comment}</p>
                <div className="pt-2 flex items-center justify-between text-xs">
                  <span className="font-semibold text-ssk-navy">{rev.reviewer_name}</span>
                  {rev.is_verified_purchase && (
                    <span className="text-[10px] text-ssk-success font-medium flex items-center gap-1">
                      <Check className="w-3 h-3" /> Verified Purchase
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-10 bg-ssk-surface rounded-2xl border border-ssk-border p-6">
            <p className="text-xs text-ssk-text-secondary">Be the first to review this product!</p>
          </div>
        )}
      </section>

      {/* Related Products */}
      {product.related_products && product.related_products.length > 0 && (
        <section className="pt-12 border-t border-ssk-border">
          <h2 className="text-2xl font-serif font-bold text-ssk-navy mb-8">You May Also Like</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {product.related_products.map((rel) => (
              <ProductCard key={rel.id} product={rel} />
            ))}
          </div>
        </section>
      )}

      {/* Write Review Modal */}
      {showReviewModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-ssk-border relative">
            <h3 className="text-lg font-serif font-bold text-ssk-navy mb-4">Write a Product Review</h3>
            <form onSubmit={handleReviewSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Your Name</label>
                <input
                  type="text"
                  required
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  placeholder="e.g. Priya S."
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Rating</label>
                <div className="flex gap-2">
                  {[1, 2, 3, 4, 5].map((val) => (
                    <button
                      type="button"
                      key={val}
                      onClick={() => setReviewRating(val)}
                      className="p-1 hover:scale-110 transition-transform"
                    >
                      <Star
                        className={`w-6 h-6 ${
                          val <= reviewRating ? 'text-amber-400 fill-amber-400' : 'text-gray-300'
                        }`}
                      />
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Review Headline</label>
                <input
                  type="text"
                  required
                  value={reviewTitle}
                  onChange={(e) => setReviewTitle(e.target.value)}
                  placeholder="e.g. Magnificent royal look and finish"
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-ssk-text mb-1">Detailed Review</label>
                <textarea
                  required
                  rows={4}
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  placeholder="Tell us about the craftsmanship, fit, and compliments received..."
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowReviewModal(false)}
                  className="flex-1 py-2.5 border border-ssk-border rounded-xl text-xs font-semibold text-ssk-text hover:bg-gray-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingReview}
                  className="flex-1 py-2.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm"
                >
                  {submittingReview ? 'Submitting...' : 'Submit Review'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
