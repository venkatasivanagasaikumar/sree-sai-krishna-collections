import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, RefreshCw, Truck, FileText, Lock, AlertCircle, Phone, Mail, MapPin } from 'lucide-react';
import { PageTransition } from '../../components/animations/PageTransition';
import { BRAND_CONFIG } from '../../assets/brand.config';

type PolicyTab = 'returns' | 'shipping' | 'terms' | 'privacy' | 'cancellation' | 'grievance';

export const PoliciesPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<PolicyTab>('returns');

  return (
    <PageTransition className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-10">
      <div className="text-center space-y-3">
        <span className="text-xs font-bold text-ssk-gold uppercase tracking-widest px-3.5 py-1 bg-ssk-gold/10 rounded-full border border-ssk-gold/30">
          Consumer Trust & Compliance
        </span>
        <h1 className="text-3xl sm:text-4xl font-serif font-bold text-ssk-navy">
          Store Policies & Customer Protection
        </h1>
        <p className="text-xs sm:text-sm text-ssk-text-secondary max-w-2xl mx-auto">
          Compliant with the Consumer Protection (E-Commerce) Rules, 2020 and Information Technology Act of India.
        </p>
      </div>

      {/* Policy Navigation Tabs */}
      <div className="flex flex-wrap gap-2 justify-center border-b border-ssk-border pb-4">
        {[
          { id: 'returns', label: 'Returns & Refunds', icon: RefreshCw },
          { id: 'shipping', label: 'Shipping & Delivery', icon: Truck },
          { id: 'terms', label: 'Terms of Service', icon: FileText },
          { id: 'privacy', label: 'Privacy Policy', icon: Lock },
          { id: 'cancellation', label: 'Cancellation Policy', icon: AlertCircle },
          { id: 'grievance', label: 'Grievance Officer', icon: Shield },
        ].map((t) => {
          const Icon = t.icon;
          const isActive = activeTab === t.id;
          return (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id as PolicyTab)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-semibold transition-all ${
                isActive
                  ? 'bg-ssk-navy text-white shadow-md shadow-ssk-navy/15'
                  : 'bg-white text-ssk-text-secondary hover:bg-ssk-surface border border-ssk-border'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'text-ssk-gold' : 'text-ssk-text-muted'}`} />
              <span>{t.label}</span>
            </button>
          );
        })}
      </div>

      {/* Policy Content */}
      <div className="bg-white rounded-3xl p-6 sm:p-10 border border-ssk-border shadow-sm text-xs text-ssk-text leading-relaxed space-y-6">
        {activeTab === 'returns' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <RefreshCw className="w-5 h-5 text-ssk-gold" />
              <span>7-Day Return & Replacement Policy</span>
            </h2>
            <p>
              At <strong>{BRAND_CONFIG.name} (SSK)</strong>, we take immense pride in the craftsmanship of our 1-gram gold plated jewellery, bridal collections, and fashion accessories. If you receive an item that is defective, transit-damaged, or significantly different from your order, we offer a hassle-free 7-day return and replacement window.
            </p>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Eligibility Criteria</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li>Return requests must be initiated within <strong>7 calendar days</strong> from the delivery timestamp.</li>
              <li>Jewellery items must be unused, unblemished, unworn, with all original tags intact and inside the original SSK protective packaging.</li>
              <li>For transit damages or transit tampering, please provide clear photos or a short unboxing video through our Order Tracking portal or via WhatsApp support within 48 hours of delivery.</li>
            </ul>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Refund Processing & Timelines</h3>
            <p>
              Once your returned parcel reaches our verification center in Secunderabad, our quality audit team will inspect the item within 24–48 hours. Upon approval:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li><strong>Prepaid Orders (Cards/UPI/Net Banking):</strong> Refund is credited back to your original payment source within <strong>3 to 5 business days</strong>.</li>
              <li><strong>Cash on Delivery (COD) Orders:</strong> Our customer support will contact you to transfer the full refund directly via UPI or verified NEFT bank account.</li>
            </ul>
          </div>
        )}

        {activeTab === 'shipping' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <Truck className="w-5 h-5 text-ssk-gold" />
              <span>Domestic Shipping & Delivery Policy</span>
            </h2>
            <p>
              We deliver to over 19,000+ PIN codes across India through verified logistics partners including Delhivery, BlueDart, DTDC, and Express Cargo.
            </p>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Shipping Charges & Thresholds</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li><strong>Free Express Shipping:</strong> Available on all orders with cart subtotal of <strong>₹999 and above</strong>.</li>
              <li><strong>Standard Delivery Fee:</strong> Orders below ₹999 are charged a flat standard shipping fee of <strong>₹79</strong> across India.</li>
              <li><strong>Cash on Delivery (COD):</strong> Available for verified pin codes on orders between ₹299 and ₹50,000.</li>
            </ul>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Dispatch & Delivery Timelines</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li><strong>Order Processing:</strong> Orders are dispatched from our Telangana warehouse within 24–48 business hours (excluding Sundays & national holidays).</li>
              <li><strong>South India & Metros:</strong> Estimated delivery within <strong>2 to 4 business days</strong>.</li>
              <li><strong>Rest of India:</strong> Estimated delivery within <strong>4 to 7 business days</strong>.</li>
              <li><strong>Live Tracking:</strong> Real-time carrier Air Waybill (AWB) tracking numbers are sent via SMS and visible under your SSK account tracking portal.</li>
            </ul>
          </div>
        )}

        {activeTab === 'terms' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <FileText className="w-5 h-5 text-ssk-gold" />
              <span>Terms of Service & Material Transparency</span>
            </h2>
            <p>
              Welcome to <strong>Sree Sai Krishna Collections (SSK)</strong>. By accessing or shopping on our website, you agree to be bound by the terms detailed below.
            </p>
            <div className="p-4 bg-ssk-surface border border-ssk-border rounded-2xl space-y-2">
              <h4 className="font-bold text-ssk-navy flex items-center gap-1.5 text-xs">
                <AlertCircle className="w-4 h-4 text-ssk-gold" />
                <span>Important Consumer Transparency Note on 1-Gram Gold & Imitation Jewellery:</span>
              </h4>
              <p className="text-[11px] text-ssk-text-secondary leading-relaxed">
                Products described as "1-Gram Gold Jewellery", "Micro Gold Plated", "Forming Gold", or "Temple Jewellery" are high-quality <strong>fashion/imitation jewellery</strong> crafted with copper, brass, or alloy base metals electroplated with a micro layer of gold-tone finish. They do <strong>NOT</strong> contain solid bullion gold and do <strong>NOT</strong> carry BIS precious hallmark certificates. Please care for your fashion accessories by avoiding direct perfume, water, chemical exposure, and humidity.
              </p>
            </div>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Pricing, Taxes & Governing Law</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li>All product prices displayed are in Indian National Rupees (INR) and are inclusive of applicable Goods and Services Tax (GST).</li>
              <li>We reserve the right to correct any typographical or inventory pricing discrepancies prior to dispatch.</li>
              <li>These terms are governed by the laws of India. Any legal dispute shall be subject to the exclusive jurisdiction of the competent courts in Secunderabad / Hyderabad, Telangana.</li>
            </ul>
          </div>
        )}

        {activeTab === 'privacy' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <Lock className="w-5 h-5 text-ssk-gold" />
              <span>Privacy & Data Protection Policy</span>
            </h2>
            <p>
              Your personal privacy is paramount to us. Sree Sai Krishna Collections adheres strictly to the Digital Personal Data Protection (DPDP) standards and the IT (Reasonable Security Practices) Rules, 2011.
            </p>
            <h3 className="text-sm font-bold text-ssk-navy uppercase tracking-wider pt-2">Information We Collect</h3>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li><strong>Account & Delivery Data:</strong> Name, delivery address, contact telephone, and email address strictly to process fulfilment and deliver parcels.</li>
              <li><strong>Payment Security:</strong> We do NOT store credit card numbers, CVVs, or UPI MPINs. All digital payments are encrypted and processed securely by RBI-authorized payment gateways (Razorpay).</li>
              <li><strong>No Data Brokering:</strong> We never sell, rent, or trade your personal information with third-party advertising brokers.</li>
            </ul>
          </div>
        )}

        {activeTab === 'cancellation' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-ssk-gold" />
              <span>Order Cancellation Policy</span>
            </h2>
            <p>
              We understand that plans can change. You can cancel your order directly from your order tracking screen or by contacting our team before the order is dispatched.
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-ssk-text-secondary">
              <li><strong>Pre-Dispatch Cancellation:</strong> Self-service one-click cancellation is available on orders in <em>Order Placed</em> or <em>Processing</em> status. Stock is immediately released and 100% of the payment is refunded within 3-5 business days.</li>
              <li><strong>Post-Dispatch Cancellation:</strong> Once an order is assigned an Air Waybill (AWB) and handed to the courier partner, it cannot be intercepted in transit. You may refuse the delivery at doorstep or initiate a 7-day return upon receipt.</li>
            </ul>
          </div>
        )}

        {activeTab === 'grievance' && (
          <div className="space-y-4">
            <h2 className="text-xl font-serif font-bold text-ssk-navy flex items-center gap-2">
              <Shield className="w-5 h-5 text-ssk-gold" />
              <span>Grievance Officer & Official Business Details</span>
            </h2>
            <p>
              In accordance with the <strong>Consumer Protection (E-Commerce) Rules, 2020</strong>, the contact details of the official Grievance Officer are published below:
            </p>
            <div className="bg-ssk-surface p-6 rounded-2xl border border-ssk-border space-y-3">
              <h4 className="font-bold text-ssk-navy text-sm">{BRAND_CONFIG.name}</h4>
              <p className="flex items-start gap-2">
                <MapPin className="w-4 h-4 text-ssk-gold flex-shrink-0 mt-0.5" />
                <span><strong>Registered Office:</strong> {BRAND_CONFIG.contact.address}</span>
              </p>
              <p className="flex items-center gap-2">
                <Phone className="w-4 h-4 text-ssk-gold flex-shrink-0" />
                <span><strong>Support & WhatsApp Desk:</strong> {BRAND_CONFIG.contact.phone} (Mon–Sat: 10:00 AM – 7:00 PM IST)</span>
              </p>
              <p className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-ssk-gold flex-shrink-0" />
                <span><strong>Grievance Email:</strong> {BRAND_CONFIG.contact.email}</span>
              </p>
              <p className="text-[11px] text-ssk-text-secondary pt-2 border-t border-ssk-border">
                All consumer complaints and queries received by the Grievance Officer will be acknowledged within 48 hours and redressed within 30 days of receipt as mandated by government regulations.
              </p>
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  );
};
