import type { ComponentType } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faUpload,
  faChartBar,
  faChartLine,
  faDownload,
  faCog,
} from '@fortawesome/free-solid-svg-icons';
import { t } from '../../i18n';

export interface NavItem {
  path: string;
  label: string;
  icon: ComponentType<{ size?: number }>;
}

const UploadIcon: ComponentType<{ size?: number }> = ({ size }) => (
  <FontAwesomeIcon icon={faUpload} style={{ fontSize: size }} />
);

const AnalyticsIcon: ComponentType<{ size?: number }> = ({ size }) => (
  <FontAwesomeIcon icon={faChartBar} style={{ fontSize: size }} />
);

const GraphsIcon: ComponentType<{ size?: number }> = ({ size }) => (
  <FontAwesomeIcon icon={faChartLine} style={{ fontSize: size }} />
);

const ExportIcon: ComponentType<{ size?: number }> = ({ size }) => (
  <FontAwesomeIcon icon={faDownload} style={{ fontSize: size }} />
);

const SettingsIcon: ComponentType<{ size?: number }> = ({ size }) => (
  <FontAwesomeIcon icon={faCog} style={{ fontSize: size }} />
);

export const navItems: NavItem[] = [
  { path: '/upload', label: 'Upload', icon: UploadIcon },
  { path: '/analytics', label: 'Analytics', icon: AnalyticsIcon },
  { path: '/graphs', label: 'Graphs', icon: GraphsIcon },
  { path: '/export', label: 'Export', icon: ExportIcon },
  { path: '/settings', label: t('settings.title'), icon: SettingsIcon },
];

