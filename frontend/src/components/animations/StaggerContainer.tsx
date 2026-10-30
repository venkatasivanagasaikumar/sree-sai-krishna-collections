/**
 * StaggerContainer — container that staggers its children's entrance animations.
 */
import React from 'react';
import { motion, type Variants } from 'framer-motion';
import { staggerContainer } from '../../animations';
import { prefersReducedMotion } from '../../animations';

interface StaggerContainerProps {
  children: React.ReactNode;
  variants?: Variants;
  className?: string;
  once?: boolean;
  amount?: number;
  useViewport?: boolean;
}

export const StaggerContainer: React.FC<StaggerContainerProps> = ({
  children,
  variants = staggerContainer,
  className = '',
  once = true,
  amount = 0.1,
  useViewport = true,
}) => {
  if (prefersReducedMotion()) {
    return <div className={className}>{children}</div>;
  }

  const viewportProps = useViewport
    ? { whileInView: 'visible' as const, viewport: { once, amount } }
    : { animate: 'visible' as const };

  return (
    <motion.div
      variants={variants}
      initial="hidden"
      {...viewportProps}
      className={className}
    >
      {children}
    </motion.div>
  );
};
