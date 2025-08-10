import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { GraphDashboard, Graph } from './components/GraphDashboard';
import { request, gql } from 'graphql-request';

const GRAPHQL_ENDPOINT = '/ui/graphql';

const App: React.FC = () => {
  const [graph, setGraph] = useState<Graph>({ nodes: [], edges: [] });
  const [is3D, setIs3D] = useState(false);
  const [labelFilter, setLabelFilter] = useState('');

  const fetchGraph = async (label: string) => {
    const query = gql`
      query($label: String) {
        graph(label: $label) {
          nodes { id label }
          edges { source target weight }
        }
      }
    `;
    const data = await request<{ graph: Graph }>(GRAPHQL_ENDPOINT, query, { label: label || null });
    setGraph(data.graph);
  };

  useEffect(() => {
    fetchGraph(labelFilter);
  }, [labelFilter]);

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

  return (
    <GraphDashboard
      graph={graph}
      is3D={is3D}
      labelFilter={labelFilter}
      onToggle3D={() => setIs3D(!is3D)}
      onFilterChange={setLabelFilter}
      onExport={exportGraph}
    />
  );
};

const container = document.getElementById('root');
if (container) {
  const root = createRoot(container);
  root.render(<App />);
}
