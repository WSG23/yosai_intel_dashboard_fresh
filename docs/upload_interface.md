# Upload Interface Guide

## Drag-and-Drop Usage

The dashboard exposes a simple drag-and-drop area on the **Upload** page. Either drag files onto the drop zone or click the region to open the file dialog. Selected files appear in a queue where you can remove entries prior to starting the upload. Once you press **Upload**, each file is sent to the server and a progress indicator shows completion status.

Supported file types are CSV and JSON. Large files are streamed to avoid exhausting browser memory. You may upload multiple files at once; they will be processed sequentially.

## Configuration Options

### Chunk Size

Large CSV files are processed in chunks. The default chunk size is configured
under `uploads.chunk_size` and can be overridden by setting the environment
variable `UPLOAD_CHUNK_SIZE`.

### Queue Limits

Background tasks such as analytics processing and file saves run in a thread
pool. The worker count comes from `uploads.max_parallel_uploads` (default `4`).
Use the `MAX_PARALLEL_UPLOADS` environment variable to adjust this value.

## Mobile & Accessibility Guidelines

- The drop zone expands to full width on small screens and falls back to a standard file input when drag events are not supported.
- Provide an `aria-label` on the drop zone so screen readers announce its purpose.
- Ensure contrast ratios meet WCAG AA guidelines and that keyboard focus is visible.
- Touch targets, including the Upload button and remove icons, should be at least 44&times;44&nbsp;px.

