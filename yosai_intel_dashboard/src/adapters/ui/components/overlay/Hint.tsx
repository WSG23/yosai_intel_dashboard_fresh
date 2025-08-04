import React from 'react';
import { Info } from 'lucide-react';
import Tooltip from './Tooltip';
import { logTipInteraction } from '../../services/analytics/usage';

interface HintProps {
  id: string;
  message: string;
}

const Hint: React.FC<HintProps> = ({ id, message }) => {
  const handleClick = () => {
    logTipInteraction({ id, action: 'click' });
  };

  const handleView = () => {
    logTipInteraction({ id, action: 'view' });
  };

  return (
    <Tooltip text={message} onOpen={handleView}>
      <button
        onClick={handleClick}
        className="text-blue-600 hover:text-blue-800 focus:outline-none"
        aria-label="Hint"
      >
        <Info size={16} />
      </button>
    </Tooltip>
  );
};

export default Hint;
export { Hint };
