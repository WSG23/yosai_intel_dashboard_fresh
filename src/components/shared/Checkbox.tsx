import React from 'react';

interface Props {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  icon?: React.ReactNode;
}

export const Checkbox: React.FC<Props> = ({ label, checked, onChange, icon }) => {
  return (
    <label className="flex items-center gap-2 text-sm">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="border rounded"
      />
      {icon}
      {label}
    </label>
  );
};
