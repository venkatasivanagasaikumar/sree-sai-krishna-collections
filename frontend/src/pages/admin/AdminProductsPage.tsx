import React, { useState, useEffect } from 'react';
import {
  Plus, Search, Download, Edit2, Trash2, Layers,
  Check, X, Eye, AlertCircle, Sparkles
} from 'lucide-react';
import { api } from '../../services/api';
import { Product, Category } from '../../types';

export const AdminProductsPage: React.FC = () => {
  const [products, setProducts] = useState<Product[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    category: '1-Gram Gold Jewellery',
    subcategory: 'Necklaces & Chains',
    description: '',
    mrp: 1999,
    price: 999,
    stock: 25,
    low_stock_threshold: 5,
    jewelry_type: '1-Gram Gold Finish',
    materials_and_finish: 'Brass copper alloy with micro gold-plating finish',
    care_instructions: 'Keep away from water, perfumes, and harsh chemicals. Store in an airtight pouch.',
    images: ['https://images.unsplash.com/photo-1599643478518-a784e5dc4c8f?auto=format&fit=crop&w=800&q=80'],
    is_featured: false,
    is_bestseller: false,
    is_trending: false
  });

  const [imageUrlInput, setImageUrlInput] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const [res, cats] = await Promise.all([
        api.getProducts({ search: searchTerm, category: categoryFilter, limit: 100 }),
        api.getCategories()
      ]);
      setProducts(res.products);
      setCategories(cats);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, [searchTerm, categoryFilter]);

  const handleExportCsv = async () => {
    try {
      const res = await api.exportProductsCsv();
      const blob = new Blob([res.csv_content], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', res.filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (e) {
      alert('Failed to export CSV');
    }
  };

  const handleSaveProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMsg(null);
    try {
      if (editingProduct) {
        await api.updateProduct(editingProduct.id, formData);
      } else {
        await api.createProduct(formData);
      }
      setShowAddModal(false);
      setEditingProduct(null);
      await fetchProducts();
    } catch (err: any) {
      setErrorMsg(err.message || 'Error saving product');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (productId: string) => {
    if (!window.confirm('Are you sure you want to archive this product?')) return;
    try {
      await api.deleteProduct(productId);
      await fetchProducts();
    } catch (err: any) {
      alert(err.message || 'Failed to archive');
    }
  };

  const openEditModal = (p: Product) => {
    setEditingProduct(p);
    setFormData({
      name: p.name,
      sku: p.sku,
      category: p.category,
      subcategory: p.subcategory || '',
      description: p.description,
      mrp: p.mrp,
      price: p.price,
      stock: p.stock,
      low_stock_threshold: p.low_stock_threshold || 5,
      jewelry_type: p.jewelry_type,
      materials_and_finish: p.materials_and_finish,
      care_instructions: p.care_instructions,
      images: p.images,
      is_featured: !!p.is_featured,
      is_bestseller: !!p.is_bestseller,
      is_trending: !!p.is_trending
    });
    setShowAddModal(true);
  };

  const addImageUrl = () => {
    if (imageUrlInput.trim()) {
      setFormData(prev => ({ ...prev, images: [...prev.images, imageUrlInput.trim()] }));
      setImageUrlInput('');
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-ssk-navy">Product Catalog Management</h1>
          <p className="text-xs text-ssk-text-secondary mt-1">
            Maintain design specifications, images, variants, and stock thresholds.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportCsv}
            className="px-4 py-2.5 border border-ssk-border hover:bg-ssk-blue-light text-ssk-navy text-xs font-semibold rounded-xl flex items-center gap-1.5 shadow-sm transition-all"
          >
            <Download className="w-4 h-4" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={() => {
              setEditingProduct(null);
              setShowAddModal(true);
            }}
            className="px-5 py-2.5 bg-ssk-navy hover:bg-ssk-navy-dark text-white text-xs font-bold rounded-xl flex items-center gap-2 shadow-md transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Add New Product</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-4 rounded-2xl border border-ssk-border shadow-sm flex flex-col sm:flex-row gap-4 items-center justify-between">
        <div className="relative w-full sm:w-80">
          <input
            type="text"
            placeholder="Search SKU or product name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-ssk-surface border border-ssk-border rounded-xl text-xs focus:outline-none focus:border-ssk-gold"
          />
          <Search className="w-4 h-4 text-ssk-text-secondary absolute left-3 top-2.5" />
        </div>

        <div className="flex items-center gap-3 w-full sm:w-auto">
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="bg-white border border-ssk-border rounded-xl px-3 py-2 text-xs font-medium text-ssk-text focus:outline-none focus:border-ssk-gold"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c.id} value={c.name}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Product Table */}
      <div className="bg-white rounded-3xl border border-ssk-border shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead className="bg-ssk-surface text-ssk-text-secondary border-b border-ssk-border uppercase font-semibold text-[10px] tracking-wider">
              <tr>
                <th className="py-4 px-6">Product & Image</th>
                <th className="py-4 px-4">SKU</th>
                <th className="py-4 px-4">Category</th>
                <th className="py-4 px-4">Type</th>
                <th className="py-4 px-4">Selling Price</th>
                <th className="py-4 px-4">Stock</th>
                <th className="py-4 px-4">Status</th>
                <th className="py-4 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-ssk-border font-medium">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-ssk-text-secondary">Loading product database...</td>
                </tr>
              ) : products.length > 0 ? (
                products.map((p) => (
                  <tr key={p.id} className="hover:bg-ssk-blue-light/30 transition-colors">
                    <td className="py-3 px-6">
                      <div className="flex items-center gap-3">
                        <img
                          src={p.images[0] || '/logo.svg'}
                          alt={p.name}
                          className="w-12 h-12 object-cover rounded-xl border border-ssk-border flex-shrink-0"
                        />
                        <div className="max-w-xs">
                          <p className="font-bold text-ssk-text truncate">{p.name}</p>
                          <span className="text-[10px] text-ssk-text-secondary line-clamp-1">{p.materials_and_finish}</span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-4 font-mono font-bold text-ssk-navy">{p.sku}</td>
                    <td className="py-3 px-4 text-ssk-text-secondary">{p.category}</td>
                    <td className="py-3 px-4">
                      <span className="text-[10px] font-semibold text-ssk-gold-dark bg-ssk-gold/10 px-2 py-0.5 rounded-full whitespace-nowrap">
                        {p.jewelry_type}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="font-bold text-ssk-navy block">₹{p.price}</span>
                      <span className="text-[10px] text-ssk-text-secondary line-through">MRP ₹{p.mrp}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-block px-2.5 py-1 rounded-full text-[10px] font-bold ${
                          p.stock <= 5
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {p.stock} units
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span className="inline-block px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-ssk-blue-light text-ssk-navy uppercase">
                        {p.status}
                      </span>
                    </td>
                    <td className="py-3 px-6 text-right space-x-2">
                      <button
                        onClick={() => openEditModal(p)}
                        className="p-1.5 text-ssk-navy hover:bg-ssk-blue-light rounded-lg transition-colors"
                        title="Edit Product"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(p.id)}
                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        title="Archive Product"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-ssk-text-secondary">No products matched query.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Product Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm overflow-y-auto">
          <div className="bg-white rounded-3xl max-w-2xl w-full p-8 shadow-2xl border border-ssk-border space-y-6 my-8 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-ssk-border pb-4">
              <h3 className="text-lg font-serif font-bold text-ssk-navy">
                {editingProduct ? `Edit Product: ${editingProduct.sku}` : 'Add New Jewellery Product'}
              </h3>
              <button onClick={() => setShowAddModal(false)}><X className="w-5 h-5 text-ssk-text-secondary" /></button>
            </div>

            {errorMsg && (
              <div className="p-3 bg-red-50 text-red-700 text-xs rounded-xl flex items-center gap-2">
                <AlertCircle className="w-4 h-4" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSaveProduct} className="space-y-4 text-xs">
              <div>
                <label className="block font-bold text-ssk-text mb-1">Product Title *</label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Royal Lakshmi Temple Matte Finish Choker Set"
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-ssk-text mb-1">SKU Identifier *</label>
                  <input
                    type="text"
                    required
                    value={formData.sku}
                    onChange={(e) => setFormData({ ...formData, sku: e.target.value.toUpperCase() })}
                    placeholder="SSK-JWL-105"
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Category *</label>
                  <select
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  >
                    {categories.map((c) => (
                      <option key={c.id} value={c.name}>{c.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Jewellery Finish / Type *</label>
                  <select
                    value={formData.jewelry_type}
                    onChange={(e) => setFormData({ ...formData, jewelry_type: e.target.value })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  >
                    <option value="1-Gram Gold Finish">1-Gram Gold Finish</option>
                    <option value="Imitation Jewellery">Imitation Jewellery</option>
                    <option value="Hair Accessory">Hair Accessory</option>
                    <option value="Traditional Accessories">Traditional Accessories</option>
                  </select>
                </div>
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Subcategory</label>
                  <input
                    type="text"
                    value={formData.subcategory}
                    onChange={(e) => setFormData({ ...formData, subcategory: e.target.value })}
                    placeholder="e.g. Chokers / Jhumkas"
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Selling Price (₹) *</label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl font-bold text-ssk-navy"
                  />
                </div>
                <div>
                  <label className="block font-bold text-ssk-text mb-1">MRP (₹) *</label>
                  <input
                    type="number"
                    required
                    min={1}
                    value={formData.mrp}
                    onChange={(e) => setFormData({ ...formData, mrp: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  />
                </div>
                <div>
                  <label className="block font-bold text-ssk-text mb-1">Stock Quantity *</label>
                  <input
                    type="number"
                    required
                    min={0}
                    value={formData.stock}
                    onChange={(e) => setFormData({ ...formData, stock: Number(e.target.value) })}
                    className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  />
                </div>
              </div>

              <div>
                <label className="block font-bold text-ssk-text mb-1">Materials & Finish Description *</label>
                <input
                  type="text"
                  required
                  value={formData.materials_and_finish}
                  onChange={(e) => setFormData({ ...formData, materials_and_finish: e.target.value })}
                  placeholder="e.g. Brass copper alloy with 24k micro gold plating and ruby kemp stones"
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                />
              </div>

              <div>
                <label className="block font-bold text-ssk-text mb-1">Product Description *</label>
                <textarea
                  rows={3}
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter detailed description..."
                  className="w-full px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                />
              </div>

              {/* Image URLs */}
              <div>
                <label className="block font-bold text-ssk-text mb-1">Product Images (URLs)</label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="url"
                    placeholder="https://images.unsplash.com/photo-..."
                    value={imageUrlInput}
                    onChange={(e) => setImageUrlInput(e.target.value)}
                    className="flex-1 px-3 py-2 bg-ssk-surface border border-ssk-border rounded-xl"
                  />
                  <button
                    type="button"
                    onClick={addImageUrl}
                    className="px-4 py-2 bg-ssk-navy text-white rounded-xl font-bold"
                  >
                    Add URL
                  </button>
                </div>
                <div className="flex gap-2 overflow-x-auto py-1">
                  {formData.images.map((img, idx) => (
                    <div key={idx} className="relative w-16 h-16 rounded-xl overflow-hidden border border-ssk-border flex-shrink-0">
                      <img src={img} alt="preview" className="w-full h-full object-cover" />
                      <button
                        type="button"
                        onClick={() => setFormData({ ...formData, images: formData.images.filter((_, i) => i !== idx) })}
                        className="absolute top-0 right-0 p-1 bg-red-600 text-white rounded-bl-lg"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-ssk-border">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-5 py-2.5 border border-ssk-border rounded-xl font-semibold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-6 py-2.5 bg-ssk-navy text-white rounded-xl font-bold shadow-md hover:bg-ssk-navy-dark"
                >
                  {isSaving ? 'Saving...' : editingProduct ? 'Update Product' : 'Create Product'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
