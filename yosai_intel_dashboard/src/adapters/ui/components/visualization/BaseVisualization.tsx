import React, { useEffect, useRef, useState } from 'react';
import useVisualizationPerformance from '../../hooks/useVisualizationPerformance';

export interface BaseVisualizationProps {
  width?: number;
  height?: number;
  rowHeight?: number;
  dataLength?: number;
  onSetup?: (gl: WebGLRenderingContext) => void;
  onRender: (gl: WebGLRenderingContext, frame: number) => void;
  children?: React.ReactNode;
}

/**
 * BaseVisualization centralizes common behavior for WebGL visualizations:
 * - WebGL context initialization
 * - Progressive rendering tied to the browser frame rate
 * - Virtual scrolling for large collections of children
 */
const BaseVisualization: React.FC<BaseVisualizationProps> = ({
  width = 300,
  height = 150,
  rowHeight = 20,
  dataLength = 0,
  onSetup,
  onRender,
  children
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const { throttleToFrameRate } = useVisualizationPerformance();

  // Initialize WebGL and start progressive rendering
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) {
      return;
    }

    const gl = canvas.getContext('webgl');
    if (!gl) {
      return;
    }

    onSetup?.(gl);

    let frame = 0;
    const stop = throttleToFrameRate(() => {
      onRender(gl, frame++);
    }, 60);

    return () => {
      stop();
    };
  }, [onSetup, onRender, throttleToFrameRate]);

  // Basic virtual scrolling implementation
  const [scrollTop, setScrollTop] = useState(0);
  const handleScroll = () => {
    if (!containerRef.current) {
      return;
    }
    setScrollTop(containerRef.current.scrollTop);
  };

  const visibleCount = Math.ceil(height / rowHeight);
  const startIndex = Math.floor(scrollTop / rowHeight);
  const endIndex = Math.min(dataLength, startIndex + visibleCount);
  const offsetY = startIndex * rowHeight;

  return (
    <div
      ref={containerRef}
      onScroll={handleScroll}
      style={{ overflowY: 'auto', height }}
    >
      <canvas ref={canvasRef} width={width} height={height} />
      {children && dataLength > 0 && (
        <div style={{ height: dataLength * rowHeight, position: 'relative' }}>
          <div style={{ transform: `translateY(${offsetY}px)` }}>
            {React.Children.toArray(children).slice(startIndex, endIndex)}
          </div>
        </div>
      )}
    </div>
  );
};

export default BaseVisualization;

