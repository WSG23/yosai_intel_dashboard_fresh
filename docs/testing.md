# Testing Setup

To run the test suite you must install both the core and testing dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

After installing the packages you can verify that `pytest` discovers the tests without executing them:

```bash
pytest --collect-only -q
```
