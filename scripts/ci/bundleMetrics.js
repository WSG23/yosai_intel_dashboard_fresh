const { execSync } = require('child_process');
const { performance } = require('perf_hooks');
const fs = require('fs');
const path = require('path');

const start = performance.now();
execSync(
  'cd yosai_intel_dashboard/src/adapters/ui && ANALYZE=true vite build --config ../../../../vite.config.ts',
  { stdio: 'inherit' },
);
const buildTime = performance.now() - start;

function getDirSize(dir) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });
  return entries.reduce((total, entry) => {
    const res = path.join(dir, entry.name);
    return total + (entry.isDirectory() ? getDirSize(res) : fs.statSync(res).size);
  }, 0);
}

const distDir = path.join(__dirname, '..', '..', 'yosai_intel_dashboard', 'src', 'adapters', 'ui', 'dist');
const bundleSize = getDirSize(distDir);
const averageKbps = 200; // estimate network speed
const loadTimeMs = (bundleSize / 1024 / averageKbps) * 1000;

const metrics = {
  buildTimeMs: Math.round(buildTime),
  bundleSizeKb: Math.round(bundleSize / 1024),
  estimatedLoadTimeMs: Math.round(loadTimeMs),
};

const outFile = path.join(distDir, 'bundle-metrics.json');
fs.writeFileSync(outFile, JSON.stringify(metrics, null, 2));
console.log('Bundle metrics:', metrics);
