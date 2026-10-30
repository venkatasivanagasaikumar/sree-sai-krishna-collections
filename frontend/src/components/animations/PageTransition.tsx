/**
 * PageTransition — wraps page content in a smooth entrance/exit animation.
 */
import React from 'react';
import { motion } from 'framer-motion';
import { pageTransition } from '../../animations';
import { prefersReducedMotion } from '../../animations';

interface PageTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export const PageTransition: React.FC<PageTransitionProps> = ({ children, className = '' }) => {
  if (prefersReducedMotion()) {
    return <div className={className}>{children}</div>;
  }

  return (
    <motion.div
      variants={pageTransition}
      initial="initial"
      animate="animate"
      exit="exit"
      className={className}
    >
      {children}
    </motion.div>
  );
};
