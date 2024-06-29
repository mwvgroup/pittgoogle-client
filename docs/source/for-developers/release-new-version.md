# Release a New Version of pittgoogle-client

When you are ready to release a new version of `pittgoogle-client`, publish to PyPI using the following steps:

1. Make sure the code in the main branch is ready for release.

2. Make sure the CHANGELOG.md file has been updated to reflect the changes being released.

3. On the repo's GitHub [releases](https://github.com/mwvgroup/pittgoogle-client/releases) page:
    - Click "Draft a new release".
    - Under "Choose a tag", enter the version tag as "v" followed by the release version
      ([semantic versioning](https://semver.org/) MAJOR.MINOR.PATCH).
    - Enter the same tag for the release title.
    - Click "Publish release".

Completing step 3 will:

- Execute the test suite.
- Publish the documentation to GitHub pages.
- Publish the package to PyPI.org.

You will now be able to install the new version using:

```bash
pip install --upgrade pittgoogle-client
```

This release process was implemented and described in [pull #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).
