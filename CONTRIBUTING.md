# Contributing to ARP-Cache-CNC

Thank you for your interest in contributing to this research project! This document provides guidelines for contributing to the ARP-Cache-CNC repository.

## Code of Conduct

We are committed to providing a welcoming and respectful environment for all contributors. By participating in this project, you agree to abide by our Code of Conduct. Please see [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## Getting Started

### Setting Up Your Development Environment

1. **Clone the repository**
   ```bash
   git clone https://github.com/uri-ise/ARP-Cache-CNC.git
   cd ARP-Cache-CNC
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies (including dev extras)**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify your setup**
   ```bash
   pytest tests/
   ```

### Project Structure

- `analysis/` - Flask server, Dash dashboard, and UI components
- `infrastructure/` - Docker and deployment configurations
- `scenarios/` - Attack modules and G-code manipulation
- `tests/` - Test suite (pytest-based)
- `requirements.txt` - Runtime dependencies
- `pyproject.toml` - Package metadata and dev extras

## Development Workflow

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Keep commits atomic and descriptive
   - Follow PEP 8 style guidelines

3. **Run tests locally**
   ```bash
   pytest tests/ -v
   ```

4. **Commit and push**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   git push origin feature/your-feature-name
   ```

5. **Open a Pull Request**
   - Use the PR template
   - Reference any related issues
   - Ensure CI pipeline passes

## Testing

All contributions must include tests. We use **pytest** for the test suite.

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/smoke_test.py -v

# Run with coverage
pytest tests/ --cov=analysis --cov=scenarios
```

### Writing Tests

- Place test files in the `tests/` directory
- Name test functions as `test_*`
- Use descriptive assertions
- Include docstrings explaining test purpose

Example:
```python
def test_attack_configuration():
    """Test that attack parameters are correctly validated."""
    config = {"axis": "x", "value": 10}
    assert validate_attack_config(config) is True
```

## Code Style

We follow **PEP 8** with these additional guidelines:

- Maximum line length: 100 characters
- Use type hints where practical
- Include docstrings for modules, classes, and functions
- Keep functions focused and testable

### Optional: Linting and Formatting

While not enforced in CI, we recommend using these tools locally:
```bash
# Format with black
black analysis/ scenarios/

# Check with flake8
flake8 analysis/ scenarios/
```

## Documentation

- Update [README.md](README.md) for user-facing changes
- Update [SETUP.md](SETUP.md) for installation/deployment changes
- Add docstrings to new functions and classes
- Include inline comments for complex logic

## Reporting Issues

When reporting bugs or requesting features, please use the GitHub issue templates:

- **Bug Report**: Use the bug report template to provide reproduction steps
- **Feature Request**: Clearly describe the desired behavior and use case

## Safety and Ethics Guidelines

As this is a **research-only project** for authorized security testing:

1. **Research Use Only**: All contributions must support authorized security research on isolated networks
2. **No Production Deployment**: Do not use on production CNC systems
3. **Compliance**: Ensure compliance with applicable laws and institutional policies
4. **Safety**: Test carefully on isolated infrastructure
5. **Documentation**: Clearly document any security implications

## Pull Request Process

1. Ensure tests pass locally and in CI
2. Update documentation as needed
3. Follow the PR template
4. Request review from maintainers
5. Address feedback promptly
6. Maintain a clean commit history

## Questions or Need Help?

- Open an issue with the `question` label
- Check existing documentation: [SETUP.md](SETUP.md), [REFERENCE.md](REFERENCE.md)
- Contact the project maintainers

## Attribution

Contributors will be recognized in the project documentation. By contributing, you agree to license your contributions under the same MIT License as the project.

---

**Last Updated**: January 2026  
**Maintained by**: University of Rhode Island, Industrial Systems Engineering
