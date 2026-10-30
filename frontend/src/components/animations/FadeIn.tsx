/**
 * FadeIn — simple fade entrance with optional direction.
 */
import React from 'react';
import { motion, type Variants } from 'framer-motion';
import { fadeIn, fadeUp, fadeLeft, fadeRight, fadeDown } from '../../animations';
import { prefersReducedMotion } from '../../animations';

const directionMap: Record<string, Variants> = {
  none: fadeIn,
  up: fadeUp,
  down: fadeDown,
  left: fadeLeft,
  right: fadeRight,
};

interface FadeInProps {
  children: React.ReactNode;
  direction?: 'none' | 'up' | 'down' | 'left' | 'right';
  className?: string;
  delay?: number;
  duration?: number;
  once?: boolean;
  useViewport?: boolean;
}

export const FadeIn: React.FC<FadeInProps> = ({
  children,
  direction = 'up',
  className = '',
  delay = 0,
  duration,
  once = true,
  useViewport = true,
}) => {
  if (prefersReducedMotion()) {
    return <div className={className}>{children}</div>;
  }

  const variants = directionMap[direction] || fadeUp;

  const viewportProps = useViewport
    ? { whileInView: 'visible' as const, viewport: { once, amount: 0.15 } }
    : { animate: 'visible' as const };

  return (
    <motion.div
      variants={variants}
      initial="hidden"
      {...viewportProps}
      transition={delay || duration ? { delay, ...(duration ? { duration } : {}) } : undefined}
      className={className}
    >
      {children}
    </motion.div>
  );
};
