import React, { useEffect, useState } from 'react';
import Hint from '../components/overlay/Hint';
import LoadingError from '../components/shared/LoadingError';
import { fetchJson } from '../public/apiClient';

const LearnMore: React.FC = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    fetchJson<string[]>('/api/analytics/suggestions')
      .then((data) => {
        setSuggestions(data);
        setError(null);
      })
      .catch((err: Error) => {
        setError(err);
        setSuggestions([]);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-4">
      <h1 className="mb-4 text-2xl font-bold">Learn More</h1>
      <LoadingError loading={loading} error={error}>
        {suggestions.length === 0 ? (
          <p>No suggestions available.</p>
        ) : (
          <ul className="pl-5 space-y-2 list-disc">
            {suggestions.map((s, idx) => (
              <li key={idx} className="flex items-center space-x-2">
                <span>{s}</span>
                <Hint id={`suggestion-${idx}`} message="Why this suggestion?" />
              </li>
            ))}
          </ul>
        )}
      </LoadingError>
    </div>
  );
};

export default LearnMore;
