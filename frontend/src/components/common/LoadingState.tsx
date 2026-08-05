import React from 'react';
import { RefreshCcw } from 'lucide-react';
import { motion } from 'framer-motion';

interface LoadingStateProps {
  message?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ message = "Loading..." }) => {
  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="flex flex-col items-center justify-center h-full w-full text-gray-500 gap-4"
    >
      <RefreshCcw size={48} className="animate-spin text-primary opacity-50" />
      <p className="text-sm font-medium tracking-wide">{message}</p>
    </motion.div>
  );
};
