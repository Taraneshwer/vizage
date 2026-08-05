import React from 'react';
import { cn } from '../../utils/cn';

type StatusType = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

interface StatusBadgeProps {
  status: StatusType;
  children: React.ReactNode;
  className?: string;
  dot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, children, className, dot = true }) => {
  const styles = {
    success: 'bg-success/10 text-success border-success/20',
    warning: 'bg-warning/10 text-warning border-warning/20',
    danger: 'bg-danger/10 text-danger border-danger/20',
    info: 'bg-primary/10 text-primary border-primary/20',
    neutral: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
  };

  const dotStyles = {
    success: 'bg-success',
    warning: 'bg-warning',
    danger: 'bg-danger',
    info: 'bg-primary',
    neutral: 'bg-gray-400',
  };

  return (
    <span className={cn(
      "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border",
      styles[status],
      className
    )}>
      {dot && (
        <span className={cn("w-1.5 h-1.5 rounded-full animate-pulse", dotStyles[status])} />
      )}
      {children}
    </span>
  );
};
