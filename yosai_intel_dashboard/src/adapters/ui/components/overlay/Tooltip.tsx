import React, { useState } from 'react';

interface TooltipProps {
  text: string;
  children: React.ReactNode;
  onOpen?: () => void;
}

const Tooltip: React.FC<TooltipProps> = ({ text, children, onOpen }) => {
  const [visible, setVisible] = useState(false);

  const show = () => {
    if (!visible) {
      onOpen?.();
    }
    setVisible(true);
  };

  const hide = () => setVisible(false);

  return (
    <div
      className="relative inline-block"
      onMouseEnter={show}
      onMouseLeave={hide}
    >
      {children}
      {visible && (
        <div className="absolute z-10 p-2 text-sm text-white bg-gray-800 rounded shadow-md whitespace-nowrap">
          {text}
        </div>
      )}
    </div>
  );
};

export default Tooltip;
export { Tooltip };
