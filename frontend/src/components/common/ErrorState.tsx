import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from './Button';

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  title = "Connection Error", 
  message = "Failed to communicate with the server. Is the backend offline?", 
  onRetry 
}) => {
  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center h-full w-full p-6 text-center max-w-md mx-auto"
    >
      <div className="w-16 h-16 rounded-full bg-danger/10 text-danger flex items-center justify-center mb-4">
        <AlertTriangle size={32} />
      </div>
      <h3 className="text-xl font-bold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-600 text-sm mb-6">{message}</p>
      {onRetry && (
        <Button variant="outline" className="border-danger/20 text-danger hover:bg-danger/10 hover:text-danger" onClick={onRetry}>
          Try Again
        </Button>
      )}
    </motion.div>
  );
};
