import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, Mail, MapPin, Send, CheckCircle2, AlertCircle, Clock, MessageSquare, Loader2 } from 'lucide-react';
import { PageTransition } from '../../components/animations/PageTransition';
import { BRAND_CONFIG } from '../../assets/brand.config';
import { api } from '../../services/api';
import { fadeDown } from '../../animations';

export const ContactPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [subject, setSubject] = useState('Product Inquiry');
  const [message, setMessage] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await api.submitContactInquiry({
        name: name.trim(),
        email: email.trim(),
        phone: phone.trim(),
        subject,
        message: message.trim()
      });
      setSubmitted(true);
      setName('');
      setEmail('');
      setPhone('');
      setMessage('');
    } catch (err: any) {
      setError(err.message || 'Failed to submit inquiry. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <PageTransition className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      <div className="text-center space-y-3">
        <span className="text-xs font-bold text-ssk-gold uppercase tracking-widest px-3.5 py-1 bg-ssk-gold/10 rounded-full border border-ssk-gold/30">
          We Are Here For You
        </span>
        <h1 className="text-3xl sm:text-4xl font-serif font-bold text-ssk-navy">
          Contact Customer Support
        </h1>
        <p className="text-xs sm:text-sm text-ssk-text-secondary max-w-xl mx-auto">
          Have a question about a product, custom bridal requirement, sizing, or shipment? Reach out and our Secunderabad team will assist you.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Contact Information Cards */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border shadow-sm space-y-6 text-xs text-ssk-text">
            <h3 className="text-base font-serif font-bold text-ssk-navy pb-3 border-b border-ssk-border">
              Store & Flagship Desk
            </h3>

            <div className="space-y-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-ssk-blue-light text-ssk-navy flex items-center justify-center flex-shrink-0">
                  <MapPin className="w-5 h-5 text-ssk-gold" />
                </div>
                <div>
                  <span className="font-bold block text-ssk-navy">Flagship Address</span>
                  <p className="text-ssk-text-secondary leading-relaxed mt-0.5">{BRAND_CONFIG.contact.address}</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-ssk-blue-light text-ssk-navy flex items-center justify-center flex-shrink-0">
                  <Phone className="w-5 h-5 text-ssk-gold" />
                </div>
                <div>
                  <span className="font-bold block text-ssk-navy">Phone & WhatsApp Support</span>
                  <p className="text-ssk-text-secondary mt-0.5">{BRAND_CONFIG.contact.phone}</p>
                  <p className="text-[11px] text-ssk-text-muted">Mon – Sat: 10:00 AM – 7:00 PM IST</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-xl bg-ssk-blue-light text-ssk-navy flex items-center justify-center flex-shrink-0">
                  <Mail className="w-5 h-5 text-ssk-gold" />
                </div>
                <div>
                  <span className="font-bold block text-ssk-navy">Email Desk</span>
                  <p className="text-ssk-text-secondary mt-0.5">{BRAND_CONFIG.contact.email}</p>
                  <p className="text-[11px] text-ssk-text-muted">Average response time: within 24 hours</p>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-r from-ssk-navy-dark to-ssk-navy p-6 rounded-3xl text-white space-y-2 border-2 border-ssk-gold/30">
            <h4 className="font-serif font-bold text-sm text-ssk-gold">Wholesale & Bridal Inquiries</h4>
            <p className="text-xs text-gray-200 leading-relaxed">
              Looking for bulk return-gift sets for traditional events, weddings, or boutique inquiries? Chat directly with our bridal specialists on WhatsApp.
            </p>
          </div>
        </div>

        {/* Contact Form */}
        <div className="lg:col-span-7 bg-white p-6 sm:p-8 rounded-3xl border border-ssk-border shadow-sm space-y-6">
          <div>
            <h2 className="text-lg font-serif font-bold text-ssk-navy">Send Us a Direct Message</h2>
            <p className="text-xs text-ssk-text-secondary mt-1">
              Fill in your details and message below. We will get back to you promptly.
            </p>
          </div>

          <AnimatePresence>
            {submitted && (
              <motion.div
                variants={fadeDown}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="p-4 bg-green-50 border border-green-200 text-green-800 text-xs rounded-2xl flex items-center gap-3"
              >
                <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0" />
                <span>
                  Thank you! Your message has been sent to our team. We will contact you shortly.
                </span>
              </motion.div>
            )}

            {error && (
              <motion.div
                variants={fadeDown}
                initial="hidden"
                animate="visible"
                exit="exit"
                className="p-4 bg-red-50 border border-red-200 text-red-700 text-xs rounded-2xl flex items-center gap-3"
              >
                <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                <span>{error}</span>
              </motion.div>
            )}
          </AnimatePresence>

          <form onSubmit={handleSubmit} className="space-y-4 text-xs">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-ssk-text mb-1">Your Name *</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ananya Rao"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>
              <div>
                <label className="block font-semibold text-ssk-text mb-1">Email Address *</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="ananya@example.com"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block font-semibold text-ssk-text mb-1">Phone Number (Optional)</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold transition-colors"
                />
              </div>
              <div>
                <label className="block font-semibold text-ssk-text mb-1">Topic / Subject</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold transition-colors"
                >
                  <option value="Product Inquiry">Product Inquiry</option>
                  <option value="Order Tracking">Order & Delivery Inquiry</option>
                  <option value="Return or Replacement">Return or Replacement Request</option>
                  <option value="Bridal / Bulk Order">Bridal / Bulk Order</option>
                  <option value="Feedback">Feedback / Suggestion</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block font-semibold text-ssk-text mb-1">Your Message *</label>
              <textarea
                required
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Please describe how we can assist you..."
                className="w-full px-3.5 py-2.5 bg-ssk-surface border border-ssk-border rounded-xl focus:outline-none focus:border-ssk-gold transition-colors resize-none"
              />
            </div>

            <motion.button
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={isSubmitting}
              className="px-8 py-3 bg-ssk-navy hover:bg-ssk-navy-dark text-white rounded-xl font-bold flex items-center justify-center gap-2 shadow-md transition-all disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Sending Message...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 text-ssk-gold" />
                  <span>Send Message</span>
                </>
              )}
            </motion.button>
          </form>
        </div>
      </div>
    </PageTransition>
  );
};
