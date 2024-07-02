# Release a new version of the `pittgoogle-client` package

This page shows how to release a new version of `pittgoogle-client.
By following these instructions, you will:

- Tag a new release on GitHub.
- Publish a new version to PyPI.
- Publish new documentation.

## Instructions

1. Make sure the code in the main branch is ready for release.

2. Make sure the CHANGELOG.md file has been updated to include all changes being released.

3. On the repo's GitHub [releases](https://github.com/mwvgroup/pittgoogle-client/releases) page:
    - Click "Draft a new release".
    - Under "Choose a tag", enter the version tag as "v" followed by the release version
      ([semantic versioning](https://semver.org/) MAJOR.MINOR.PATCH).
    - Enter the same tag for the release title.
    - Under "Write", paste in the relevant section of CHANGELOG.md describing the release.
    - Click "Publish release".

Completing step 3 will (or should):

- Tag a new version on GitHub.
- Publish the documentation to GitHub pages.
- Publish the package to PyPI.org.

View the [GitHub Actions](https://github.com/mwvgroup/pittgoogle-client/actions) page to see the
status of the release process.

If all went well, you will now be able to install the new version using:

```bash
pip install --upgrade pittgoogle-client
```

This release process was implemented and described in [pull #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).
