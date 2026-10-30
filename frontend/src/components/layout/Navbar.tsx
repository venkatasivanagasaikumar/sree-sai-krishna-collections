import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ShoppingBag, Heart, User as UserIcon, Menu, X, ChevronDown, LogOut, Package, Shield, Sparkles } from 'lucide-react';
import { BrandLogo } from '../common/BrandLogo';
import { useAuth } from '../../context/AuthContext';
import { useCart } from '../../context/CartContext';
import { useWishlist } from '../../context/WishlistContext';
import { api } from '../../services/api';
import { Product, Category } from '../../types';
import { navDropdown, mobileMenu } from '../../animations';

export const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const { itemCount } = useCart();
  const { wishlistCount } = useWishlist();

  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<Product[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearchDropdown, setShowSearchDropdown] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isScrolled, setIsScrolled] = useState(false);

  const searchRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);

  // Scroll listener for elegant header elevation
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 12);
    };
    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

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
    <header
      className={`sticky top-0 z-40 bg-white/95 backdrop-blur-md border-b border-ssk-border transition-all duration-300 ${
        isScrolled ? 'shadow-md py-0' : 'shadow-none py-0.5'
      }`}
    >
      {/* Main Navbar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20 gap-4">
          
          {/* Mobile menu button */}
          <motion.button
            whileTap={{ scale: 0.92 }}
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg text-ssk-text hover:bg-ssk-blue-light transition-colors"
            aria-label="Toggle Navigation"
          >
            {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </motion.button>

          {/* Logo as Home Button */}
          <Link
            to="/"
            title="Go to Home"
            aria-label="Sree Sai Krishna Collections Home"
            className="flex-shrink-0 group flex items-center transition-all duration-200 hover:opacity-95 focus:outline-none focus:ring-2 focus:ring-ssk-gold/30 rounded-xl"
          >
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
                className="w-full pl-10 pr-4 py-2.5 bg-ssk-surface border border-ssk-border rounded-full text-sm text-ssk-text placeholder-ssk-text-secondary focus:outline-none focus:border-ssk-gold focus:ring-2 focus:ring-ssk-gold/20 transition-all shadow-inner"
              />
              <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3.5 top-3.5" />
            </form>

            {/* Live Search Suggestions Dropdown with AnimatePresence */}
            <AnimatePresence>
              {showSearchDropdown && (
                <motion.div
                  variants={navDropdown}
                  initial="hidden"
                  animate="visible"
                  exit="exit"
                  className="absolute top-full left-0 right-0 mt-2 bg-white rounded-2xl shadow-xl border border-ssk-border overflow-hidden z-50 origin-top"
                >
                  {isSearching ? (
                    <div className="p-4 text-center text-xs text-ssk-text-secondary">Searching collections...</div>
                  ) : searchResults.length > 0 ? (
                    <div className="divide-y divide-ssk-border">
                      {searchResults.map((product) => (
                        <Link
                          key={product.id}
                          to={`/product/${product.sku}`}
                          onClick={() => setShowSearchDropdown(false)}
                          className="flex items-center gap-3 p-3 hover:bg-ssk-blue-light transition-colors group"
                        >
                          <img
                            src={product.images[0] || '/logo.svg'}
                            alt={product.name}
                            className="w-12 h-12 object-cover rounded-lg border border-ssk-border group-hover:scale-105 transition-transform"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-semibold text-ssk-text truncate group-hover:text-ssk-navy">{product.name}</p>
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
                        className="w-full py-2.5 text-center text-xs font-semibold text-ssk-royal hover:bg-ssk-blue-light transition-colors"
                      >
                        View all results for "{searchQuery}"
                      </button>
                    </div>
                  ) : (
                    <div className="p-4 text-center text-xs text-ssk-text-secondary">
                      No products found matching "{searchQuery}"
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Right Action Icons */}
          <div className="flex items-center gap-3 sm:gap-4">
            
            {/* Wishlist */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.92 }}>
              <Link
                to="/wishlist"
                className="relative p-2 text-ssk-text hover:text-ssk-navy hover:bg-ssk-blue-light rounded-full transition-colors block"
                title="Wishlist"
              >
                <Heart className="w-5 h-5" />
                <AnimatePresence>
                  {wishlistCount > 0 && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      exit={{ scale: 0 }}
                      className="absolute -top-0.5 -right-0.5 bg-ssk-gold text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center shadow-sm"
                    >
                      {wishlistCount}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            </motion.div>

            {/* Shopping Bag / Cart */}
            <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.92 }}>
              <Link
                to="/cart"
                className="relative p-2 text-ssk-text hover:text-ssk-navy hover:bg-ssk-blue-light rounded-full transition-colors flex items-center gap-1.5"
                title="Shopping Bag"
              >
                <ShoppingBag className="w-5 h-5" />
                <AnimatePresence>
                  {itemCount > 0 && (
                    <motion.span
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      exit={{ scale: 0 }}
                      className="absolute -top-0.5 -right-0.5 bg-ssk-navy text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center shadow-sm"
                    >
                      {itemCount}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Link>
            </motion.div>

            {/* User Account Menu */}
            <div ref={userMenuRef} className="relative">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
                className="flex items-center gap-2 p-1.5 rounded-full hover:bg-ssk-blue-light transition-colors text-ssk-text"
                aria-expanded={isUserMenuOpen}
                aria-label="User account menu"
              >
                <div className="w-8 h-8 rounded-full bg-ssk-navy text-white flex items-center justify-center font-semibold text-xs shadow-sm">
                  {isAuthenticated ? (user?.full_name?.charAt(0).toUpperCase() || 'U') : <UserIcon className="w-4 h-4" />}
                </div>
                {isAuthenticated && (
                  <span className="hidden xl:inline text-xs font-medium text-ssk-text max-w-[100px] truncate">
                    {user?.full_name?.split(' ')[0]}
                  </span>
                )}
                <ChevronDown className={`w-3.5 h-3.5 text-ssk-text-secondary hidden sm:inline transition-transform duration-200 ${isUserMenuOpen ? 'rotate-180' : ''}`} />
              </motion.button>

              {/* User Dropdown with AnimatePresence */}
              <AnimatePresence>
                {isUserMenuOpen && (
                  <motion.div
                    variants={navDropdown}
                    initial="hidden"
                    animate="visible"
                    exit="exit"
                    className="absolute right-0 mt-2 w-56 bg-white rounded-2xl shadow-xl border border-ssk-border py-2 z-50 origin-top-right"
                  >
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
                          className="flex items-center gap-2.5 px-4 py-2 text-xs text-ssk-text hover:bg-ssk-blue-light transition-colors"
                        >
                          <UserIcon className="w-4 h-4 text-ssk-navy" />
                          My Profile & Addresses
                        </Link>
                        <Link
                          to="/account/orders"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="flex items-center gap-2.5 px-4 py-2 text-xs text-ssk-text hover:bg-ssk-blue-light transition-colors"
                        >
                          <Package className="w-4 h-4 text-ssk-navy" />
                          My Orders & Tracking
                        </Link>
                        
                        {/* Seller/Admin Panel Shortcut */}
                        {isAdmin && (
                          <Link
                            to="/admin/dashboard"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-ssk-navy bg-ssk-gold/10 hover:bg-ssk-gold/20 transition-colors"
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
                          className="flex items-center gap-2.5 w-full text-left px-4 py-2 text-xs text-ssk-error hover:bg-red-50 border-t border-ssk-border mt-1 transition-colors"
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
                          className="block w-full text-center py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark shadow-sm transition-colors"
                        >
                          Sign In
                        </Link>
                        <Link
                          to="/register"
                          onClick={() => setIsUserMenuOpen(false)}
                          className="block w-full text-center py-2 bg-ssk-surface border border-ssk-border text-ssk-text text-xs font-medium rounded-xl hover:bg-ssk-blue-light transition-colors"
                        >
                          Create Account
                        </Link>
                        <div className="pt-2 border-t border-ssk-border">
                          <Link
                            to="/admin/login"
                            onClick={() => setIsUserMenuOpen(false)}
                            className="flex items-center justify-center gap-1.5 text-[11px] text-ssk-gold-dark font-medium hover:underline transition-colors"
                          >
                            <Shield className="w-3.5 h-3.5" />
                            Seller / Staff Login
                          </Link>
                        </div>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </div>
      </div>

      {/* Category Navigation Bar (Desktop) with elegant animated hover underlines */}
      <nav className="hidden md:block bg-ssk-surface/80 border-t border-ssk-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <ul className="flex items-center justify-between text-xs font-medium text-ssk-text py-2.5 overflow-x-auto no-scrollbar">
            <li>
              <Link to="/shop" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors flex items-center gap-1 py-1">
                <Sparkles className="w-3.5 h-3.5 text-ssk-gold" />
                <span>All Collections</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=1-Gram+Gold+Jewellery" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>1-Gram Gold</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Earrings+%26+Jhumkas" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Earrings & Jhumkas</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Necklaces+%26+Chains" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Necklaces & Chokers</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Bangles+%26+Bracelets" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Kada Bangles</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Claw+Clips" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Claw Clips</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Scrunchies+%26+Hair+Bands" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Silk Scrunchies</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Hair+Clips+%26+Pins" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors py-1">
                <span>Bridal Hair Pins</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
            <li>
              <Link to="/shop?category=Traditional+Accessories" className="relative group hover:text-ssk-navy hover:font-semibold transition-colors text-ssk-gold-dark font-semibold py-1">
                <span>Traditional Vaddanam</span>
                <span className="absolute bottom-0 left-0 w-0 h-0.5 bg-ssk-gold transition-all duration-300 group-hover:w-full" />
              </Link>
            </li>
          </ul>
        </div>
      </nav>

      {/* Mobile Drawer Menu with AnimatePresence */}
      <AnimatePresence>
        {isMobileMenuOpen && (
          <motion.div
            variants={mobileMenu}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="md:hidden bg-white border-b border-ssk-border px-4 pt-3 pb-6 space-y-4 overflow-hidden"
          >
            <form onSubmit={handleSearchSubmit} className="relative">
              <input
                type="text"
                placeholder="Search jewellery & hair accessories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-sm focus:outline-none focus:border-ssk-gold"
              />
              <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-3" />
            </form>

            <div className="space-y-1">
              <p className="text-[11px] font-bold text-ssk-text-secondary uppercase tracking-wider px-2">Browse Categories</p>
              <Link
                to="/shop"
                onClick={() => setIsMobileMenuOpen(false)}
                className="block px-3 py-2 text-sm font-semibold text-ssk-navy rounded-lg hover:bg-ssk-blue-light transition-colors"
              >
                All Jewellery & Accessories
              </Link>
              {categories.map((c) => (
                <Link
                  key={c.id}
                  to={`/shop?category=${encodeURIComponent(c.name)}`}
                  onClick={() => setIsMobileMenuOpen(false)}
                  className="block px-3 py-2 text-sm text-ssk-text rounded-lg hover:bg-ssk-blue-light transition-colors"
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
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};
