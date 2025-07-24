import React, { useState } from 'react';
import { useCallbackApi } from './useCallbackApi';

const CustomFieldToggle: React.FC = () => {
  const { toggleCustomField } = useCallbackApi();
  const [value, setValue] = useState('');
  const [style, setStyle] = useState<Record<string, string>>({});

  const handleChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setValue(val);
    const res = await toggleCustomField(val);
    setStyle(res);
  };

  return (
    <div>
      <select value={value} onChange={handleChange} aria-label="Select field">
        <option value="">Choose</option>
        <option value="other">Other</option>
        <option value="ignore">Ignore</option>
      </select>
      <input type="text" style={style} aria-label="Custom field" />
    </div>
  );
};

export default CustomFieldToggle;
