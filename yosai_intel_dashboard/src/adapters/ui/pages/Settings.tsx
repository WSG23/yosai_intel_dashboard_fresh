import React, { useEffect, useState } from 'react';
import { api } from '../api/client';
import ErrorBoundary from '../components/ErrorBoundary';
import { ChunkGroup } from '../components/layout';
import { t } from '../i18n';

interface UserSettings {
  theme: string;
  itemsPerPage: number;
}

const Settings: React.FC = () => {
  const [settings, setSettings] = useState<UserSettings>({
    theme: 'light',
    itemsPerPage: 10,
  });
  const [status, setStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<UserSettings>('/settings')
      .then((data) => setSettings((prev) => ({ ...prev, ...data })))
      .catch(() => {
        /* ignore load errors */
      });
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setSettings((prev) => ({ ...prev, [name]: name === 'itemsPerPage' ? Number(value) : value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('saving');
    api
      .put('/settings', settings)
      .then(() => {
        setStatus('success');
        setError(null);
      })
      .catch((err) => {
        setStatus('error');
        setError(err.message);
      });
  };

  return (
    <div className="page-container">
      <h1 className="mb-4">{t('settings.title')}</h1>
      <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
        <ChunkGroup>
          <div>
            <label htmlFor="theme" className="block font-semibold mb-1">
              {t('settings.theme')}
            </label>
            <select
              id="theme"
              name="theme"
              value={settings.theme}
              onChange={handleChange}
              className="border rounded p-2 w-full"
            >
              <option value="light">{t('settings.theme_light')}</option>
              <option value="dark">{t('settings.theme_dark')}</option>
            </select>
          </div>
          <div>
            <label htmlFor="itemsPerPage" className="block font-semibold mb-1">
              {t('settings.items_per_page')}
            </label>
            <input
              type="number"
              id="itemsPerPage"
              name="itemsPerPage"
              value={settings.itemsPerPage}
              onChange={handleChange}
              className="border rounded p-2 w-full"
            />
          </div>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded"
            disabled={status === 'saving'}
          >
            {status === 'saving' ? t('settings.saving') : t('settings.save')}
          </button>
          {status === 'success' && (
            <p className="text-green-600">{t('settings.saved')}</p>
          )}
          {status === 'error' && <p className="text-red-600">{error}</p>}
        </ChunkGroup>
      </form>
    </div>
  );
};

const SettingsPage: React.FC = () => (
  <ErrorBoundary>
    <Settings />
  </ErrorBoundary>
);

export default SettingsPage;

