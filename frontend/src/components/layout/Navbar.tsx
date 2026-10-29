import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Search, ShoppingBag, Heart, User as UserIcon, Menu, X, ChevronDown, LogOut, Package, Shield, Sparkles } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';
import { api } from '../../services/api';
import { Product, Category } from '../../types';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { itemCount } = useCart();
  const { wishlistCount } = useWishlist();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isCategoryDropdownOpen, setIsCategoryDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Product[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);

  const searchRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Load categories
  useEffect(() => {
    api.getCategories().then(setCategories).catch(console.error);
  }, []);

  // Handle live search
  useEffect(() => {
    if (!searchQuery.trim() || searchQuery.length < 2) {
      setSearchResults([]);
      setShowSearchDropdown(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await api.getProducts({ search: searchQuery, limit: 5 });
        setSearchResults(res.products);
        setShowSearchDropdown(true);
      } catch (e) {
        console.error(e);
      } finally {
        setIsSearching(false);
      }
    }, 250);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) {
        setShowSearchDropdown(false);
      }
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setIsUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      setShowSearchDropdown(false);
      navigate(`/shop?search=${encodeURIComponent(searchQuery.trim())}`);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-ssk-border transition-all">
      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          
          {/* Mobile menu button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-ssk-text hover:bg-ssk-blue-light"
            aria-label="Toggle Navigation"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>

          {/* Logo */}
          <Link to="/" className="flex-shrink-0">
            <BrandLogo size="md" />
          </Link>

          {/* Search Bar (Desktop) */}
          <div ref={searchRef} className="hidden md:flex flex-1 max-w-lg mx-6 relative">
            <form onSubmit={handleSearchSubmit} className="w-full relative">
              <input
                type="text"
                placeholder="Search jhumkas, chokers, kada bangles, claw clips..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={() => searchQuery.length >= 2 && setShowSearchDropdown(true)}
                className="w-full pl-10 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-full text-sm text-ssk-text placeholder-ssk-text-secondary focus:outline-none focus:border-ssk-gold focus:ring-2 focus:ring-ssk-gold/20 transition-all"
              />
              <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3.5 top-3.5" />
            </form>

            {/* Live Search Suggestions Dropdown */}
            {showSearchDropdown && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-ssk-border overflow-hidden z-50">
                {isSearching ? (
                  <div className="p-4 text-center text-xs text-ssk-text-secondary">Searching collections...</div>
                ) : searchResults.length > 0 ? (
                  <div className="divide-y divide-ssk-border">
                    {searchResults.map((product) => (
                      <Link
                        key={product.id}
                        to={`/product/${product.sku}`}
                        onClick={() => setShowSearchDropdown(false)}
                        className="flex items-center gap-3 p-3 hover:bg-ssk-blue-light transition-colors"
                      >
                        <img
                          src={product.images[0] || '/logo.svg'}
                          alt={product.name}
                          className="w-12 h-12 object-cover rounded-lg border border-ssk-border"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-xs font-semibold text-ssk-text truncate">{product.name}</p>
                          <div className="flex items-center gap-2 mt-0.5">
                            <span className="text-xs font-bold text-ssk-navy">₹{product.price}</span>
                            <span className="text-[10px] text-ssk-text-secondary line-through">₹{product.mrp}</span>
                            <span className="text-[10px] text-ssk-gold font-semibold uppercase">{product.jewelry_type}</span>
                          </div>
                        </div>
                      </Link>
                    ))}
                    <button
                      onClick={handleSearchSubmit}
                      className="w-full py-2.5 text-center text-xs font-semibold text-ssk-royal hover:bg-ssk-blue-light"
                    >
                      View all results for "{searchQuery}"
                    </button>
                  </div>
                ) : (
                  <div className="p-4 text-center text-xs text-ssk-text-secondary">
                    No products found matching "{searchQuery}"
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Right Action Icons */}
          <div className="flex items-center gap-3 sm:gap-4">
            
            {/* Wishlist */}
            <Link
              to="/wishlist"
              className="relative p-2 text-ssk-text hover:text-ssk-navy hover:bg-ssk-blue-light rounded-full transition-colors"
              title="Wishlist"
            >
              <Heart className="w-5 h-5" />
              {wishlistCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 bg-ssk-gold text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center shadow-sm">
                  {wishlistCount}
                </span>
              )}
            </Link>

            {/* Shopping Bag / Cart */}
            <Link
              to="/cart"
              className="relative p-2 text-ssk-text hover:text-ssk-navy hover:bg-ssk-blue-light rounded-full transition-colors flex items-center gap-1.5"
              title="Shopping Bag"
            >
              <ShoppingBag className="w-5 h-5" />
              {itemCount > 0 && (
                <span className="absolute -top-0.5 -right-0.5 bg-ssk-navy text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center shadow-sm">
                  {itemCount}
                </span>
              )}
            </Link>

            {/* User Account Menu */}
            <div ref={userMenuRef} className="relative">
              <button
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 p-1.5 rounded-full hover:bg-ssk-blue-light transition-colors text-ssk-text"
              >
                <div className="w-8 h-8 rounded-full bg-ssk-navy text-white flex items-center justify-center font-semibold text-xs shadow-sm">
                  {isAuthenticated ? (user?.full_name?.charAt(0).toUpperCase() || 'U') : <UserIcon className="w-4 h-4" />}
                </div>
                {isAuthenticated && (
                  <span className="hidden xl:inline text-xs font-medium text-ssk-text max-w-[100px] truncate">
                    {user?.full_name?.split(' ')[0]}
                  </span>
                )}
                <ChevronDown className="w-3.5 h-3.5 text-ssk-text-secondary hidden sm:inline" />
              </button>

              {/* User Dropdown */}
              {isUserMenuOpen && (
                <div className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-ssk-border py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                  {isAuthenticated ? (
                    <>
                      <div className="px-4 py-2 border-b border-ssk-border">
                        <p className="text-xs font-bold text-ssk-text truncate">{user?.full_name}</p>
                        <p className="text-[11px] text-ssk-text-secondary truncate">{user?.email}</p>
                        <span className="inline-block mt-1 px-2 py-0.5 text-[9px] font-bold bg-ssk-blue-light text-ssk-navy rounded-full uppercase">
                          {user?.role}
                        </span>
                      </div>
                      <Link
                        to="/account"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-xs text-ssk-text hover:bg-ssk-blue-light"
                      >
                        <UserIcon className="w-4 h-4 text-ssk-navy" />
                        My Profile & Addresses
                      </Link>
                      <Link
                        to="/account/orders"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="flex items-center gap-2.5 px-4 py-2 text-xs text-ssk-text hover:bg-ssk-blue-light"
                      >
                        <Package className="w-4 h-4 text-ssk-navy" />
                        My Orders & Tracking
                      </Link>
                      
                      {/* Seller/Admin Panel Shortcut */}
                      {isAdmin && (
                        <Link
                          to="/admin/dashboard"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-ssk-navy bg-ssk-gold/10 hover:bg-ssk-gold/20"
                        >
                          <Shield className="w-4 h-4 text-ssk-gold-dark" />
                          Seller Dashboard (Meesho Style)
                        </Link>
                      )}

                      <button
                        onClick={() => {
                          logout();
                          setIsUserMenuOpen(false);
                        }}
                        className="flex items-center gap-2.5 w-full text-left px-4 py-2 text-xs text-ssk-error hover:bg-red-50 border-t border-ssk-border mt-1"
                      >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                      </button>
                    </>
                  ) : (
                    <div className="p-3 space-y-2">
                      <p className="text-xs text-ssk-text-secondary mb-2">Sign in for saved bags, tracking & faster checkout.</p>
                      <Link
                        to="/login"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="block w-full text-center py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm"
                      >
                        Sign In
                      </Link>
                      <Link
                        to="/register"
                        onClick={() => setIsUserMenuOpen(false)}
                        className="block w-full text-center py-2 bg-ssk-surface border border-ssk-border text-ssk-text text-xs font-medium rounded-xl hover:bg-ssk-blue-light"
                      >
                        Create Account
                      </Link>
                      <div className="pt-2 border-t border-ssk-border">
                        <Link
                          to="/admin/login"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center justify-center gap-1.5 text-[11px] text-ssk-gold-dark font-medium hover:underline"
                        >
                          <Shield className="w-3.5 h-3.5" />
                          Seller / Staff Login
                        </Link>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Category Navigation Bar (Desktop) */}
      <nav className="hidden md:block bg-ssk-surface/80 border-t border-ssk-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ul className="flex items-center justify-between text-xs font-medium text-ssk-text py-2.5 overflow-x-auto no-scrollbar">
            <li>
              <Link to="/shop" className="hover:text-ssk-navy hover:font-semibold transition-colors flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-ssk-gold" />
                All Collections
              </Link>
            </li>
            <li>
              <Link to="/shop?category=1-Gram+Gold+Jewellery" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                1-Gram Gold
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Earrings+%26+Jhumkas" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Earrings & Jhumkas
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Necklaces+%26+Chains" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Necklaces & Chokers
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Bangles+%26+Bracelets" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Kada Bangles
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Claw+Clips" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Claw Clips
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Scrunchies+%26+Hair+Bands" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Silk Scrunchies
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Hair+Clips+%26+Pins" className="hover:text-ssk-navy hover:font-semibold transition-colors">
                Bridal Hair Pins
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Traditional+Accessories" className="hover:text-ssk-navy hover:font-semibold transition-colors text-ssk-gold-dark font-semibold">
                Traditional Vaddanam
              </Link>
            </li>
          </ul>
        </div>
      </nav>

      {/* Mobile Drawer Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-ssk-border px-4 pt-3 pb-6 space-y-4">
          <form onSubmit={handleSearchSubmit} className="relative">
            <input
              type="text"
              placeholder="Search jewellery & hair accessories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-sm"
            />
            <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
          </form>

          <div className="space-y-1">
            <p className="text-[11px] font-bold text-ssk-text-secondary uppercase tracking-wider px-2">Browse Categories</p>
            <Link
              to="/shop"
              onClick={() => setIsMobileMenuOpen(false)}
              className="block px-3 py-2 text-sm font-semibold text-ssk-navy rounded-lg hover:bg-ssk-blue-light"
            >
              All Jewellery & Accessories
            </Link>
            {categories.map((c) => (
              <Link
                key={c.id}
                to={`/shop?category=${encodeURIComponent(c.name)}`}
                onClick={() => setIsMobileMenuOpen(false)}
                className="block px-3 py-2 text-sm text-ssk-text rounded-lg hover:bg-ssk-blue-light"
              >
                {c.name}
              </Link>
            ))}
          </div>

          <div className="pt-3 border-t border-ssk-border space-y-2">
            {isAdmin && (
              <Link
                to="/admin/dashboard"
                onClick={() => setIsMobileMenuOpen(false)}
                className="block w-full py-2.5 px-3 bg-ssk-gold/15 text-ssk-navy font-bold text-xs rounded-xl"
              >
                Seller Dashboard (Meesho Style)
              </Link>
            )}
            {!isAuthenticated ? (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  to="/login"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="py-2.5 text-center bg-ssk-navy text-white text-xs font-semibold rounded-xl"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="py-2.5 text-center border border-ssk-border text-ssk-text text-xs font-semibold rounded-xl"
                >
                  Register
                </Link>
              </div>
            ) : (
              <button
                onClick={() => {
                  logout();
                  setIsMobileMenuOpen(false);
                }}
                className="w-full py-2 text-center text-xs text-ssk-error font-medium"
              >
                Sign Out
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
