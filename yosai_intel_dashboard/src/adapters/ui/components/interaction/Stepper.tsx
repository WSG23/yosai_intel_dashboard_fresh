import React, { useState, useMemo } from 'react';

export interface Step<TContext = unknown> {
  id: string;
  label: string;
  content: React.ReactNode;
  /**
   * Optional step can be skipped via the provided skip handler.
   */
  optional?: boolean;
  /**
   * Branching logic to determine the next step. If provided as a function,
   * the function receives the supplied context and should return the id of
   * the next step. Returning `undefined` or `null` will terminate the flow.
   * If a string is provided the stepper will navigate to that step id.
   */
  next?: string | ((context: TContext) => string | undefined | null);
}

interface StepperProps<TContext = unknown> {
  steps: Step<TContext>[];
  /** Optional context passed to branching functions */
  context?: TContext;
  initialStepId?: string;
}

const Stepper = <TContext,>({ steps, context, initialStepId }: StepperProps<TContext>) => {
  const stepMap = useMemo(() => new Map(steps.map((s) => [s.id, s])), [steps]);
  const [current, setCurrent] = useState<string>(initialStepId ?? steps[0]?.id);

  const currentIndex = steps.findIndex((s) => s.id === current);
  const currentStep = stepMap.get(current);

  const goTo = (id?: string | null) => {
    if (id && stepMap.has(id)) {
      setCurrent(id);
    }
  };

  const nextId = (): string | undefined => {
    if (!currentStep) return undefined;
    if (typeof currentStep.next !== 'undefined') {
      const target =
        typeof currentStep.next === 'function'
          ? currentStep.next(context as TContext)
          : currentStep.next;
      return target ?? undefined;
    }
    return steps[currentIndex + 1]?.id;
  };

  const handleNext = () => {
    const target = nextId();
    goTo(target);
  };

  const handleBack = () => {
    const prev = steps[currentIndex - 1];
    goTo(prev?.id);
  };

  const handleSkip = () => {
    const nextSeq = steps[currentIndex + 1];
    goTo(nextSeq?.id);
  };

  return (
    <div>
      <div className="flex space-x-2 mb-4">
        {steps.map((s, idx) => (
          <div
            key={s.id}
            className={`px-2 py-1 rounded border text-sm ${
              idx === currentIndex ? 'bg-blue-500 text-white' : 'bg-gray-200'
            }`}
          >
            {s.label}
            {s.optional && <span className="ml-1 text-xs">(optional)</span>}
          </div>
        ))}
      </div>

      <div>{currentStep?.content}</div>

      <div className="mt-4 flex justify-between">
        <button
          type="button"
          onClick={handleBack}
          disabled={currentIndex <= 0}
          className="px-3 py-1 rounded bg-gray-200 disabled:opacity-50"
        >
          Back
        </button>
        <div className="space-x-2 ml-auto">
          {currentStep?.optional && (
            <button
              type="button"
              onClick={handleSkip}
              className="px-3 py-1 rounded bg-yellow-200"
            >
              Skip
            </button>
          )}
          {nextId() && (
            <button
              type="button"
              onClick={handleNext}
              className="px-3 py-1 rounded bg-blue-500 text-white"
            >
              Next
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default Stepper;
