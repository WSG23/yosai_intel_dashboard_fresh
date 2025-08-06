import React, { useEffect, useState } from 'react';
import ErrorBoundary from '../components/ErrorBoundary';
import ProgressiveSection from '../components/ProgressiveSection';
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

  const adoptionTotal = Object.values(stats.adoption).reduce(
    (sum, c) => sum + c,
    0,
  );
  const errorTotal = Object.values(stats.errors).reduce((sum, c) => sum + c, 0);
  const userCount = Object.keys(stats.proficiency).length;
  const avgProficiency =
    userCount === 0
      ? 0
      : Math.round(
          Object.values(stats.proficiency).reduce((sum, l) => sum + l, 0) /
            userCount,
        );

  return (
    <ErrorBoundary>
      <div className="usage-dashboard">
        <h1>Usage Dashboard</h1>

        <section>
          <h2>Adoption</h2>
          <p>
            {adoptionTotal} interactions across{' '}
            {Object.keys(stats.adoption).length} features
          </p>
          <ProgressiveSection
            title="Show adoption details"
            id="adoption-details"
            className="mt-2"
          >
            <ul>
              {Object.entries(stats.adoption).map(([feature, count]) => (
                <li key={feature}>
                  <details>
                    <summary>
                      {feature}: {count}
                    </summary>
                    <div className="ml-4 text-sm text-gray-600">
                      Feature {feature} has been used {count} times.
                    </div>
                  </details>
                </li>
              ))}
            </ul>
          </ProgressiveSection>
        </section>

        <section className="mt-4">
          <h2>Errors</h2>
          <p>
            {errorTotal} errors across {Object.keys(stats.errors).length}{' '}
            features
          </p>
          <ProgressiveSection
            title="Show error details"
            id="error-details"
            className="mt-2"
          >
            <ul>
              {Object.entries(stats.errors).map(([feature, count]) => (
                <li key={feature}>
                  <details>
                    <summary>
                      {feature}: {count}
                    </summary>
                    <div className="ml-4 text-sm text-gray-600">
                      {count} errors reported for {feature}.
                    </div>
                  </details>
                </li>
              ))}
            </ul>
          </ProgressiveSection>
        </section>

        <section className="mt-4">
          <h2>Proficiency Levels</h2>
          <p>
            Tracking {userCount} users. Average level: {avgProficiency}
          </p>
          <ProgressiveSection
            title="Show proficiency details"
            id="proficiency-details"
            className="mt-2"
          >
            <ul>
              {Object.entries(stats.proficiency).map(([user, level]) => (
                <li key={user}>
                  <details>
                    <summary>
                      {user}: {level}
                    </summary>
                    <div className="ml-4 text-sm text-gray-600">
                      User {user} proficiency level is {level}.
                    </div>
                  </details>
                </li>
              ))}
            </ul>
          </ProgressiveSection>
        </section>
      </div>
    </ErrorBoundary>
  );
};

export default UsageDashboard;
