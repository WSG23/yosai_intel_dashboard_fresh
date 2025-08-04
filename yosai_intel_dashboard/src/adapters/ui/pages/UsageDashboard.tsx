import React, { useEffect, useState } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import {
  snapshot as getSnapshot,
  onUsageUpdate,
  UsageSnapshot,
} from '../services/analytics/usage';

const UsageDashboard: React.FC = () => {
  const [stats, setStats] = useState<UsageSnapshot>(getSnapshot());

  useEffect(() => {
    const unsub = onUsageUpdate(setStats);
    setStats(getSnapshot());
    return () => {
      unsub();
    };
  }, []);

  return (
    <ErrorBoundary>
      <div className="usage-dashboard">
        <h1>Usage Dashboard</h1>

        <section>
          <h2>Adoption</h2>
          <ul>
            {Object.entries(stats.adoption).map(([feature, count]) => (
              <li key={feature}>{feature}: {count}</li>
            ))}
          </ul>
        </section>

        <section>
          <h2>Errors</h2>
          <ul>
            {Object.entries(stats.errors).map(([feature, count]) => (
              <li key={feature}>{feature}: {count}</li>
            ))}
          </ul>
        </section>

        <section>
          <h2>Proficiency Levels</h2>
          <ul>
            {Object.entries(stats.proficiency).map(([user, level]) => (
              <li key={user}>{user}: {level}</li>
            ))}
          </ul>
        </section>
      </div>
    </ErrorBoundary>
  );
};

export default UsageDashboard;
