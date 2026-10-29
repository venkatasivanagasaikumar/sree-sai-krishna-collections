import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { Filter, SlidersHorizontal, ChevronRight, X, Sparkles } from 'lucide-react';
import { ProductCard } from '../../components/products/ProductCard';
import { QuickViewModal } from '../../components/products/QuickViewModal';
import { api } from '../../services/api';
import { Product, Category } from '../../types';

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
          limit: 12
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
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Breadcrumbs */}
      <nav className="flex items-center gap-2 text-xs text-ssk-text-secondary mb-6">
        <Link to="/" className="hover:text-ssk-navy">Home</Link>
        <ChevronRight className="w-3.5 h-3.5" />
        <Link to="/shop" className="hover:text-ssk-navy">Shop</Link>
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
          <button
            onClick={() => setShowMobileFilter(true)}
            className="lg:hidden flex items-center gap-2 px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold text-ssk-text hover:bg-ssk-blue-light"
          >
            <SlidersHorizontal className="w-4 h-4 text-ssk-gold" />
            <span>Filters</span>
          </button>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-ssk-text-secondary hidden sm:inline">Sort by:</span>
            <select
              value={currentSort}
              onChange={(e) => updateFilter('sort_by', e.target.value)}
              className="bg-white border border-ssk-border rounded-xl px-3 py-2 text-xs font-medium text-ssk-text focus:outline-none focus:border-ssk-gold shadow-sm"
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

      {/* Active Filter Pills */}
      {hasActiveFilters && (
        <div className="flex flex-wrap items-center gap-2 mb-6">
          <span className="text-xs text-ssk-text-secondary font-medium">Active filters:</span>
          {currentCategory && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold">
              Category: {currentCategory}
              <button onClick={() => updateFilter('category', null)}><X className="w-3.5 h-3.5" /></button>
            </span>
          )}
          {currentJewelryType && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold">
              Type: {currentJewelryType}
              <button onClick={() => updateFilter('jewelry_type', null)}><X className="w-3.5 h-3.5" /></button>
            </span>
          )}
          {currentSearch && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold">
              Search: "{currentSearch}"
              <button onClick={() => updateFilter('search', null)}><X className="w-3.5 h-3.5" /></button>
            </span>
          )}
          {inStockOnly && (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-ssk-blue-light text-ssk-navy rounded-full text-xs font-semibold">
              In Stock Only
              <button onClick={() => updateFilter('in_stock_only', null)}><X className="w-3.5 h-3.5" /></button>
            </span>
          )}
          <button
            onClick={clearAllFilters}
            className="text-xs text-ssk-error font-semibold hover:underline ml-2"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Main Grid & Sidebar Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        
        {/* Desktop Sidebar Filters */}
        <aside className="hidden lg:block space-y-6 bg-white p-6 rounded-2xl border border-ssk-border self-start sticky top-28">
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
                <label key={t} className="flex items-center gap-2 cursor-pointer text-ssk-text hover:text-ssk-navy">
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
            <label className="flex items-center gap-2 cursor-pointer text-xs text-ssk-text">
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
                <div key={i} className="animate-pulse bg-white rounded-2xl border border-ssk-border p-4 space-y-3">
                  <div className="aspect-square bg-gray-200 rounded-xl" />
                  <div className="h-4 bg-gray-200 rounded w-3/4" />
                  <div className="h-4 bg-gray-200 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : products.length > 0 ? (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
                {products.map((product) => (
                  <ProductCard
                    key={product.id}
                    product={product}
                    onQuickView={(p) => setQuickViewProduct(p)}
                  />
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-center gap-2 mt-12">
                  <button
                    disabled={currentPage <= 1}
                    onClick={() => updateFilter('page', String(currentPage - 1))}
                    className="px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold disabled:opacity-40 hover:bg-ssk-blue-light"
                  >
                    Previous
                  </button>
                  {[...Array(totalPages)].map((_, i) => (
                    <button
                      key={i + 1}
                      onClick={() => updateFilter('page', String(i + 1))}
                      className={`w-9 h-9 rounded-xl text-xs font-bold transition-all ${
                        currentPage === i + 1
                          ? 'bg-ssk-navy text-white shadow-sm'
                          : 'border border-ssk-border hover:bg-ssk-blue-light text-ssk-text'
                      }`}
                    >
                      {i + 1}
                    </button>
                  ))}
                  <button
                    disabled={currentPage >= totalPages}
                    onClick={() => updateFilter('page', String(currentPage + 1))}
                    className="px-4 py-2 border border-ssk-border rounded-xl text-xs font-semibold disabled:opacity-40 hover:bg-ssk-blue-light"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-16 bg-white rounded-2xl border border-ssk-border p-8">
              <Sparkles className="w-12 h-12 text-ssk-gold mx-auto mb-3" />
              <h3 className="text-lg font-bold text-ssk-navy font-serif">No jewellery found</h3>
              <p className="text-xs text-ssk-text-secondary mt-1 max-w-sm mx-auto">
                Try selecting a different category or clearing search filters to see all available designs.
              </p>
              <button
                onClick={clearAllFilters}
                className="mt-4 px-6 py-2.5 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm"
              >
                Clear All Filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Quick View Modal */}
      <QuickViewModal
        product={quickViewProduct}
        onClose={() => setQuickViewProduct(null)}
      />
    </div>
  );
};
