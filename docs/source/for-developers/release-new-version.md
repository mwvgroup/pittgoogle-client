# Release a new version of pittgoogle-client

This page shows how to release a new version of pittgoogle-client.
Completing these instructions and clicking "Publish" will trigger the following to
happen automatically:

- A new release will be tagged on GitHub here: <https://github.com/mwvgroup/pittgoogle-client/releases>.
- A new version will publish to PyPI here: <https://pypi.org/project/pittgoogle-client/>.
- New documentation will publish to GitHub pages here: <https://mwvgroup.github.io/pittgoogle-client/>.

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

Completing step 3 will (or should) cause the new version to be published to the three places listed above.
View the [GitHub Actions](https://github.com/mwvgroup/pittgoogle-client/actions) page to see the
status of the release process.

If all went well, you will now be able to install the new version using:

```bash
pip install --upgrade pittgoogle-client
```

----

This release process was implemented and described in [pull #7](https://github.com/mwvgroup/pittgoogle-client/pull/7).
