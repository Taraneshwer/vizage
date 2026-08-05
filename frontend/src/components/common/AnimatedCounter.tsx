import React, { useEffect } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

interface AnimatedCounterProps {
  value: number;
  className?: string;
  format?: (val: number) => string;
}

export const AnimatedCounter: React.FC<AnimatedCounterProps> = ({ 
  value, 
  className,
  format = Math.round 
}) => {
  const spring = useSpring(0, { mass: 1, stiffness: 50, damping: 15 });
  const displayValue = useTransform(spring, (current) => format(current));

  useEffect(() => {
    spring.set(value);
  }, [value, spring]);

  return (
    <motion.span className={className}>
      {displayValue as any}
    </motion.span>
  );
};
