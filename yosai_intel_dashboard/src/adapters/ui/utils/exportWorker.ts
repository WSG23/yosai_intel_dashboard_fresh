/* eslint-disable no-restricted-globals */
// Web Worker for assembling streamed chunks into a single Blob

const ctx: DedicatedWorkerGlobalScope = self as unknown as DedicatedWorkerGlobalScope;

let chunks: BlobPart[] = [];

ctx.onmessage = (
  e: MessageEvent<{ chunk?: Uint8Array; done?: boolean; mimeType?: string }>
) => {
  const { chunk, done, mimeType } = e.data;

  if (chunk) {
    // Store received chunk
    chunks.push(chunk);
  }

  if (done) {
    const blob = new Blob(chunks, { type: mimeType });
    ctx.postMessage({ blob });
    // Reset for possible future use
    chunks = [];
  }
};

export {};
