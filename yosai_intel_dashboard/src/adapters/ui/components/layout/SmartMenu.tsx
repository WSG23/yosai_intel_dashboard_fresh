import React, { useEffect, useMemo, useState } from 'react';

export interface SmartMenuItem {
  id: string;
  label: string;
  onSelect: () => void;
}

const USAGE_KEY = 'smartMenuUsage';
const RECENT_KEY = 'smartMenuRecent';

const loadUsage = (): Record<string, number> => {
  try {
    const raw = localStorage.getItem(USAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
};

const loadRecent = (): string[] => {
  try {
    const raw = localStorage.getItem(RECENT_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
};

const SmartMenu: React.FC<{ items: SmartMenuItem[] }> = ({ items }) => {
  const [usage, setUsage] = useState<Record<string, number>>({});
  const [recent, setRecent] = useState<string[]>([]);

  useEffect(() => {
    setUsage(loadUsage());
    setRecent(loadRecent());
  }, []);

  const handleSelect = (id: string, onSelect: () => void) => {
    const nextUsage = { ...usage, [id]: (usage[id] || 0) + 1 };
    const nextRecent = [id, ...recent.filter((r) => r !== id)].slice(0, 3);
    setUsage(nextUsage);
    setRecent(nextRecent);
    try {
      localStorage.setItem(USAGE_KEY, JSON.stringify(nextUsage));
      localStorage.setItem(RECENT_KEY, JSON.stringify(nextRecent));
    } catch {
      /* ignore */
    }
    onSelect();
  };

  const sortedItems = useMemo(
    () =>
      [...items].sort(
        (a, b) => (usage[b.id] || 0) - (usage[a.id] || 0)
      ),
    [items, usage]
  );

  const recentItems = useMemo(
    () =>
      recent
        .map((id) => items.find((i) => i.id === id))
        .filter((i): i is SmartMenuItem => Boolean(i)),
    [recent, items]
  );

  return (
    <div>
      {recentItems.length > 0 && (
        <div>
          <h4>Recently Used</h4>
          <ul>
            {recentItems.map((item) => (
              <li key={item.id}>
                <button onClick={() => handleSelect(item.id, item.onSelect)}>
                  {item.label}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <ul>
        {sortedItems.map((item) => (
          <li key={item.id}>
            <button onClick={() => handleSelect(item.id, item.onSelect)}>
              {item.label}
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default SmartMenu;
