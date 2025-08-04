import React from 'react';
import { motion } from 'framer-motion';
import { defaultSpring } from './springs';

export const FadeIn: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={defaultSpring}>
    {children}
  </motion.div>
);
