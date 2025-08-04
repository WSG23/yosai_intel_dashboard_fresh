import React, { useEffect, useState } from 'react';
import { getLearningSuggestions } from '../services/analytics/usage';
import Hint from '../components/overlay/Hint';

const LearnMore: React.FC = () => {
  const [suggestions, setSuggestions] = useState<string[]>([]);

  useEffect(() => {
    const fetchSuggestions = async () => {
      const data = await getLearningSuggestions();
      setSuggestions(data);
    };
    fetchSuggestions();
  }, []);

  return (
    <div className="p-4">
      <h1 className="mb-4 text-2xl font-bold">Learn More</h1>
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
    </div>
  );
};

export default LearnMore;
