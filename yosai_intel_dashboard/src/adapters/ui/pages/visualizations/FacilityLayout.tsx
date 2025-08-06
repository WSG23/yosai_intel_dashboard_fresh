import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';

const FacilityLayout: React.FC = () => {
  const mountRef = useRef<HTMLDivElement>(null);
  const cubeRef = useRef<THREE.Mesh>();
  const rendererRef = useRef<THREE.WebGLRenderer>();
  const [webglSupported, setWebglSupported] = useState(true);

  useEffect(() => {
    const width = mountRef.current?.clientWidth ?? 400;
    const height = 300;

    try {
      const scene = new THREE.Scene();
      const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
      const renderer = new THREE.WebGLRenderer({ antialias: true });
      renderer.setSize(width, height);
      renderer.domElement.setAttribute('aria-hidden', 'true');
      mountRef.current?.appendChild(renderer.domElement);
      rendererRef.current = renderer;

      const geometry = new THREE.BoxGeometry();
      const material = new THREE.MeshBasicMaterial({ color: 0x00ff00, wireframe: true });
      const cube = new THREE.Mesh(geometry, material);
      scene.add(cube);
      cubeRef.current = cube;

      camera.position.z = 3;

      let frame: number;
      const animate = () => {
        cube.rotation.x += 0.01;
        cube.rotation.y += 0.01;
        renderer.render(scene, camera);
        frame = requestAnimationFrame(animate);
      };
      animate();

      const handleResize = () => {
        const w = mountRef.current?.clientWidth ?? width;
        renderer.setSize(w, height);
      };
      window.addEventListener('resize', handleResize);

      return () => {
        cancelAnimationFrame(frame);
        window.removeEventListener('resize', handleResize);
        if (mountRef.current) {
          mountRef.current.removeChild(renderer.domElement);
        }
      };
    } catch (e) {
      setWebglSupported(false);
    }
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const cube = cubeRef.current;
    if (!cube) {
      return;
    }
    switch (e.key) {
      case 'ArrowLeft':
        cube.rotation.y -= 0.1;
        break;
      case 'ArrowRight':
        cube.rotation.y += 0.1;
        break;
      case 'ArrowUp':
        cube.rotation.x -= 0.1;
        break;
      case 'ArrowDown':
        cube.rotation.x += 0.1;
        break;
      default:
        break;
    }
  };

  if (!webglSupported) {
    return (
      <div role="img" aria-label="3D facility layout not supported">
        WebGL not supported
      </div>
    );
  }

  return (
    <div
      ref={mountRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      role="img"
      aria-label="3D facility layout"
      style={{ width: '100%', height: '300px' }}
    />
  );
};

export default FacilityLayout;

