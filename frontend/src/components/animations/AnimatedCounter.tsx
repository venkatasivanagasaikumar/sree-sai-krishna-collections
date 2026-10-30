/**
 * AnimatedCounter — smoothly animates a number counting up from 0 to the target value.
 */
import React, { useEffect, useRef, useState } from 'react';
import { useInView } from 'framer-motion';

interface AnimatedCounterProps {
  value: number;
  duration?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
  decimals?: number;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({
  value,
  duration = 1.5,
  prefix = '',
  suffix = '',
  className = '',
  decimals = 0,
}) => {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (!isInView) return;

    let startTime: number;
    let rafId: number;

    const animate = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = Math.min((timestamp - startTime) / (duration * 1000), 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(eased * value);

      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      }
    };

    rafId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(rafId);
  }, [isInView, value, duration]);

  return (
    <span ref={ref} className={className}>
      {prefix}{display.toFixed(decimals)}{suffix}
    </span>
  );
};
