import React, { useState, useRef } from 'react';
import { getPreferences } from '../services/preferences';
import { saveTemplate, loadTemplate, ChartTemplate } from '../lib/dashboardTemplates';
import { ChunkGroup } from '../components/layout';


const chartTypes = ['Line', 'Bar', 'Pie'];

const DashboardBuilder: React.FC = () => {
  const prefs = getPreferences();
  const [charts, setCharts] = useState<ChartTemplate[]>(() => loadTemplate('default') || []);
  const workspaceRef = useRef<HTMLDivElement>(null);

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, type: string) => {
    e.dataTransfer.setData('chart-type', type);
  };

  const handleContainerDragStart = (e: React.DragEvent<HTMLDivElement>, id: string) => {
    const chart = charts.find((c) => c.id === id);
    if (!chart) return;
    e.dataTransfer.setData('move-id', id);
    e.dataTransfer.setData('offset-x', String(e.clientX - chart.x));
    e.dataTransfer.setData('offset-y', String(e.clientY - chart.y));
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const rect = workspaceRef.current?.getBoundingClientRect();
    const offsetX = rect ? rect.left : 0;
    const offsetY = rect ? rect.top : 0;

    const moveId = e.dataTransfer.getData('move-id');
    if (moveId) {
      const ox = Number(e.dataTransfer.getData('offset-x'));
      const oy = Number(e.dataTransfer.getData('offset-y'));
      const x = e.clientX - offsetX - ox;
      const y = e.clientY - offsetY - oy;
      setCharts((prev) => prev.map((c) => (c.id === moveId ? { ...c, x, y } : c)));
      return;
    }

    const type = e.dataTransfer.getData('chart-type');
    if (!type) return;
    const id = Date.now().toString();
    const x = e.clientX - offsetX;
    const y = e.clientY - offsetY;
    const newChart: ChartTemplate = { id, type, x, y, w: 200, h: 150 };
    setCharts((prev) => [...prev, newChart]);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => e.preventDefault();

  const handleResize = (id: string, el: HTMLDivElement) => {
    const { offsetWidth, offsetHeight } = el;
    setCharts((prev) => prev.map((c) => (c.id === id ? { ...c, w: offsetWidth, h: offsetHeight } : c)));
  };

  const saveCurrent = () => saveTemplate('default', charts);
  const loadCurrent = () => {
    const tpl = loadTemplate('default');
    if (tpl) setCharts(tpl);
  };

  const workspaceClasses = `relative flex-1 ${
    prefs.colorScheme === 'dark' ? 'bg-gray-800' : 'bg-gray-50'
  }`;

  const designStep = (
    <div className="flex h-full">
      <div className="w-48 md:w-56 p-2.5 border-r border-gray-300 space-y-2">
        <ChunkGroup>
          <h3>Charts</h3>
          {chartTypes.map((type) => (
            <div
              key={type}
              draggable
              onDragStart={(e) => handleDragStart(e, type)}
              className="mb-2 p-1 border border-gray-300 cursor-grab"
            >
              {type} Chart
            </div>
          ))}
          <button onClick={saveCurrent} className="mt-2 block">
            Save Template
          </button>
          <button onClick={loadCurrent} className="mt-1 block">
            Load Template
          </button>
        </ChunkGroup>
      </div>
      <div
        ref={workspaceRef}
        className={workspaceClasses}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {charts.map((chart) => (
          <div
            key={chart.id}
            draggable
            onDragStart={(e) => handleContainerDragStart(e, chart.id)}
            onMouseUp={(e) =>
              handleResize(chart.id, e.currentTarget as HTMLDivElement)
            }
            className="absolute border border-gray-400 bg-white resize overflow-auto"
            style={{
              top: chart.y,
              left: chart.x,
              width: chart.w,
              height: chart.h,
              transition: `all ${prefs.animationSpeed}s`,
            }}
          >
            <strong>{chart.type} Chart</strong>
          </div>
        ))}
      </div>
    </div>
  );

  const steps = [
    { title: 'Design', content: designStep },
    { title: 'Review', content: <div>Review your dashboard before saving.</div> },
  ];

  return (
    <>
      <TaskLauncher />
      <Wizard steps={steps} storageKey="dashboard-builder-wizard" />
    </>
  );
};

export default DashboardBuilder;
