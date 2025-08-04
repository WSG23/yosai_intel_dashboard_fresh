import React, { useState, useRef } from 'react';
import { getPreferences } from '../services/preferences';
import { saveTemplate, loadTemplate, ChartTemplate } from '../lib/dashboardTemplates';
import { TaskLauncher, Wizard } from '../components/interaction';

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

  const workspaceStyle: React.CSSProperties = {
    position: 'relative',
    flex: 1,
    background: prefs.colorScheme === 'dark' ? '#1f2937' : '#f9fafb',
  };

  const designStep = (
    <div style={{ display: 'flex', height: '100%' }}>
      <div style={{ width: 200, padding: 10, borderRight: '1px solid #ccc' }}>
        <h3>Charts</h3>
        {chartTypes.map((type) => (
          <div
            key={type}
            draggable
            onDragStart={(e) => handleDragStart(e, type)}
            style={{ marginBottom: 8, padding: 4, border: '1px solid #ddd', cursor: 'grab' }}
          >
            {type} Chart
          </div>
        ))}
        <button onClick={saveCurrent} style={{ marginTop: 10, display: 'block' }}>Save Template</button>
        <button onClick={loadCurrent} style={{ marginTop: 4, display: 'block' }}>Load Template</button>
      </div>
      <div
        ref={workspaceRef}
        style={workspaceStyle}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {charts.map((chart) => (
          <div
            key={chart.id}
            draggable
            onDragStart={(e) => handleContainerDragStart(e, chart.id)}
            onMouseUp={(e) => handleResize(chart.id, e.currentTarget as HTMLDivElement)}
            style={{
              position: 'absolute',
              top: chart.y,
              left: chart.x,
              width: chart.w,
              height: chart.h,
              border: '1px solid #999',
              background: '#fff',
              resize: 'both',
              overflow: 'auto',
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
