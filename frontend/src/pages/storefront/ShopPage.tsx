import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Filter, SlidersHorizontal, ChevronRight, X, Sparkles } from 'lucide-react';
import { ProductCard } from '../../components/products/ProductCard';
import { QuickViewModal } from '../../components/products/QuickViewModal';
import { api } from '../../services/api';
import { Product, Category } from '../../types';
import { PageTransition } from '../../components/animations/PageTransition';
import { StaggerContainer } from '../../components/animations/StaggerContainer';
import { FadeIn } from '../../components/animations/FadeIn';
import { fadeUp, scaleIn, slideInLeft, modalOverlay } from '../../animations';

export const ShopPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [quickViewProduct, setQuickViewProduct] = useState<Product | null>(null);
  const [showMobileFilter, setShowMobileFilter] = useState(false);

  // Filters from URL query params
  const currentCategory = searchParams.get('category') || '';
  const currentSearch = searchParams.get('search') || '';
  const currentJewelryType = searchParams.get('jewelry_type') || '';
  const currentSort = searchParams.get('sort_by') || 'recommended';
  const currentPage = parseInt(searchParams.get('page') || '1', 10);
  const inStockOnly = searchParams.get('in_stock_only') === 'true';

  useEffect(() => {
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  useEffect(() => {
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const res = await api.getProducts({
          category: currentCategory,
          search: currentSearch,
          jewelry_type: currentJewelryType,
          sort_by: currentSort,
          page: currentPage,
          in_stock_only: inStockOnly ? 'true' : undefined,
          limit: 12,
        });
        setProducts(res.products);
        setTotalCount(res.total);
        setTotalPages(res.pages);
      } catch (err) {
        console.error('Failed to fetch products:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentCategory, currentSearch, currentJewelryType, currentSort, currentPage, inStockOnly]);

  const updateFilter = (key: string, value: string | null) => {
    const next = new URLSearchParams(searchParams);
    if (value) {
      next.set(key, value);
    } else {
      next.delete(key);
    }
    next.set('page', '1'); // Reset to page 1 on filter change
    setSearchParams(next);
  };

  const clearAllFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const hasActiveFilters = !!(currentCategory || currentSearch || currentJewelryType || inStockOnly);

  return (
    <PageTransition className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-xs text-ssk-text-secondary mb-6">
        <Link to="/" className="hover:text-ssk-navy transition-colors">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to="/shop" className="hover:text-ssk-navy transition-colors">Shop</Link>
        {currentCategory && (
          <>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="font-semibold text-ssk-navy">{currentCategory}</span>
          </>
        )}
        {currentSearch && (
          <>
            <ChevronRight className="w-3.5 h-3.5" />
            <span className="font-semibold text-ssk-navy">"{currentSearch}"</span>
          </>
        )}
      </nav>

      {/* Header & Sort Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-ssk-border mb-8">
        <div>
          <h1 className="text-2xl sm:text-3xl font-serif font-bold text-ssk-navy">
            {currentCategory || (currentSearch ? `Search Results for "${currentSearch}"` : 'All Jewellery & Accessories')}
          </h1>
          <p className="text-xs text-ssk-text-secondary mt-1">Showing {products.length} of {totalCount} designs</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Mobile Filter Toggle */}
          <motion.button
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowMobileFilter(true)}
            className="lg:hidden flex items-center gap-2 px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold text-ssk-text hover:bg-ssk-blue-light transition-colors"
          >
            <SlidersHorizontal className="w-4 h-4 text-ssk-gold" />
            <span>Filters</span>
          </motion.button>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-ssk-text-secondary hidden sm:inline">Sort by:</span>
            <select
              value={currentSort}
              onChange={(e) => updateFilter('sort_by', e.target.value)}
              className="bg-white border border-ssk-border rounded-xl px-3 py-2 text-xs font-medium text-ssk-text focus:outline-none focus:border-ssk-gold shadow-sm transition-colors"
            >
              <option value="recommended">Recommended</option>
              <option value="newest">Newest Arrivals</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
              <option value="popularity">Most Popular</option>
              <option value="discount">Biggest Discount</option>
            </select>
          </div>
        </div>
      </div>

      {/* Active Filter Pills with AnimatePresence */}
      <AnimatePresence>
        {hasActiveFilters && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="flex flex-wrap items-center gap-2 mb-6 overflow-hidden"
          >
            <span className="text-xs text-ssk-text-secondary font-medium">Active filters:</span>
            {currentCategory && (
              <motion.span
                layout
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold"
              >
                Category: {currentCategory}
                <button onClick={() => updateFilter('category', null)} aria-label="Remove category filter">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.span>
            )}
            {currentJewelryType && (
              <motion.span
                layout
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold"
              >
                Type: {currentJewelryType}
                <button onClick={() => updateFilter('jewelry_type', null)} aria-label="Remove type filter">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.span>
            )}
            {currentSearch && (
              <motion.span
                layout
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold"
              >
                Search: "{currentSearch}"
                <button onClick={() => updateFilter('search', null)} aria-label="Remove search filter">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.span>
            )}
            {inStockOnly && (
              <motion.span
                layout
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.8, opacity: 0 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold"
              >
                In Stock Only
                <button onClick={() => updateFilter('in_stock_only', null)} aria-label="Remove in-stock filter">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.span>
            )}
            <motion.button
              whileHover={{ scale: 1.05 }}
              onClick={clearAllFilters}
              className="text-xs text-ssk-error font-semibold hover:underline ml-2"
            >
              Clear all
            </motion.button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Main Grid & Sidebar Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block space-y-6 bg-white p-6 rounded-2xl border border-ssk-border self-start sticky top-28 shadow-sm">
          <div>
            <h3 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider mb-3">
              Categories
            </h3>
            <ul className="space-y-1.5 text-xs text-ssk-text">
              <li>
                <button
                  onClick={() => updateFilter('category', null)}
                  className={`w-full text-left py-1.5 px-2.5 rounded-lg transition-colors ${
                    !currentCategory ? 'bg-ssk-navy text-white font-semibold' : 'hover:bg-ssk-blue-light'
                  }`}
                >
                  All Categories
                </button>
              </li>
              {categories.map((c) => (
                <li key={c.id}>
                  <button
                    onClick={() => updateFilter('category', c.name)}
                    className={`w-full text-left py-1.5 px-2.5 rounded-lg transition-colors ${
                      currentCategory === c.name ? 'bg-ssk-navy text-white font-semibold' : 'hover:bg-ssk-blue-light'
                    }`}
                  >
                    {c.name}
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="pt-6 border-t border-ssk-border">
            <h3 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider mb-3">
              Jewellery Type
            </h3>
            <div className="space-y-2 text-xs">
              {['1-Gram Gold Finish', 'Imitation Jewellery', 'Hair Accessory'].map((t) => (
                <label key={t} className="flex items-center gap-2 cursor-pointer text-ssk-text hover:text-ssk-navy transition-colors">
                  <input
                    type="radio"
                    name="jewelry_type"
                    checked={currentJewelryType === t}
                    onChange={() => updateFilter('jewelry_type', currentJewelryType === t ? null : t)}
                    className="accent-ssk-gold"
                  />
                  <span>{t}</span>
                </label>
              ))}
            </div>
          </div>

          <div className="pt-6 border-t border-ssk-border">
            <h3 className="text-sm font-serif font-bold text-ssk-navy uppercase tracking-wider mb-3">
              Availability
            </h3>
            <label className="flex items-center gap-2 cursor-pointer text-xs text-ssk-text hover:text-ssk-navy transition-colors">
              <input
                type="checkbox"
                checked={inStockOnly}
                onChange={(e) => updateFilter('in_stock_only', e.target.checked ? 'true' : null)}
                className="accent-ssk-navy rounded"
              />
              <span>In-stock items only</span>
            </label>
          </div>
        </aside>

        {/* Product Grid Area */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <motion.div
                  key={i}
                  animate={{ opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
                  className="bg-white rounded-2xl border border-ssk-border p-4 space-y-3"
                >
                  <div className="aspect-square bg-gray-200 rounded-xl" />
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-4 bg-gray-200 rounded w-1/2" />
                </motion.div>
              ))}
            </div>
          ) : products.length > 0 ? (
            <>
              <StaggerContainer className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {products.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onQuickView={(p) => setQuickViewProduct(p)}
                  />
                ))}
              </StaggerContainer>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-12">
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    disabled={currentPage <= 1}
                    onClick={() => updateFilter('page', String(currentPage - 1))}
                    className="px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold disabled:opacity-40 hover:bg-ssk-blue-light transition-colors"
                  >
                    Previous
                  </motion.button>
                  {[...Array(totalPages)].map((_, i) => (
                    <motion.button
                      key={i + 1}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => updateFilter('page', String(i + 1))}
                      className={`w-9 h-9 rounded-xl text-xs font-bold transition-all ${
                        currentPage === i + 1
                          ? 'bg-ssk-navy text-white shadow-sm'
                          : 'border border-ssk-border hover:bg-ssk-blue-light text-ssk-text'
                      }`}
                    >
                      {i + 1}
                    </motion.button>
                  ))}
                  <motion.button
                    whileTap={{ scale: 0.95 }}
                    disabled={currentPage >= totalPages}
                    onClick={() => updateFilter('page', String(currentPage + 1))}
                    className="px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold disabled:opacity-40 hover:bg-ssk-blue-light transition-colors"
                  >
                    Next
                  </motion.button>
                </div>
              )}
            </>
          ) : (
            <FadeIn direction="up" className="text-center py-16 bg-white rounded-2xl border border-ssk-border p-8">
              <Sparkles className="w-12 h-12 text-ssk-gold mx-auto mb-3" />
              <h3 className="text-lg font-bold text-ssk-navy font-serif">No jewellery found</h3>
              <p className="text-xs text-ssk-text-secondary mt-1 max-w-sm mx-auto">
                Try selecting a different category or clearing search filters to see all available designs.
              </p>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={clearAllFilters}
                className="mt-4 px-6 py-2.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm transition-colors"
              >
                Clear All Filters
              </motion.button>
            </FadeIn>
          )}
        </div>
      </div>

      {/* Mobile Filter Slide Drawer with AnimatePresence */}
      <AnimatePresence>
        {showMobileFilter && (
          <motion.div
            variants={modalOverlay}
            initial="hidden"
            animate="visible"
            exit="exit"
            onClick={() => setShowMobileFilter(false)}
            className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm lg:hidden"
          >
            <motion.div
              variants={slideInLeft}
              initial="hidden"
              animate="visible"
              exit="exit"
              onClick={(e) => e.stopPropagation()}
              className="w-4/5 max-w-xs h-full bg-white p-6 overflow-y-auto space-y-6 shadow-2xl"
            >
              <div className="flex items-center justify-between pb-4 border-b border-ssk-border">
                <h3 className="font-serif font-bold text-ssk-navy text-sm uppercase">Filters</h3>
                <button onClick={() => setShowMobileFilter(false)} aria-label="Close filters">
                  <X className="w-5 h-5 text-ssk-text" />
                </button>
              </div>

              <div>
                <h4 className="text-xs font-bold text-ssk-navy uppercase tracking-wider mb-2">Categories</h4>
                <div className="space-y-1">
                  <button
                    onClick={() => {
                      updateFilter('category', null);
                      setShowMobileFilter(false);
                    }}
                    className={`block w-full text-left py-1.5 px-2 text-xs rounded-lg ${
                      !currentCategory ? 'bg-ssk-navy text-white font-semibold' : 'text-ssk-text'
                    }`}
                  >
                    All Categories
                  </button>
                  {categories.map((c) => (
                    <button
                      key={c.id}
                      onClick={() => {
                        updateFilter('category', c.name);
                        setShowMobileFilter(false);
                      }}
                      className={`block w-full text-left py-1.5 px-2 text-xs rounded-lg ${
                        currentCategory === c.name ? 'bg-ssk-navy text-white font-semibold' : 'text-ssk-text'
                      }`}
                    >
                      {c.name}
                    </button>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-ssk-border">
                <h4 className="text-xs font-bold text-ssk-navy uppercase tracking-wider mb-2">Jewellery Type</h4>
                <div className="space-y-2 text-xs">
                  {['1-Gram Gold Finish', 'Imitation Jewellery', 'Hair Accessory'].map((t) => (
                    <label key={t} className="flex items-center gap-2">
                      <input
                        type="radio"
                        name="mobile_jewelry_type"
                        checked={currentJewelryType === t}
                        onChange={() => {
                          updateFilter('jewelry_type', currentJewelryType === t ? null : t);
                          setShowMobileFilter(false);
                        }}
                        className="accent-ssk-gold"
                      />
                      <span>{t}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="pt-4 border-t border-ssk-border">
                <button
                  onClick={() => {
                    clearAllFilters();
                    setShowMobileFilter(false);
                  }}
                  className="w-full py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs font-semibold text-ssk-navy hover:bg-ssk-blue-light"
                >
                  Reset All Filters
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Quick View Modal */}
      <QuickViewModal
        product={quickViewProduct}
        onClose={() => setQuickViewProduct(null)}
      />
    </PageTransition>
  );
};
