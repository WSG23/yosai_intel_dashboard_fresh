import React from 'react';

interface ThresholdSliderProps {
  value: number;
  min?: number;
  max?: number;
  step?: number;
  onChange: (value: number) => void;
}

const ThresholdSlider: React.FC<ThresholdSliderProps> = ({
  value,
  min = 0,
  max = 100,
  step = 1,
  onChange,
}) => (
  <div className="flex flex-col space-y-2" style={{ touchAction: 'none' }}>
    <input
      type="range"
      min={min}
      max={max}
      step={step}
      value={value}
      onChange={(e) => onChange(Number(e.target.value))}
      onTouchStart={(e) => e.stopPropagation()}
      onPointerDown={(e) => e.stopPropagation()}
    />
    <span className="text-center">{value}</span>
  </div>
);

export default ThresholdSlider;
