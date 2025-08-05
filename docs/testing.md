# Testing Setup

To run the test suite you must install the development dependencies:

```bash
pip install -r requirements-dev.txt
```

After installing the packages you can verify that `pytest` discovers the tests without executing them:

```bash
pytest --collect-only -q
```
