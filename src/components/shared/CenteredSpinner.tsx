import React from 'react';
import Spinner from './Spinner';

interface Props {
  sizeClass?: string;
  className?: string;
}

export const CenteredSpinner: React.FC<Props> = ({ sizeClass, className = '' }) => (
  <div className={`flex items-center justify-center ${className}`}>
    <Spinner sizeClass={sizeClass} />
  </div>
);

export default CenteredSpinner;
