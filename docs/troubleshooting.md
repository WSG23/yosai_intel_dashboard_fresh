# Troubleshooting

This guide covers solutions to common issues when setting up or running the dashboard.

## Flask CLI NameError

If running `python app.py` fails with a traceback ending in:

```
NameError: name '_env_file_callback' is not defined
```

Flask may have been installed incorrectly or corrupted. Reinstall Flask in your virtual environment:

```bash
pip install --force-reinstall "Flask>=2.2.5"
```

This restores the missing function in `flask/cli.py` and allows the dashboard to start normally.
