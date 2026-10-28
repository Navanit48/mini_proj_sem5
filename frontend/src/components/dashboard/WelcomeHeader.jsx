import React from 'react';
import { motion } from 'framer-motion';
import { useAuth } from '../../context/AuthContext';

const WelcomeHeader = () => {
  const { user } = useAuth();
  const firstName = user?.profile?.full_name?.split(' ')[0] || 'Citizen';

  // Get greeting based on time of day
  const hour = new Date().getHours();
  let greeting = 'Good morning';
  if (hour >= 12 && hour < 17) greeting = 'Good afternoon';
  else if (hour >= 17) greeting = 'Good evening';

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: [0.25, 0.46, 0.45, 0.94] }}
      className="mb-6"
    >
      <h1 className="text-2xl sm:text-[28px] font-bold text-foreground tracking-tight">
        {greeting}, {firstName} <span className="inline-block ml-0.5">👋</span>
      </h1>
      <p className="text-sm text-muted-foreground mt-1.5 max-w-lg">
        Here's an overview of your welfare applications, documents, and scheme eligibility.
      </p>
    </motion.div>
  );
};

export default WelcomeHeader;
