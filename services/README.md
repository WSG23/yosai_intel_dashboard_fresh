# Services Package

## Testing

Install development dependencies and run the test suite:

```bash
pip install -r ../requirements-dev.txt
pytest
```

Generate a coverage report:

```bash
pytest --cov --cov-report=term-missing
```
