# Local CI/CD with `act`

This repository uses [act](https://github.com/nektos/act) to run GitHub Actions workflows locally.

## Installation

Install `act` by following the [official instructions](https://github.com/nektos/act#installation). On macOS with Apple Silicon, specify the container architecture when running:

```bash
act --container-architecture linux/amd64
```

Store GitHub secrets in a `.secrets` file in the repository root so `act` can load them during execution.

## Sample Commands

```bash
act pull_request -j validate-structure
act pull_request -j build
act pull_request -W .github/workflows/ci-cd.yml -j tests
act pull_request -W .github/workflows/microservices-ci-cd.yml -j deploy
act push -W .github/workflows/docker-release.yml -j build-and-push
```

## Security Checks

The CI pipeline runs additional security scans after the test jobs complete:

- **Dependency Review** using `actions/dependency-review-action` fails if new
  dependencies introduce critical vulnerabilities.
- **Trivy** scans the repository for known vulnerabilities and exits with an
  error when critical issues are found.

Run these checks locally with `act`:

```bash
act pull_request -j security-scans
```
