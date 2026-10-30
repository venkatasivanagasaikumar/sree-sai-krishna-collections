/**
 * SSK Collections - Reusable Animation Variants
 * All motion variants for the premium jewellery shopping experience.
 */
import type { Variants, TargetAndTransition } from 'framer-motion';
import { DURATION, DELAY, EASE, TRANSITION } from './config';

// ─── Fade ─────────────────────────────────────────────
export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: TRANSITION.default },
  exit: { opacity: 0, transition: TRANSITION.fast },
};

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: { opacity: 1, y: 0, transition: { duration: DURATION.normal, ease: EASE.smooth } },
  exit: { opacity: 0, y: -12, transition: TRANSITION.fast },
};

export const fadeDown: Variants = {
  hidden: { opacity: 0, y: -16 },
  visible: { opacity: 1, y: 0, transition: TRANSITION.default },
  exit: { opacity: 0, y: 8, transition: TRANSITION.fast },
};

export const fadeLeft: Variants = {
  hidden: { opacity: 0, x: -30 },
  visible: { opacity: 1, x: 0, transition: TRANSITION.default },
  exit: { opacity: 0, x: -15, transition: TRANSITION.fast },
};

export const fadeRight: Variants = {
  hidden: { opacity: 0, x: 30 },
  visible: { opacity: 1, x: 0, transition: TRANSITION.default },
  exit: { opacity: 0, x: 15, transition: TRANSITION.fast },
};

// ─── Scale ────────────────────────────────────────────
export const scaleIn: Variants = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: { opacity: 1, scale: 1, transition: TRANSITION.default },
  exit: { opacity: 0, scale: 0.95, transition: TRANSITION.fast },
};

export const scaleUp: Variants = {
  hidden: { opacity: 0, scale: 0.85, y: 20 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { duration: DURATION.slow, ease: EASE.elegant } },
  exit: { opacity: 0, scale: 0.9, y: 10, transition: TRANSITION.fast },
};

// ─── Stagger Containers ──────────────────────────────
export const staggerContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: DELAY.staggerChild,
      delayChildren: DELAY.entrance,
    },
  },
};

export const staggerContainerSlow: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: DELAY.staggerSection,
      delayChildren: DELAY.entrance,
    },
  },
};

// ─── Page Transitions ─────────────────────────────────
export const pageTransition: Variants = {
  initial: { opacity: 0, y: 12 },
  animate: { opacity: 1, y: 0, transition: TRANSITION.page },
  exit: { opacity: 0, y: -8, transition: { duration: DURATION.fast, ease: EASE.in } },
};

// ─── Modal / Overlay ──────────────────────────────────
export const modalOverlay: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: DURATION.fast } },
  exit: { opacity: 0, transition: { duration: DURATION.fast } },
};

export const modalContent: Variants = {
  hidden: { opacity: 0, scale: 0.93, y: 20 },
  visible: { opacity: 1, scale: 1, y: 0, transition: { duration: DURATION.normal, ease: EASE.elegant } },
  exit: { opacity: 0, scale: 0.95, y: 10, transition: { duration: DURATION.fast, ease: EASE.in } },
};

// ─── Drawer / Slide Panel ─────────────────────────────
export const slideInRight: Variants = {
  hidden: { x: '100%', opacity: 0 },
  visible: { x: 0, opacity: 1, transition: { duration: DURATION.normal, ease: EASE.out } },
  exit: { x: '100%', opacity: 0, transition: { duration: DURATION.fast, ease: EASE.in } },
};

export const slideInLeft: Variants = {
  hidden: { x: '-100%', opacity: 0 },
  visible: { x: 0, opacity: 1, transition: { duration: DURATION.normal, ease: EASE.out } },
  exit: { x: '-100%', opacity: 0, transition: { duration: DURATION.fast, ease: EASE.in } },
};

export const slideDown: Variants = {
  hidden: { height: 0, opacity: 0, overflow: 'hidden' as const },
  visible: { height: 'auto', opacity: 1, overflow: 'hidden' as const, transition: { duration: DURATION.normal, ease: EASE.smooth } },
  exit: { height: 0, opacity: 0, overflow: 'hidden' as const, transition: { duration: DURATION.fast } },
};

// ─── Card Hover ───────────────────────────────────────
export const cardHover = {
  rest: { scale: 1, y: 0, boxShadow: '0 1px 3px rgba(0,0,0,0.06)' },
  hover: {
    scale: 1.02,
    y: -4,
    boxShadow: '0 12px 28px rgba(18,63,122,0.12)',
    transition: { duration: DURATION.fast, ease: EASE.smooth },
  },
};

// ─── Button Press ─────────────────────────────────────
export const buttonTap = {
  whileTap: { scale: 0.97 },
};

// ─── Hero Text Stagger ────────────────────────────────
export const heroContainer: Variants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: DELAY.heroText,
      delayChildren: 0.2,
    },
  },
};

export const heroChild: Variants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: DURATION.slow, ease: EASE.elegant } },
};

// ─── Counter / Number Animation ───────────────────────
export const counterIn: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: { opacity: 1, y: 0, transition: TRANSITION.default },
};

// ─── Navbar ───────────────────────────────────────────
export const navDropdown: Variants = {
  hidden: { opacity: 0, y: -8, scale: 0.97 },
  visible: { opacity: 1, y: 0, scale: 1, transition: { duration: DURATION.fast, ease: EASE.out } },
  exit: { opacity: 0, y: -4, scale: 0.98, transition: { duration: 0.15, ease: EASE.in } },
};

export const mobileMenu: Variants = {
  hidden: { height: 0, opacity: 0 },
  visible: { height: 'auto', opacity: 1, transition: { duration: DURATION.normal, ease: EASE.out } },
  exit: { height: 0, opacity: 0, transition: { duration: DURATION.fast } },
};

// ─── Toast Notification ───────────────────────────────
export const toastEnter: Variants = {
  hidden: { opacity: 0, y: 30, scale: 0.95 },
  visible: { opacity: 1, y: 0, scale: 1, transition: TRANSITION.spring },
  exit: { opacity: 0, y: 20, scale: 0.95, transition: TRANSITION.fast },
};

// ─── Skeleton Shimmer ─────────────────────────────────
export const shimmer: Variants = {
  hidden: { opacity: 0.4 },
  visible: {
    opacity: 1,
    transition: { duration: 1, repeat: Infinity, repeatType: 'reverse' as const, ease: 'easeInOut' },
  },
};

// ─── Image Reveal ─────────────────────────────────────
export const imageReveal: Variants = {
  hidden: { opacity: 0, scale: 1.05 },
  visible: { opacity: 1, scale: 1, transition: { duration: DURATION.slow, ease: EASE.elegant } },
};

// ─── Tab content ──────────────────────────────────────
export const tabContent: Variants = {
  hidden: { opacity: 0, x: 8 },
  visible: { opacity: 1, x: 0, transition: TRANSITION.fast },
  exit: { opacity: 0, x: -8, transition: { duration: 0.15 } },
};

// ─── Floating/Decorative ──────────────────────────────
export const floatSlow: TargetAndTransition = {
  y: [0, -8, 0],
  transition: { duration: 4, repeat: Infinity, ease: 'easeInOut' },
};

export const floatMedium: TargetAndTransition = {
  y: [0, -5, 0],
  transition: { duration: 3, repeat: Infinity, ease: 'easeInOut' },
};
