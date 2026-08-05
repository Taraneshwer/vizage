import React from 'react';
import { Card } from '../common/Card';
import { AnimatedCounter } from '../common/AnimatedCounter';
import type { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: number;
  suffix?: string;
  prefix?: string;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  color?: 'primary' | 'success' | 'warning' | 'danger';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  suffix = '',
  prefix = '',
  icon: Icon,
  trend,
  color = 'primary'
}) => {
  const colorStyles = {
    primary: 'text-primary bg-primary/10',
    success: 'text-success bg-success/10',
    warning: 'text-warning bg-warning/10',
    danger: 'text-danger bg-danger/10',
  };

  return (
    <Card className="p-5 flex flex-col gap-4 relative overflow-hidden group hover:border-white/10 transition-colors">
      <div className="flex justify-between items-start">
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-400">{title}</p>
          <div className="flex items-baseline gap-1">
            <span className="text-2xl font-bold text-white tracking-tight">{prefix}</span>
            <AnimatedCounter value={value} className="text-3xl font-bold text-white tracking-tight" />
            <span className="text-xl font-medium text-gray-400 ml-1">{suffix}</span>
          </div>
        </div>
        <div className={`p-3 rounded-xl ${colorStyles[color]}`}>
          <Icon size={24} />
        </div>
      </div>
      
      {trend && (
        <div className="flex items-center gap-2 mt-2">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${trend.isPositive ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'}`}>
            {trend.isPositive ? '+' : '-'}{Math.abs(trend.value)}%
          </span>
          <span className="text-xs text-gray-500">vs last hour</span>
        </div>
      )}
      
      {/* Decorative gradient blob */}
      <div className={`absolute -bottom-12 -right-12 w-32 h-32 blur-3xl opacity-20 rounded-full bg-${color} group-hover:opacity-30 transition-opacity pointer-events-none`} />
    </Card>
  );
};
