# Release Process

This project follows [Semantic Versioning](https://semver.org) for all public
releases. Versions are tagged in the form `vMAJOR.MINOR.PATCH`.

To create a new release:

1. Increment the version number according to the nature of your changes.
2. Tag the commit with the version (e.g. `git tag v1.2.0`).
3. Push the tag to GitHub. The CI workflow will automatically generate release
   notes for the tag.

See the [CHANGELOG](../CHANGELOG.md) for a list of changes.

