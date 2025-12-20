# Contributing to Waygate MCP

Thank you for your interest in contributing to Waygate MCP! This document provides guidelines for contributing to our security-hardened MCP server framework.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Security](#security)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- Turso CLI (for database development)

### Quick Development Setup

```bash
# Clone the repository
git clone https://github.com/jeremylongshore/waygate-mcp.git
cd waygate-mcp

# Set up development environment
source activate_venv.sh

# Install dependencies
pip install -r source/requirements.txt
pip install -r source/requirements-dev.txt

# Initialize database
python -m source.waygate_mcp --init-db

# Run development server
python -m source.waygate_mcp --host 127.0.0.1 --port 8000 --reload --env development
```

## Development Setup

### Environment Configuration

Create a `.env` file in the project root:

```bash
# Database
DATABASE_URL=sqlite:///./waygate.db  # For local development
# DATABASE_URL=libsql://your-turso-db.turso.io?authToken=your-token  # For Turso

# Application
WAYGATE_SECRET_KEY=your-secret-key
WAYGATE_ENV=development

# Optional: MCP Server Integration
FIREBASE_PROJECT_ID=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
GITHUB_TOKEN=your-token
```

### Database Setup

#### Local SQLite (Default)
```bash
# Automatic initialization
python -m source.waygate_mcp --init-db
```

#### Turso Edge Database (Production)
```bash
# Install Turso CLI
curl -sSfL https://get.tur.so/install.sh | bash

# Create database
turso db create waygate-mcp

# Get auth token
turso db tokens create waygate-mcp

# Update .env with Turso URL
export DATABASE_URL="libsql://waygate-mcp-[username].turso.io?authToken=your-token"
```

## Making Changes

### Project Structure

```
waygate-mcp/
├── 01-docs/                    # Documentation
├── 02-src/                     # Migrated source code
│   ├── core/                   # Core business logic
│   ├── features/               # Feature modules
│   └── shared/                 # Shared utilities
├── source/                     # Active source code
│   ├── waygate_mcp.py         # Main server
│   ├── database.py            # Database layer
│   ├── mcp_integration.py     # MCP protocol
│   └── plugins/               # Plugin system
├── deployment/                 # Docker configs
└── 04-assets/configs/         # Configuration files
```

### Coding Standards

- Follow PEP 8 style guidelines
- Use type hints for all function parameters and returns
- Write docstrings for all public functions and classes
- Maximum line length: 88 characters (Black formatter)
- Use async/await for I/O operations

### Commit Message Format

Use conventional commits format:

```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

Examples:
```
feat(api): add new MCP tool execution endpoint
fix(database): resolve connection timeout issues
docs(readme): update quickstart instructions
```

## Testing

### Running Tests

```bash
# Install test dependencies
pip install -r source/requirements-dev.txt

# Run all tests
pytest source/tests/

# Run with coverage
pytest source/tests/ --cov=source --cov-report=html

# Run specific test file
pytest source/tests/test_database.py

# Run tests with verbose output
pytest source/tests/ -v
```

### Test Structure

- Unit tests: `source/tests/unit/`
- Integration tests: `source/tests/integration/`
- End-to-end tests: `source/tests/e2e/`

### Writing Tests

```python
import pytest
from source.waygate_mcp import WaygateMCP

@pytest.fixture
async def app():
    """Create test application instance."""
    app = WaygateMCP(testing=True)
    await app.initialize()
    yield app
    await app.cleanup()

@pytest.mark.asyncio
async def test_health_endpoint(app):
    """Test health check endpoint."""
    response = await app.test_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## Security

### Security Requirements

- All external inputs must be validated and sanitized
- Use parameterized queries for database operations
- Never log sensitive information (passwords, tokens, keys)
- Follow OWASP security guidelines
- Run security scans before committing

### Security Testing

```bash
# Run security scan with bandit
bandit -r source/ --severity-level medium

# Check for known vulnerabilities
safety check --policy-file .safety-policy.json

# Run comprehensive security scan (CI/CD)
./scripts/security-scan.sh
```

### Reporting Security Issues

Please report security vulnerabilities privately to security@waygatemcp.com. Do not create public issues for security vulnerabilities.

## Pull Request Process

### Before Submitting

1. **Run the full test suite**:
   ```bash
   pytest source/tests/
   ```

2. **Run code quality checks**:
   ```bash
   black source/
   isort source/
   flake8 source/
   mypy source/
   ```

3. **Run security scans**:
   ```bash
   bandit -r source/
   safety check
   ```

4. **Test Docker build**:
   ```bash
   docker build -t waygate-mcp:test deployment/
   ```

### Pull Request Checklist

- [ ] Branch is up to date with main
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Security scans pass
- [ ] Documentation updated if needed
- [ ] Commit messages follow conventional format
- [ ] No merge conflicts

### Review Process

1. Automated CI/CD checks must pass
2. Code review by at least one maintainer
3. Security review for security-related changes
4. Documentation review for user-facing changes

## Release Process

### Version Numbering

We use [Semantic Versioning](https://semver.org/):
- `MAJOR.MINOR.PATCH` (e.g., 2.1.0)
- Breaking changes increment MAJOR
- New features increment MINOR
- Bug fixes increment PATCH

### Release Checklist

1. Update version in `source/__init__.py`
2. Update CHANGELOG.md
3. Run full test suite
4. Create release branch: `release/v2.1.0`
5. Update documentation
6. Create signed git tag
7. Build and test Docker images
8. Deploy to staging environment
9. Create GitHub release with changelog

## Development Workflow

### Feature Development

```bash
# Create feature branch
git checkout main
git pull origin main
git checkout -b feature/new-mcp-tool

# Make changes
# ... code changes ...

# Run tests and checks
pytest source/tests/
black source/
mypy source/

# Commit changes
git add .
git commit -m "feat(tools): add new MCP tool for data processing"

# Push and create PR
git push origin feature/new-mcp-tool
```

### Hotfix Process

```bash
# Create hotfix branch from main
git checkout main
git checkout -b hotfix/security-vulnerability

# Make minimal fix
# ... security fix ...

# Test thoroughly
pytest source/tests/
bandit -r source/

# Commit and push
git commit -m "fix(security): resolve authentication bypass vulnerability"
git push origin hotfix/security-vulnerability
```

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python Security Guidelines](https://python.org/dev/security/)
- [MCP Protocol Specification](https://github.com/anthropics/mcp)

## Getting Help

- **Documentation**: Check the [docs/](01-docs/) directory
- **Issues**: Search existing GitHub issues
- **Discussions**: Use GitHub Discussions for questions
- **Discord**: Join our developer Discord server
- **Email**: developers@waygatemcp.com

## Recognition

Contributors who make significant contributions will be recognized in:
- CONTRIBUTORS.md file
- Release notes
- Annual contributor appreciation

Thank you for contributing to Waygate MCP! 🚀

---
*Last updated: September 29, 2025*