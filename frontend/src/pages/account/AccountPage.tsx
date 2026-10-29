import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { User, Package, MapPin, Heart, Shield, LogOut, Plus, Trash2, ArrowRight } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { api } from '../../services/api';
import { Order, Address } from '../../types';

export const AccountPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAuthenticated, logout, refreshProfile } = useAuth();
  const [orders, setOrders] = useState<Order[]>([]);
  const [activeTab, setActiveTab] = useState<'orders' | 'addresses' | 'profile'>('orders');
  const [loading, setLoading] = useState(true);

  // New address state
  const [showAddAddress, setShowAddAddress] = useState(false);
  const [newAddr, setNewAddr] = useState<Address>({
    name: user?.full_name || '',
    phone: user?.phone || '',
    address_line1: '',
    address_line2: '',
    landmark: '',
    city: 'Hyderabad',
    state: 'Telangana',
    pincode: '',
    is_default: false,
    type: 'Home'
  });

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    api.getMyOrders()
      .then(setOrders)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [isAuthenticated]);

  const handleSaveAddress = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.addAddress(newAddr);
      setShowAddAddress(false);
      await refreshProfile();
    } catch (err: any) {
      alert(err.message || 'Failed to add address');
    }
  };

  const handleDeleteAddress = async (addrId: string) => {
    try {
      await api.deleteAddress(addrId);
      await refreshProfile();
    } catch (err: any) {
      alert(err.message || 'Failed to delete address');
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="flex flex-col md:flex-row gap-8">
        
        {/* Sidebar Tabs */}
        <aside className="md:w-64 space-y-2 bg-white p-4 rounded-2xl border border-ssk-border self-start">
          <div className="p-4 border-b border-ssk-border mb-2 text-center">
            <div className="w-16 h-16 rounded-full bg-ssk-navy text-white flex items-center justify-center font-bold text-xl mx-auto shadow-sm mb-2">
              {user.full_name?.charAt(0).toUpperCase()}
            </div>
            <h3 className="font-bold text-sm text-ssk-text">{user.full_name}</h3>
            <p className="text-xs text-ssk-text-secondary truncate">{user.email}</p>
          </div>

          <button
            onClick={() => setActiveTab('orders')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'orders' ? 'bg-ssk-navy text-white shadow-sm' : 'text-ssk-text hover:bg-ssk-blue-light'
            }`}
          >
            <Package className="w-4 h-4" />
            <span>My Orders & Tracking</span>
          </button>

          <button
            onClick={() => setActiveTab('addresses')}
            className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold transition-all ${
              activeTab === 'addresses' ? 'bg-ssk-navy text-white shadow-sm' : 'text-ssk-text hover:bg-ssk-blue-light'
            }`}
          >
            <MapPin className="w-4 h-4" />
            <span>Saved Addresses</span>
          </button>

          <Link
            to="/wishlist"
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-ssk-text hover:bg-ssk-blue-light"
          >
            <Heart className="w-4 h-4" />
            <span>My Wishlist</span>
          </Link>

          {['Super Admin', 'Admin', 'Order Manager', 'Inventory Manager'].includes(user.role) && (
            <Link
              to="/admin/dashboard"
              className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-bold text-ssk-navy bg-ssk-gold/15 hover:bg-ssk-gold/25"
            >
              <Shield className="w-4 h-4 text-ssk-gold-dark" />
              <span>Seller Panel</span>
            </Link>
          )}

          <button
            onClick={logout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-xs font-semibold text-red-600 hover:bg-red-50 mt-4 border-t border-ssk-border pt-4"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </aside>

        {/* Tab Content */}
        <div className="flex-1">
          {activeTab === 'orders' && (
            <div className="space-y-4">
              <h2 className="text-xl font-serif font-bold text-ssk-navy">Your Order History</h2>
              {loading ? (
                <div className="p-8 text-center text-xs text-ssk-text-secondary">Loading your orders...</div>
              ) : orders.length > 0 ? (
                <div className="space-y-4">
                  {orders.map((order) => (
                    <div key={order.order_id} className="bg-white p-6 rounded-2xl border border-ssk-border shadow-sm space-y-4">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-ssk-border">
                        <div>
                          <span className="text-[10px] text-ssk-text-secondary uppercase">Order ID</span>
                          <p className="font-mono font-bold text-xs text-ssk-navy">{order.order_id}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-ssk-text-secondary uppercase">Date</span>
                          <p className="text-xs font-semibold">{new Date(order.created_at).toLocaleDateString()}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-ssk-text-secondary uppercase">Status</span>
                          <p className="text-xs font-bold uppercase text-ssk-navy">{order.order_status}</p>
                        </div>
                        <div>
                          <span className="text-[10px] text-ssk-text-secondary uppercase">Amount</span>
                          <p className="text-sm font-bold text-ssk-navy font-serif">₹{order.final_amount}</p>
                        </div>
                      </div>

                      <div className="space-y-2">
                        {order.items.map((item, idx) => (
                          <div key={idx} className="flex items-center justify-between text-xs">
                            <div className="flex items-center gap-3">
                              <img src={item.image || '/logo.svg'} alt={item.name} className="w-10 h-10 object-cover rounded-lg border border-ssk-border" />
                              <div>
                                <p className="font-semibold text-ssk-text">{item.name}</p>
                                <span className="text-ssk-text-secondary text-[10px]">Qty: {item.quantity}</span>
                              </div>
                            </div>
                            <span className="font-bold text-ssk-navy">₹{item.total_price}</span>
                          </div>
                        ))}
                      </div>

                      <div className="flex justify-end pt-3 border-t border-ssk-border">
                        <Link
                          to={`/account/orders/${order.order_id}`}
                          className="px-4 py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl hover:bg-ssk-navy-dark flex items-center gap-1.5 shadow-sm"
                        >
                          <span>Track & Manage Order</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </Link>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 bg-white rounded-2xl border border-ssk-border p-6">
                  <Package className="w-10 h-10 text-ssk-gold mx-auto mb-2" />
                  <p className="text-xs font-semibold text-ssk-text">You haven't placed any orders yet.</p>
                  <Link to="/shop" className="mt-3 inline-block px-5 py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl">
                    Explore SSK Jewellery
                  </Link>
                </div>
              )}
            </div>
          )}

          {activeTab === 'addresses' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-serif font-bold text-ssk-navy">Saved Delivery Addresses</h2>
                <button
                  onClick={() => setShowAddAddress(!showAddAddress)}
                  className="px-4 py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-sm"
                >
                  <Plus className="w-4 h-4" />
                  <span>Add New Address</span>
                </button>
              </div>

              {showAddAddress && (
                <form onSubmit={handleSaveAddress} className="bg-white p-6 rounded-2xl border border-ssk-gold/50 shadow-md space-y-4">
                  <h3 className="text-xs font-bold text-ssk-navy uppercase tracking-wider">New Address Form</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <input
                      type="text"
                      required
                      placeholder="Contact Name"
                      value={newAddr.name}
                      onChange={(e) => setNewAddr({ ...newAddr, name: e.target.value })}
                      className="px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                    />
                    <input
                      type="tel"
                      required
                      placeholder="Phone Number"
                      value={newAddr.phone}
                      onChange={(e) => setNewAddr({ ...newAddr, phone: e.target.value })}
                      className="px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                    />
                  </div>
                  <input
                    type="text"
                    required
                    placeholder="House/Flat No., Street"
                    value={newAddr.address_line1}
                    onChange={(e) => setNewAddr({ ...newAddr, address_line1: e.target.value })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                  />
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="text"
                      required
                      maxLength={6}
                      placeholder="PIN Code"
                      value={newAddr.pincode}
                      onChange={(e) => setNewAddr({ ...newAddr, pincode: e.target.value })}
                      className="px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                    />
                    <input
                      type="text"
                      required
                      placeholder="City"
                      value={newAddr.city}
                      onChange={(e) => setNewAddr({ ...newAddr, city: e.target.value })}
                      className="px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                    />
                    <input
                      type="text"
                      required
                      placeholder="State"
                      value={newAddr.state}
                      onChange={(e) => setNewAddr({ ...newAddr, state: e.target.value })}
                      className="px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs"
                    />
                  </div>
                  <div className="flex justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setShowAddAddress(false)}
                      className="px-4 py-2 border border-ssk-border text-xs rounded-xl"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-5 py-2 bg-ssk-navy text-white text-xs font-semibold rounded-xl"
                    >
                      Save Address
                    </button>
                  </div>
                </form>
              )}

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {user.addresses && user.addresses.length > 0 ? (
                  user.addresses.map((addr) => (
                    <div key={addr.id} className="bg-white p-5 rounded-2xl border border-ssk-border shadow-sm flex flex-col justify-between space-y-3">
                      <div className="space-y-1 text-xs">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-ssk-text">{addr.name}</span>
                          <span className="text-[10px] font-semibold bg-ssk-blue-light text-ssk-navy px-2 py-0.5 rounded-full">
                            {addr.type || 'Home'}
                          </span>
                        </div>
                        <p className="text-ssk-text-secondary">{addr.address_line1}</p>
                        {addr.address_line2 && <p className="text-ssk-text-secondary">{addr.address_line2}</p>}
                        <p className="text-ssk-text-secondary">{addr.city}, {addr.state} - {addr.pincode}</p>
                        <p className="text-ssk-text-secondary pt-1">Phone: {addr.phone}</p>
                      </div>
                      <div className="flex justify-end pt-2 border-t border-ssk-border">
                        <button
                          onClick={() => addr.id && handleDeleteAddress(addr.id)}
                          className="text-xs text-red-600 hover:text-red-800 flex items-center gap-1 font-semibold"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                          <span>Remove</span>
                        </button>
                      </div>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-ssk-text-secondary">No saved addresses yet.</p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
