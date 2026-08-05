import React from 'react';
import { cn } from '../../utils/cn';
import { motion } from 'framer-motion';
import type { HTMLMotionProps } from 'framer-motion';

interface CardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ children, className, ...props }, ref) => {
    return (
      <motion.div
        ref={ref}
      className={cn(
        "rounded-md overflow-hidden bg-card border border-gray-200",
        className
      )}
      {...props}
    >
      {children}
      </motion.div>
    );
  }
);
Card.displayName = 'Card';
