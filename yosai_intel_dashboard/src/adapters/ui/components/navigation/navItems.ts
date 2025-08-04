import type { ComponentType } from 'react';
import { Upload, BarChart3, LineChart, Download, Settings } from 'lucide-react';

export interface NavItem {
  path: string;
  label: string;
  icon: ComponentType<{ size?: number }>;
}

export const navItems: NavItem[] = [
  { path: '/upload', label: 'Upload', icon: Upload },
  { path: '/analytics', label: 'Analytics', icon: BarChart3 },
  { path: '/graphs', label: 'Graphs', icon: LineChart },
  { path: '/export', label: 'Export', icon: Download },
  { path: '/settings', label: 'Settings', icon: Settings },
];

