import React, { useEffect, useRef, useState } from 'react';
import ForceGraph2D from 'react-force-graph';
import ForceGraph3D from 'react-force-graph-3d';
import Slider from 'rc-slider';
import 'rc-slider/assets/index.css';
import Heatmap from 'heatmap.js';
import { request, gql } from 'graphql-request';
import { AccessibleVisualization } from '../../../components/accessibility';

type Node = { id: string; label: string; properties?: Record<string, string> };
type Edge = { source: string; target: string; weight?: number };
type Graph = { nodes: Node[]; edges: Edge[] };

const GRAPHQL_ENDPOINT = '/ui/graphql';

export const GraphDashboard: React.FC = () => {
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [is3D, setIs3D] = useState(false);
  const [labelFilter, setLabelFilter] = useState('');
  const heatmapRef = useRef<HTMLDivElement>(null);
  const [heatmapInstance, setHeatmapInstance] = useState<any>(null);

  const fetchGraph = async () => {
    const query = gql`
      query($label: String) {
        graph(label: $label) {
          nodes { id label }
          edges { source target weight }
        }
      }
    `;
    const data = await request<{ graph: Graph }>(GRAPHQL_ENDPOINT, query, { label: labelFilter || null });
    setGraph(data.graph);
    if (heatmapInstance) {
      heatmapInstance.setData({
        max: 5,
        data: data.graph.nodes.map((n, i) => ({ x: i * 10, y: i * 10, value: 1 })),
      });
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [labelFilter]);

  useEffect(() => {
    if (heatmapRef.current && !heatmapInstance) {
      const instance = Heatmap.create({ container: heatmapRef.current });
      setHeatmapInstance(instance);
    }
  }, [heatmapRef, heatmapInstance]);

  const exportGraph = async (format: string) => {
    const query = gql`
      query($fmt: String!) { exportGraph(format: $fmt) }
    `;
    const data = await request<{ exportGraph: string }>(GRAPHQL_ENDPOINT, query, { fmt: format });
    const blob = new Blob([data.exportGraph], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `graph.${format}.json`;
    a.click();
  };

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
        <button
          onClick={() => setIs3D(!is3D)}
          aria-label="Toggle 3D view"
        >
          {is3D ? '2D' : '3D'}
        </button>
        <input
          placeholder="Filter by label"
          aria-label="Filter nodes by label"
          value={labelFilter}
          onChange={(e) => setLabelFilter(e.target.value)}
          style={{ marginLeft: 10 }}
        />
        <button onClick={() => exportGraph('gephi')} aria-label="Export Gephi">
          Export Gephi
        </button>
        <button
          onClick={() => exportGraph('cytoscape')}
          aria-label="Export Cytoscape"
        >
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
