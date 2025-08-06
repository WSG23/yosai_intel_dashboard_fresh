import React, { useRef, useEffect } from 'react';
import * as d3 from 'd3';

interface NodeDatum {
  id: string;
  x?: number;
  y?: number;
  vx?: number;
  vy?: number;
  fx?: number | null;
  fy?: number | null;
}

interface LinkDatum {
  source: string;
  target: string;
}

const NetworkGraph: React.FC = () => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const render = () => {
      const svg = d3.select(svgRef.current);
      const width = containerRef.current?.clientWidth ?? 400;
      const height = 300;
      svg.selectAll('*').remove();
      svg.attr('viewBox', `0 0 ${width} ${height}`);

      const nodes: NodeDatum[] = [
        { id: 'A' },
        { id: 'B' },
        { id: 'C' },
      ];
      const links: LinkDatum[] = [
        { source: 'A', target: 'B' },
        { source: 'B', target: 'C' },
      ];

      const simulation = d3
        .forceSimulation(nodes)
        .force(
          'link',
          d3
            .forceLink<LinkDatum, NodeDatum>(links)
            .id((d) => d.id)
            .distance(80),
        )
        .force('charge', d3.forceManyBody().strength(-200))
        .force('center', d3.forceCenter(width / 2, height / 2));

      const link = svg
        .append('g')
        .attr('stroke', '#999')
        .selectAll('line')
        .data(links)
        .enter()
        .append('line');

      const node = svg
        .append('g')
        .selectAll('circle')
        .data(nodes)
        .enter()
        .append('circle')
        .attr('r', 8)
        .attr('fill', '#69b3a2')
        .attr('tabindex', 0)
        .attr('role', 'button')
        .attr('aria-label', (d) => `Node ${d.id}`)
        .call(
          d3
            .drag<SVGCircleElement, NodeDatum>()
            .on('start', (event, d) => {
              if (!event.active) simulation.alphaTarget(0.3).restart();
              d.fx = d.x;
              d.fy = d.y;
            })
            .on('drag', (event, d) => {
              d.fx = event.x;
              d.fy = event.y;
            })
            .on('end', (event, d) => {
              if (!event.active) simulation.alphaTarget(0);
              d.fx = null;
              d.fy = null;
            }),
        )
        .on('click', function () {
          const current = d3.select(this);
          const isRed = current.attr('fill') === 'red';
          current.attr('fill', isRed ? '#69b3a2' : 'red');
        })
        .on('keydown', function (event) {
          if (event.key === 'Enter' || event.key === ' ') {
            const current = d3.select(this as SVGCircleElement);
            const isRed = current.attr('fill') === 'red';
            current.attr('fill', isRed ? '#69b3a2' : 'red');
          }
        });

      simulation.on('tick', () => {
        link
          .attr('x1', (d) => (d.source as NodeDatum).x || 0)
          .attr('y1', (d) => (d.source as NodeDatum).y || 0)
          .attr('x2', (d) => (d.target as NodeDatum).x || 0)
          .attr('y2', (d) => (d.target as NodeDatum).y || 0);

        node
          .attr('cx', (d) => d.x || 0)
          .attr('cy', (d) => d.y || 0);
      });

      return simulation;
    };

    const simulation = render();
    window.addEventListener('resize', render);
    return () => {
      simulation.stop();
      window.removeEventListener('resize', render);
    };
  }, []);

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <svg
        ref={svgRef}
        width="100%"
        height={300}
        role="img"
        aria-label="Relationship graph showing security entity connections"
      >
        <title>Relationship graph showing security entity connections</title>
      </svg>
    </div>
  );
};

export default NetworkGraph;

