# Release Process

This project follows [Semantic Versioning](https://semver.org) for all public
releases. Versions are tagged in the form `vMAJOR.MINOR.PATCH`.

To create a new release:

1. Increment the version number according to the nature of your changes.
2. Tag the commit with the version (e.g. `git tag v1.2.0`).
3. Push the tag to GitHub. The CI workflow will automatically generate release
   notes for the tag.

See the [CHANGELOG](../CHANGELOG.md) for a list of changes.

## Dependency updates

This repository uses [Dependabot](https://docs.github.com/en/code-security/dependabot)
to automatically propose updates for packages listed in
`requirements.txt` and `requirements-dev.txt`. Dependabot runs weekly and
opens pull requests with updated pins.

If Dependabot is disabled or you need to update dependencies manually,
run `pip list --outdated` in a virtual environment and bump the versions
in the requirement files accordingly:

```bash
pip list --outdated
pip install --upgrade <package>
# update requirements*.txt with the new versions and commit the changes
```

After updating dependencies, run the Safety audit script to ensure no new high
severity vulnerabilities are introduced:

```bash
python scripts/audit_dependencies.py
```


