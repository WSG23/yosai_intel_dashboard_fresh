import React, { useEffect, useState } from 'react';
import CenteredSpinner from './shared/CenteredSpinner';
import { eventBus } from '../eventBus';

const GlobalLoading: React.FC = () => {
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const off = eventBus.on<boolean>('loading', setLoading);
    return off;
  }, []);

  if (!loading) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/20">
      <CenteredSpinner />
    </div>
  );
};

export default GlobalLoading;
