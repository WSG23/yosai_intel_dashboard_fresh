import React from 'react';
import { Link } from 'react-router-dom';
import { Upload, LayoutDashboard, BarChart3, Filter } from 'lucide-react';

interface TaskTemplate {
  name: string;
  href: string;
  description?: string;
  icon?: React.ComponentType<{ className?: string }>;
}

const defaultTemplates: TaskTemplate[] = [
  {
    name: 'Upload Data',
    href: '/upload',
    description: 'Upload and process new data files',
    icon: Upload,
  },
  {
    name: 'Build Dashboard',
    href: '/builder',
    description: 'Create custom dashboard layouts',
    icon: LayoutDashboard,
  },
  {
    name: 'Run Analytics',
    href: '/analytics',
    description: 'Explore security analytics',
    icon: BarChart3,
  },
  {
    name: 'Query Data',
    href: '/query-builder',
    description: 'Construct complex data queries',
    icon: Filter,
  },
];

export interface TaskLauncherProps {
  templates?: TaskTemplate[];
  onSelect?: (template: TaskTemplate) => void;
}

const TaskLauncher: React.FC<TaskLauncherProps> = ({
  templates = defaultTemplates,
  onSelect,
}) => {
  return (
    <div className="mb-6">
      <h2 className="text-lg font-semibold mb-3">What would you like to do?</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
        {templates.map((tpl) => {
          const Icon = tpl.icon;
          return (
            <Link
              key={tpl.name}
              to={tpl.href}
              onClick={() => onSelect?.(tpl)}
              className="flex flex-col p-4 border rounded-md hover:bg-gray-50 transition-colors"
            >
              {Icon && <Icon className="h-6 w-6 mb-2 text-blue-600" />}
              <span className="font-medium">{tpl.name}</span>
              {tpl.description && (
                <span className="text-sm text-gray-600">{tpl.description}</span>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
};

export default TaskLauncher;
