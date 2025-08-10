import React, { useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph';
import ForceGraph3D from 'react-force-graph-3d';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import Heatmap from 'heatmap.js';
import { AccessibleVisualization } from '../../../components/accessibility';

export type Node = { id: string; label: string; properties?: Record<string, string> };
export type Edge = { source: string; target: string; weight?: number };
export type Graph = { nodes: Node[]; edges: Edge[] };

type GraphDashboardProps = {
  graph: Graph;
  is3D: boolean;
  labelFilter: string;
  onToggle3D: () => void;
  onFilterChange: (value: string) => void;
  onExport: (format: string) => void;
};

const GraphDashboardComponent: React.FC<GraphDashboardProps> = ({
  graph,
  is3D,
  labelFilter,
  onToggle3D,
  onFilterChange,
  onExport,
}) => {
  const heatmapRef = useRef<HTMLDivElement>(null);
  const heatmapInstanceRef = useRef<any>(null);

  useEffect(() => {
    if (heatmapRef.current && !heatmapInstanceRef.current) {
      heatmapInstanceRef.current = Heatmap.create({ container: heatmapRef.current });
    }
  }, []);

  useEffect(() => {
    if (heatmapInstanceRef.current) {
      heatmapInstanceRef.current.setData({
        max: 5,
        data: graph.nodes.map((n, i) => ({ x: i * 10, y: i * 10, value: 1 })),
      });
    }
  }, [graph]);

  const graphVisualization = is3D ? (
    <ForceGraph3D graphData={graph} />
  ) : (
    <ForceGraph2D graphData={graph} />
  );

  const graphComponent = (
    <AccessibleVisualization
      title="Security Graph"
      summary={`Graph with ${graph.nodes.length} nodes and ${graph.edges.length} edges.`}
      tableData={{
        headers: ['Node ID', 'Label'],
        rows: graph.nodes.map((n) => [n.id, n.label]),
      }}
    >
      {graphVisualization}
    </AccessibleVisualization>
  );

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <div style={{ position: 'absolute', top: 10, left: 10, zIndex: 10 }}>
        <button onClick={onToggle3D} aria-label="Toggle 3D view">
          {is3D ? '2D' : '3D'}
        </button>
        <input
          placeholder="Filter by label"
          aria-label="Filter nodes by label"
          value={labelFilter}
          onChange={(e) => onFilterChange(e.target.value)}
          style={{ marginLeft: 10 }}
        />
        <button onClick={() => onExport('gephi')} aria-label="Export Gephi">
          Export Gephi
        </button>
        <button onClick={() => onExport('cytoscape')} aria-label="Export Cytoscape">
          Export Cytoscape
        </button>
        <div style={{ width: 200, marginTop: 10 }}>
          <Slider min={0} max={100} defaultValue={0} aria-label="Graph slider" />
        </div>
      </div>
      {graphComponent}
      <div
        ref={heatmapRef}
        style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none' }}
      />
    </div>
  );
};

export const GraphDashboard = React.memo(GraphDashboardComponent);
