# New Dashboard Migration

The original dashboard interface served from `yosai_intel_dashboard` has been replaced with the redesigned React frontend in `ui/`.

## Migration Steps

1. Update deployment pipelines to build the React assets using `npm run build`.
2. Serve the compiled files from the `ui/dist` directory.
3. Remove references to the legacy Jinja templates and associated routes.
