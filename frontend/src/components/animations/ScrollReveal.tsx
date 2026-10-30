/**
 * ScrollReveal — triggers fade+slide animation when an element scrolls into view.
 * Uses Intersection Observer via framer-motion's whileInView.
 */
import React from 'react';
import { motion, type Variants } from 'framer-motion';
import { fadeUp } from '../../animations';
import { prefersReducedMotion } from '../../animations';

interface ScrollRevealProps {
  children: React.ReactNode;
  variants?: Variants;
  className?: string;
  delay?: number;
  once?: boolean;
  amount?: number;
}

export const ScrollReveal: React.FC<ScrollRevealProps> = ({
  children,
  variants = fadeUp,
  className = '',
  delay = 0,
  once = true,
  amount = 0.15,
}) => {
  if (prefersReducedMotion()) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      variants={variants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once, amount }}
      transition={delay ? { delay } : undefined}
      className={className}
    >
      {children}
    </motion.div>
  );
};
