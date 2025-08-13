import React from 'react';
import Spinner, { SpinnerProps } from './Spinner';

type CenteredSpinnerProps = SpinnerProps;

const CenteredSpinner: React.FC<CenteredSpinnerProps> = ({
  sizeClass,
  className = '',
}) => (
  <div className={`flex items-center justify-center ${className}`}>
    <Spinner sizeClass={sizeClass} />
  </div>
);

export default CenteredSpinner;
