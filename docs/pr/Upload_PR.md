# Upload Pull Request

Use the following commands before uploading your pull request to verify formatting, linting, and tests for both the backend and frontend:

```sh
python -m pip install -r requirements-dev.txt
black .
ruff check .
pytest -q
npm ci
npm test
```
