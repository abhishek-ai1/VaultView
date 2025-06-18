# 🤝 Contributing to VaultView

Thank you for your interest in contributing to VaultView! This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)
- [Feature Requests](#feature-requests)
- [Documentation](#documentation)

## 📜 Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for details.

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+**
- **Git**
- **pip** or **poetry**
- **Docker** (optional, for containerized development)

### Fork and Clone

1. **Fork the repository**
   - Go to [VaultView GitHub repository](https://github.com/yourusername/vaultview)
   - Click the "Fork" button in the top-right corner

2. **Clone your fork**
   ```bash
   git clone https://github.com/yourusername/vaultview.git
   cd vaultview
   ```

3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/yourusername/vaultview.git
   ```

## 🔧 Development Setup

### Environment Setup

1. **Create virtual environment**
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   
   # Using poetry
   poetry install
   poetry shell
   ```

2. **Install dependencies**
   ```bash
   # Install production dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install -r requirements-dev.txt
   # or
   pip install -e ".[dev]"
   ```

3. **Setup pre-commit hooks**
   ```bash
   pre-commit install
   ```

4. **Configure development environment**
   ```bash
   # Copy example configuration
   cp instance/config.example.py instance/config.py
   
   # Edit configuration for development
   nano instance/config.py
   ```

5. **Initialize database**
   ```bash
   python -c "from vaultview.app import create_app; from vaultview.db import init_db; app = create_app(); init_db(app)"
   ```

6. **Run development server**
   ```bash
   python run.py
   ```

### Docker Development Setup

```bash
# Build development image
docker build -f Dockerfile.dev -t vaultview-dev .

# Run development container
docker run -it --rm \
  -p 5000:5000 \
  -v $(pwd):/app \
  -e FLASK_ENV=development \
  vaultview-dev
```

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some modifications:

- **Line length**: 88 characters (Black default)
- **Import sorting**: Use `isort`
- **Code formatting**: Use `black`
- **Type hints**: Use type hints for all function parameters and return values

### Code Formatting

```bash
# Format code with Black
black vaultview/ tests/

# Sort imports with isort
isort vaultview/ tests/

# Check code style with flake8
flake8 vaultview/ tests/

# Type checking with mypy
mypy vaultview/
```

### File Structure

```
vaultview/
├── __init__.py
├── app.py                 # Flask application factory
├── models.py              # Database models
├── routes.py              # Main application routes
├── auth/                  # Authentication module
│   ├── __init__.py
│   ├── forms.py           # Authentication forms
│   └── routes.py          # Auth routes
├── ssl_checker.py         # SSL certificate checker
├── dns_checker.py         # DNS record analyzer
├── email_checker.py       # Email diagnostics
├── blacklist_checker.py   # Blacklist monitoring
├── notifications.py       # Alert system
├── scheduler.py           # Background tasks
├── utils.py               # Utility functions
└── reports/               # Report generation
    ├── __init__.py
    ├── generator.py       # Report generation logic
    └── templates/         # Report templates
```

### Naming Conventions

- **Files**: Use snake_case (e.g., `ssl_checker.py`)
- **Classes**: Use PascalCase (e.g., `SSLChecker`)
- **Functions**: Use snake_case (e.g., `check_ssl_certificate`)
- **Variables**: Use snake_case (e.g., `domain_name`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_RETRIES`)

### Documentation Standards

- **Docstrings**: Use Google-style docstrings
- **Comments**: Write clear, concise comments
- **README**: Keep documentation up-to-date

Example docstring:
```python
def check_ssl_certificate(domain: str) -> dict:
    """Check SSL certificate for a given domain.
    
    Args:
        domain: The domain name to check (e.g., 'example.com')
        
    Returns:
        Dictionary containing SSL certificate information:
        - subject: Certificate subject
        - issuer: Certificate issuer
        - valid_until: Expiration date
        - is_valid: Certificate validity status
        - days_until_expiry: Days remaining until expiry
        
    Raises:
        SSLError: If SSL connection fails
        ValueError: If domain is invalid
    """
    pass
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=vaultview --cov-report=html

# Run specific test file
pytest tests/test_ssl_checker.py

# Run tests with verbose output
pytest -v

# Run tests in parallel
pytest -n auto
```

### Writing Tests

- **Test files**: Name test files as `test_*.py`
- **Test functions**: Name test functions as `test_*`
- **Test classes**: Name test classes as `Test*`

Example test:
```python
import pytest
from vaultview.ssl_checker import check_ssl_certificate

def test_check_ssl_certificate_valid_domain():
    """Test SSL certificate check with valid domain."""
    result = check_ssl_certificate("google.com")
    
    assert result is not None
    assert "subject" in result
    assert "issuer" in result
    assert "valid_until" in result
    assert "is_valid" in result

def test_check_ssl_certificate_invalid_domain():
    """Test SSL certificate check with invalid domain."""
    with pytest.raises(ValueError):
        check_ssl_certificate("invalid-domain-12345.com")
```

### Test Coverage

We aim for at least 80% test coverage. To check coverage:

```bash
# Generate coverage report
pytest --cov=vaultview --cov-report=html

# View coverage report
open htmlcov/index.html
```

## 🔄 Pull Request Process

### Before Submitting

1. **Update your fork**
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write code following our standards
   - Add tests for new functionality
   - Update documentation if needed

4. **Run tests and checks**
   ```bash
   # Run all tests
   pytest
   
   # Run linting
   flake8 vaultview/ tests/
   
   # Run type checking
   mypy vaultview/
   
   # Run pre-commit hooks
   pre-commit run --all-files
   ```

5. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add new SSL certificate validation feature"
   ```

### Commit Message Format

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:
```
feat: add bulk DNS scanning functionality
fix(ssl): handle expired certificates gracefully
docs: update API documentation
test: add tests for email diagnostics
```

### Submitting PR

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your feature branch
   - Fill out the PR template

3. **PR Template**
   ```markdown
   ## Description
   Brief description of changes

   ## Type of Change
   - [ ] Bug fix
   - [ ] New feature
   - [ ] Documentation update
   - [ ] Test addition/update

   ## Testing
   - [ ] Tests pass locally
   - [ ] Added tests for new functionality
   - [ ] Updated existing tests if needed

   ## Checklist
   - [ ] Code follows style guidelines
   - [ ] Self-review completed
   - [ ] Documentation updated
   - [ ] No breaking changes
   ```

### PR Review Process

1. **Automated Checks**
   - CI/CD pipeline runs tests
   - Code coverage is checked
   - Linting and type checking

2. **Code Review**
   - Maintainers review your code
   - Address any feedback
   - Make requested changes

3. **Merge**
   - PR is merged after approval
   - Feature branch is deleted

## 🐛 Issue Reporting

### Before Reporting

1. **Check existing issues**
   - Search existing issues for similar problems
   - Check closed issues for solutions

2. **Try to reproduce**
   - Test with latest version
   - Check if issue occurs in different environments

### Issue Template

```markdown
## Bug Description
Clear description of the bug

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. Scroll down to '...'
4. See error

## Expected Behavior
What you expected to happen

## Actual Behavior
What actually happened

## Environment
- OS: [e.g., Ubuntu 20.04]
- Python Version: [e.g., 3.9.7]
- VaultView Version: [e.g., 1.0.0]
- Browser: [e.g., Chrome 91.0]

## Additional Information
- Screenshots if applicable
- Error logs
- Configuration files
```

## 💡 Feature Requests

### Before Requesting

1. **Check existing features**
   - Review current functionality
   - Check roadmap and milestones

2. **Research alternatives**
   - Look for existing solutions
   - Consider workarounds

### Feature Request Template

```markdown
## Feature Description
Clear description of the feature

## Use Case
Why this feature is needed

## Proposed Solution
How you think it should work

## Alternatives Considered
Other approaches you've considered

## Additional Information
- Mockups or wireframes
- Related issues
- Implementation suggestions
```

## 📚 Documentation

### Contributing to Documentation

1. **Update README.md**
   - Keep installation instructions current
   - Update feature descriptions
   - Add usage examples

2. **API Documentation**
   - Update API docs for new endpoints
   - Add code examples
   - Include error responses

3. **Code Comments**
   - Add docstrings to new functions
   - Update existing docstrings
   - Add inline comments for complex logic

### Documentation Standards

- **Clear and concise**: Write for the target audience
- **Examples**: Include practical examples
- **Links**: Link to related documentation
- **Formatting**: Use consistent markdown formatting

## 🏷️ Labels and Milestones

### Issue Labels

- `bug`: Something isn't working
- `enhancement`: New feature or request
- `documentation`: Improvements to documentation
- `good first issue`: Good for newcomers
- `help wanted`: Extra attention is needed
- `priority: high`: High priority issues
- `priority: low`: Low priority issues

### Milestones

- `v1.1.0`: Next minor release
- `v1.2.0`: Future minor release
- `Backlog`: Future consideration

## 🎯 Development Workflow

### Daily Workflow

1. **Start of day**
   ```bash
   git fetch upstream
   git checkout main
   git pull upstream main
   ```

2. **During development**
   ```bash
   # Make changes
   # Run tests frequently
   pytest tests/test_your_feature.py
   
   # Check code quality
   flake8 vaultview/your_file.py
   ```

3. **End of day**
   ```bash
   # Commit work in progress
   git add .
   git commit -m "WIP: feature description"
   
   # Push to your fork
   git push origin feature/your-feature-name
   ```

### Release Process

1. **Version bump**
   ```bash
   # Update version in setup.py
   # Update CHANGELOG.md
   # Create release branch
   git checkout -b release/v1.1.0
   ```

2. **Testing**
   ```bash
   # Run full test suite
   pytest
   
   # Test in different environments
   # Update documentation
   ```

3. **Release**
   ```bash
   # Merge to main
   git checkout main
   git merge release/v1.1.0
   
   # Create tag
   git tag v1.1.0
   git push origin v1.1.0
   ```

## 🆘 Getting Help

### Resources

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/yourusername/vaultview/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/vaultview/discussions)
- **Wiki**: [GitHub Wiki](https://github.com/yourusername/vaultview/wiki)

### Communication

- **Email**: contributors@vaultview.com
- **Slack**: [VaultView Slack](https://vaultview.slack.com)
- **Discord**: [VaultView Discord](https://discord.gg/vaultview)

## 🙏 Recognition

Contributors are recognized in several ways:

1. **Contributors list**: Added to [CONTRIBUTORS.md](CONTRIBUTORS.md)
2. **Release notes**: Mentioned in release announcements
3. **Hall of Fame**: Featured on the project website

## 📄 License

By contributing to VaultView, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to VaultView! 🚀 