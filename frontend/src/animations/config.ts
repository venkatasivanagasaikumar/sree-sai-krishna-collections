/**
 * SSK Collections - Animation Configuration
 * Centralized animation settings for a premium jewellery shopping experience.
 */

// --- Reduced Motion Detection ---
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

// --- Timing Constants ---
export const DURATION = {
  instant: 0.1,
  fast: 0.2,
  normal: 0.35,
  slow: 0.5,
  slower: 0.7,
  page: 0.45,
} as const;

export const DELAY = {
  staggerChild: 0.07,
  staggerSection: 0.12,
  heroText: 0.15,
  entrance: 0.1,
} as const;

// --- Easing Curves ---
export const EASE = {
  // Default smooth easing — elegant entrance/exit
  smooth: [0.25, 0.46, 0.45, 0.94] as [number, number, number, number],
  // Gentle deceleration for elements coming into view
  out: [0.0, 0.0, 0.2, 1.0] as [number, number, number, number],
  // Acceleration for elements exiting
  in: [0.4, 0.0, 1.0, 1.0] as [number, number, number, number],
  // Elegant ease-in-out for transforms
  elegant: [0.43, 0.13, 0.23, 0.96] as [number, number, number, number],
  // Spring-like for subtle micro-interactions
  spring: [0.34, 1.56, 0.64, 1.0] as [number, number, number, number],
} as const;

// --- Transition Presets ---
export const TRANSITION = {
  default: { duration: DURATION.normal, ease: EASE.smooth },
  fast: { duration: DURATION.fast, ease: EASE.smooth },
  slow: { duration: DURATION.slow, ease: EASE.elegant },
  page: { duration: DURATION.page, ease: EASE.out },
  spring: { type: 'spring' as const, stiffness: 300, damping: 25 },
  springGentle: { type: 'spring' as const, stiffness: 200, damping: 20 },
  springBouncy: { type: 'spring' as const, stiffness: 400, damping: 17 },
} as const;
