import React, { useEffect, useMemo, useRef, useState } from 'react';
import * as d3 from 'd3';
import * as THREE from 'three';

export interface SecurityNode {
  id: string;
  risk: number;
  group: string | number;
  time?: number;
}

export interface SecurityLink {
  source: string;
  target: string;
  time: number;
}

export interface NetworkSecurityGraphProps {
  nodes: SecurityNode[];
  links: SecurityLink[];
  width?: number;
  height?: number;
}

/**
 * NetworkSecurityGraph renders a force‑directed network graph using d3 for the
 * layout and Three.js for WebGL acceleration. Nodes are sized by risk score and
 * coloured by community group. Edges are bundled by routing them through group
 * centroids. A timeline scrubber allows temporal playback by filtering nodes and
 * edges based on their timestamp.
 */
const NetworkSecurityGraph: React.FC<NetworkSecurityGraphProps> = ({
  nodes,
  links,
  width = 800,
  height = 600,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [time, setTime] = useState(0);

  const maxTime = useMemo(() => {
    const linkMax = d3.max(links, (d) => d.time) ?? 0;
    const nodeMax = d3.max(nodes, (d) => d.time ?? 0) ?? 0;
    return Math.max(linkMax, nodeMax);
  }, [links, nodes]);

  const filtered = useMemo(() => {
    return {
      nodes: nodes.filter((n) => (n.time ?? 0) <= time),
      links: links.filter((l) => l.time <= time),
    };
  }, [nodes, links, time]);

  useEffect(() => {
    const { nodes: simNodes, links: simLinks } = filtered;
    if (!containerRef.current || simNodes.length === 0) return;

    // WebGL renderer setup
    const scene = new THREE.Scene();
    const camera = new THREE.OrthographicCamera(0, width, height, 0, -1000, 1000);
    camera.position.z = 10;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    containerRef.current.innerHTML = '';
    containerRef.current.appendChild(renderer.domElement);

    const riskScale = d3
      .scaleLinear()
      .domain(d3.extent(simNodes, (d) => d.risk) as [number, number])
      .range([2, 14]);

    const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

    // create node meshes
    const nodeMesh: Record<string, THREE.Mesh> = {};
    simNodes.forEach((n) => {
      const geom = new THREE.SphereGeometry(riskScale(n.risk), 8, 8);
      const mat = new THREE.MeshBasicMaterial({ color: colorScale(n.group.toString()) as THREE.ColorRepresentation });
      const mesh = new THREE.Mesh(geom, mat);
      scene.add(mesh);
      nodeMesh[n.id] = mesh;
    });

    const lineGroup = new THREE.Group();
    scene.add(lineGroup);

    // D3 force simulation
    const simulation = d3
      .forceSimulation(simNodes as d3.SimulationNodeDatum[])
      .force('link', d3.forceLink(simLinks).id((d: any) => d.id).distance(50))
      .force('charge', d3.forceManyBody().strength(-35))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const update = () => {
      const centers = d3.rollup(
        simNodes,
        (v) => ({
          x: d3.mean(v, (d: any) => d.x ?? 0) ?? 0,
          y: d3.mean(v, (d: any) => d.y ?? 0) ?? 0,
        }),
        (d) => (d as SecurityNode).group,
      );

      simNodes.forEach((n: any) => {
        const mesh = nodeMesh[n.id];
        if (mesh) {
          mesh.position.set(n.x ?? 0, n.y ?? 0, 0);
        }
      });

      lineGroup.clear();
      simLinks.forEach((l) => {
        const s = l.source as any;
        const t = l.target as any;
        const sCenter = centers.get((s as SecurityNode).group) || { x: s.x, y: s.y };
        const tCenter = centers.get((t as SecurityNode).group) || { x: t.x, y: t.y };

        // Control point halfway between group centers to produce bundled curve
        const control = new THREE.Vector3(
          (sCenter.x + tCenter.x) / 2,
          (sCenter.y + tCenter.y) / 2,
          0,
        );

        const curve = new THREE.QuadraticBezierCurve3(
          new THREE.Vector3(s.x, s.y, 0),
          control,
          new THREE.Vector3(t.x, t.y, 0),
        );
        const points = curve.getPoints(16);
        const geometry = new THREE.BufferGeometry().setFromPoints(points);
        const material = new THREE.LineBasicMaterial({ color: 0x999999, transparent: true, opacity: 0.3 });
        const line = new THREE.Line(geometry, material);
        lineGroup.add(line);
      });

      renderer.render(scene, camera);
    };

    simulation.on('tick', update);
    update();

    return () => {
      simulation.stop();
      renderer.dispose();
    };
  }, [filtered, width, height]);

  return (
    <div>
      <div ref={containerRef} />
      {maxTime > 0 && (
        <input
          type="range"
          min={0}
          max={maxTime}
          value={time}
          onChange={(e) => setTime(+e.target.value)}
        />
      )}
    </div>
  );
};

export default NetworkSecurityGraph;
