# Contributing to fast-sim

Thanks for your interest in contributing! This guide covers environment setup, coding standards, and the release workflow.

## Environment setup

1. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e '.[dev,bench]'
   ```
2. Install pre-commit tooling if desired: `pip install pre-commit && pre-commit install`.

## Development workflow

- Use feature branches and open pull requests early.
- Run formatting and quality checks locally:
  ```bash
  make lint
  make type
  make test
  ```
- Keep functions small and add docstrings for public APIs.
- Write deterministic tests that run in seconds.
- Commit messages should follow the imperative mood (e.g. "Add queue example").

## Documentation

- Update `README.md` and examples when adding new features.
- Include narrative explanations and code samples where appropriate.

## Publishing a release

1. Update the version in `src/fast_sim/version.py` using semantic versioning.
2. Regenerate artifacts:
   ```bash
   rm -rf dist/
   make dist
   ```
3. Upload to PyPI using `twine upload dist/*`.
4. Tag the release in Git and publish release notes summarising changes.

## Community expectations

- Respect the [Code of Conduct](CODE_OF_CONDUCT.md).
- Be responsive to review feedback and iterate quickly.

Happy hacking!
