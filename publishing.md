# Publishing a New Version

This repository uses [UV](https://docs.astral.sh/uv/guides/publish/) for building and publishing the package to PyPI. The GitHub Actions workflow defined in [`.github/workflows/main.yaml`](.github/workflows/main.yaml) automates the following steps:

1. **Linting and Type Checking:**
   The workflow runs linting, formatting, type-checking, and unit tests on every commit and pull request.

2. **Building and Publishing:**
   When a new Git tag is pushed, the workflow:
   - Checks out the source code.
   - Sets up Python and installs UV.
   - Syncs dependencies.
   - Builds the package using `uv build`.
   - Publishes the package to PyPI using `uv publish`.

## Steps to Publish a New Version

1. **Update the Version in `pyproject.toml`:**
   In the `[project]` section of your `pyproject.toml`, update the `version` field:

   ```toml
   [project]
   name = "your_package_name"
   version = "X.Y.Z"  # Update this to your new version
   description = "Your package description."
   # ... other metadata ...
   ```

2. **Commit Your Changes:**
   Commit the updated `pyproject.toml` (or any other relevant files) to your repository.

   ```bash
   git add pyproject.toml
   git commit -m "Bump version to X.Y.Z"
   ```

3. **Tag the Commit:**
   Create a git tag following your versioning convention (e.g., `vX.Y.Z`):

   ```bash
   git tag vX.Y.Z
   ```

   Alternatively, you can also create a tag using the GitHub web interface to draft a new release, which will automatically tag the commit.

4. **Push the Changes and the Tag:**
   Push your commit and tags to the main branch:

   ```bash
   git push origin main --tags
   ```

5. **Automatic Build and Publish:**
   Once the tag is pushed, GitHub Actions will trigger the `build-and-publish` job:

   - **Build:** The job runs `uv build` to create the package distributions.
   - **Publish:** The job then runs `uv publish --token $UV_PUBLISH_TOKEN` to publish the package to PyPI. Make sure that the `PYPI_API_TOKEN` secret is set in your repository configuration.

6. **Verify the Release:**
   - Check the workflow run in GitHub Actions for any errors.
   - Confirm that the new version is available on [PyPI](https://pypi.org/).

## Additional Notes

- **Version Management:** The version published to PyPI is read from the `pyproject.toml` file. It is your responsibility to update it for each release.
- **Secrets:** Ensure that the secret `PYPI_API_TOKEN` is defined in your repository's settings. This token should have the necessary permissions to publish to PyPI.
- **Workflow Dependencies:** The publishing step depends on successful completion of linting, type-checking, and unit tests.

Happy releasing!
