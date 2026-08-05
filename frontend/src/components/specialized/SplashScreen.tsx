import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const loadingSteps = [
  "Loading AI Models",
  "Loading YOLO11",
  "Loading AdaFace",
  "Loading MediaPipe",
  "Loading FAISS",
  "Initializing Recognition Engine",
  "Opening Dashboard"
];

interface SplashScreenProps {
  onComplete: () => void;
}

export const SplashScreen: React.FC<SplashScreenProps> = ({ onComplete }) => {
  const [stepIndex, setStepIndex] = useState(0);

  useEffect(() => {
    if (stepIndex < loadingSteps.length) {
      const timer = setTimeout(() => {
        setStepIndex(s => s + 1);
      }, 600); // 600ms per step
      return () => clearTimeout(timer);
    } else {
      const completeTimer = setTimeout(() => {
        onComplete();
      }, 500);
      return () => clearTimeout(completeTimer);
    }
  }, [stepIndex, onComplete]);

  const progress = Math.min(((stepIndex) / loadingSteps.length) * 100, 100);

  return (
    <div className="fixed inset-0 z-[100] bg-background flex flex-col items-center justify-center text-gray-900">
      <div className="w-80 flex flex-col items-center gap-8">
        <div className="flex flex-col items-center gap-4">
          <div className="w-16 h-16 bg-primary text-gray-900 flex items-center justify-center text-3xl font-bold rounded-md shadow-lg shadow-primary/20">
            M
          </div>
          <div className="text-center">
            <h1 className="text-2xl font-bold tracking-tight text-gray-900">Vizage</h1>
            <p className="text-xs text-gray-600 mt-1 uppercase tracking-widest">Enterprise Security System</p>
          </div>
        </div>

        <div className="w-full space-y-3">
          <div className="h-1 w-full bg-gray-200 rounded-full overflow-hidden">
            <motion.div 
              className="h-full bg-primary"
              initial={{ width: 0 }}
              animate={{ width: `${progress}%` }}
              transition={{ ease: "easeInOut", duration: 0.5 }}
            />
          </div>
          
          <div className="h-6 flex items-center justify-center overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.span
                key={stepIndex}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="text-xs text-gray-600 font-mono"
              >
                {loadingSteps[stepIndex] || "Ready."}
              </motion.span>
            </AnimatePresence>
          </div>
        </div>
      </div>
    </div>
  );
};
