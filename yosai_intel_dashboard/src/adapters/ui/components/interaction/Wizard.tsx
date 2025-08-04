import React, { useState, useEffect } from 'react';

export interface WizardStep {
  title: string;
  content: React.ReactNode;
}

export interface WizardProps {
  steps: WizardStep[];
  storageKey?: string;
}

const Wizard: React.FC<WizardProps> = ({ steps, storageKey }) => {
  const [current, setCurrent] = useState(0);

  useEffect(() => {
    if (!storageKey) return;
    const saved = Number(window.localStorage.getItem(storageKey));
    if (!Number.isNaN(saved) && saved >= 0 && saved < steps.length) {
      setCurrent(saved);
    }
  }, [storageKey, steps.length]);

  const persist = (value: number) => {
    if (storageKey) {
      window.localStorage.setItem(storageKey, String(value));
    }
  };

  const goTo = (index: number) => {
    setCurrent(index);
    persist(index);
  };

  const next = () => {
    if (current < steps.length - 1) {
      goTo(current + 1);
    }
  };

  const prev = () => {
    if (current > 0) {
      goTo(current - 1);
    }
  };

  const skip = () => {
    next();
  };

  return (
    <div className="wizard">
      <div className="flex mb-4 space-x-2" role="tablist">
        {steps.map((step, index) => (
          <button
            key={step.title}
            type="button"
            className={`px-3 py-1 rounded-md text-sm border ${
              index === current
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-600'
            }`}
            onClick={() => goTo(index)}
            aria-selected={index === current}
            role="tab"
          >
            {step.title}
          </button>
        ))}
      </div>

      <div className="mb-4" role="tabpanel">
        {steps[current]?.content}
      </div>

      <div className="flex space-x-2">
        <button
          type="button"
          onClick={prev}
          disabled={current === 0}
          className="px-3 py-1 border rounded-md disabled:opacity-50"
        >
          Back
        </button>
        <button
          type="button"
          onClick={skip}
          disabled={current === steps.length - 1}
          className="px-3 py-1 border rounded-md disabled:opacity-50"
        >
          Skip
        </button>
        <button
          type="button"
          onClick={next}
          disabled={current === steps.length - 1}
          className="px-3 py-1 border rounded-md disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default Wizard;
