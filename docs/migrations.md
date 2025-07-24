# Migration Guides

This directory collects scripts and tips for upgrading the dashboard across major versions.

## Converting legacy pickle mappings

Older releases stored learned device mappings in a `learned_mappings.pkl` file. The dashboard no longer loads pickle data because unpickling arbitrary files is insecure.

Run `tools/migrate_pickle_mappings.py` to convert the file to JSON:

```bash
python tools/migrate_pickle_mappings.py /path/to/learned_mappings.pkl
```

Pass `--remove-pickle` to delete the original file after a successful conversion:

```bash
python tools/migrate_pickle_mappings.py --remove-pickle /path/to/learned_mappings.pkl
```

The JSON output is written next to the pickle using the `.json` extension. Once migrated, configure your deployment to rely only on the JSON file.

### Removing legacy directories
After running `scripts/migrate_to_clean_arch.py` and `scripts/update_imports.py` the
old top-level packages are no longer required. You can remove them with:

```bash
rm -rf core services models api config monitoring security plugins
```

`yosai_intel_dashboard/__init__.py` will continue to map the previous package names
for any code that still imports them. Update your Dockerfiles and CI workflows to
reference paths under `yosai_intel_dashboard/src/`.
