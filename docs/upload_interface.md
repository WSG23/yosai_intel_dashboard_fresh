# Upload Interface Guide

## Drag-and-Drop Usage

The dashboard exposes a simple drag-and-drop area on the **Upload** page. Either drag files onto the drop zone or click the region to open the file dialog. Selected files appear in a queue where you can remove entries prior to starting the upload. Once you press **Upload**, each file is sent to the server and a progress indicator shows completion status.

Supported file types are CSV and JSON. Large files are streamed to avoid exhausting browser memory. You may upload multiple files at once; they will be processed sequentially.

## Configuration Options

### Chunk Size

Large CSV files are processed in chunks. The default chunk size is 50,000 rows and is configured via `dynamic_config.analytics.chunk_size`. You can override it at runtime by setting the environment variable `ANALYTICS_CHUNK_SIZE`.

### Queue Limits

Background tasks such as analytics processing and file saves run in a thread pool. The number of concurrent workers is controlled by `dynamic_config.analytics.max_workers` (default `4`). Adjust the `MAX_WORKERS` environment variable to increase or decrease the processing queue.

## Mobile & Accessibility Guidelines

- The drop zone expands to full width on small screens and falls back to a standard file input when drag events are not supported.
- Provide an `aria-label` on the drop zone so screen readers announce its purpose.
- Ensure contrast ratios meet WCAG AA guidelines and that keyboard focus is visible.
- Touch targets, including the Upload button and remove icons, should be at least 44&times;44&nbsp;px.

