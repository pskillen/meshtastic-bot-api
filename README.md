# MeshtasticBot API

A Django-based API for managing Meshtastic nodes and their data.

## Installation

### Development Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv-api
source venv-api/bin/activate  # On Windows: venv-api\Scripts\activate
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Set up pre-commit hooks:
```bash
pre-commit install
```

The pre-commit hooks will run automatically on each commit, ensuring:
- Code is formatted with Black
- Imports are sorted with isort
- Code style is checked with flake8
- Various other code quality checks

You can also run the checks manually:
```bash
pre-commit run --all-files
```

### Installation on RPi (ARMv7)

Since there's no wheel for psycopg2, we need to install it from source. This will take a while.

```bash
sudo apt-get update
sudo apt-get install -y libpq-dev python3-dev

pip install wheel
pip install -r requirements.txt
```

## Development

### Running Tests

```bash
pytest
```

For coverage report:
```bash
pytest --cov=. --cov-report=xml
```

### Code Style

This project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting

All these tools are configured as pre-commit hooks and will run automatically on each commit.
