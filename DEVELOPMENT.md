# Development Guide

This document outlines best practices for developing and maintaining the Tempest Weather Station InfluxDB Publisher.

## Development Workflow

### 1. Documentation Requirements

#### Update README.md
- **Always** update README.md when adding new features or changing existing ones
- Include usage examples for new functionality
- Update configuration tables and examples
- Ensure all command-line arguments and environment variables are documented
- Add troubleshooting sections for new features

#### Update CHANGES.md (Changelog)
- **Every change** must be documented in CHANGES.md
- Use consistent date format: `YYYY-MM-DD`
- Include section headers for major changes vs bugfixes vs enhancements
- Document:
  - What was changed
  - Why it was changed  
  - Code locations affected (file paths and line numbers when relevant)
  - Breaking changes or migration notes
- Use clear, descriptive commit-style messages

#### Maintain TODO.md
- Keep a **running TODO.md** with current work in progress
- Mark completed tasks with checkmarks
- Add new tasks as they're identified
- Include future enhancement ideas
- Update project status regularly

### 2. Git Workflow

#### Commit Requirements
- **Always commit changes** after every significant modification
- Include comprehensive commit messages with:
  - What was changed
  - Why it was changed
  - Technical details when relevant
- Use conventional commit-style messages when possible:
  - `feat: add new feature`
  - `fix: resolve bug`
  - `docs: update documentation`
  - `refactor: improve code structure`

### 3. Code Quality Standards

#### Python Best Practices
- Use context managers where appropriate
- Avoid global mutable state
- Use type hints where appropriate
- Follow PEP 8 style guidelines
- Use descriptive variable and function names

#### Error Handling
- Always handle exceptions gracefully
- Log errors with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Write error status to InfluxDB when applicable
- Continue operation when possible (don't crash on single message errors)

#### Testing Approach
- Test error conditions (network failures, malformed data)
- Verify environment variable parsing
- Test throttling behavior
- Validate InfluxDB write operations

### 4. File Organization

#### Required Files
- `main.py` - Core application logic
- `README.md` - User documentation
- `CHANGES.md` - Detailed changelog
- `TODO.md` - Task tracking
- `DEVELOPMENT.md` - This file
- `requirements.txt` - Dependencies
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Docker Compose configuration

#### Update Priority
When making changes, update files in this order:
1. **Code changes** (main.py)
2. **README.md** (user-facing documentation)
3. **CHANGES.md** (changelog)
4. **TODO.md** (task tracking)
5. **Git commit** (version control)

### 5. Development Checklist

Before committing any changes, verify:

- [ ] Code changes are working and tested
- [ ] **Syntax checks pass** (see Syntax Checking section below)
- [ ] README.md is updated with new features/examples
- [ ] CHANGES.md includes detailed changelog entry
- [ ] TODO.md reflects current status
- [ ] Commit message is comprehensive
- [ ] Working directory is clean before commit

#### Syntax Checking

**Required checks before every commit**:

1. **Python Syntax Check**:
   ```bash
   python3 -m py_compile main.py
   ```

2. **Python Linting** (if flake8 is available):
   ```bash
   python3 -m flake8 main.py --max-line-length=100
   ```

3. **Basic Import Test**:
   ```bash
   python3 -c "import main" 2>/dev/null || echo "Import test failed"
   ```

**Automated syntax check script**:
Use the included `check-syntax.sh` script for comprehensive checking:
```bash
./check-syntax.sh
```

This script performs:
- Python syntax validation (`py_compile`)
- Import testing (handles development environments)
- Code quality checks (long lines, print statements)
- Optional flake8 linting (if available)
- File permission verification
- Required file presence checks

### 6. Documentation Standards

#### README.md Structure
```markdown
# Title
Brief description

## Overview
What it does

## Features
- Bullet list of capabilities

## Installation
Step-by-step instructions

## Usage
- Basic examples
- Configuration options
- Advanced usage

## Configuration
Tables of all options (CLI args + ENV vars)

## Troubleshooting
Common issues and solutions
```

### 7. InfluxDB Integration Standards

#### Data Writing
- Use appropriate tags for filtering (sensor, source, device_sn, hub_sn)
- Use fields for numeric measurements
- Include timestamps with all data points
- Filter out None values before writing

#### Error Handling
- Write status points for monitoring
- Handle connection failures gracefully
- Log all errors with context
- Reconnect when possible

### 8. Environment and Deployment

#### Docker Compatibility
- Ensure all configuration can be set via environment variables
- Document Docker usage examples
- Test container startup scenarios

#### Configuration Management
- Support both CLI args and environment variables
- Document precedence order (CLI > ENV > Defaults)
- Validate configuration values
- Show active configuration at startup

### 9. Maintenance Guidelines

#### Regular Tasks
- Update dependencies in requirements.txt
- Review and update TODO.md monthly
- Keep CHANGES.md current with each release
- Test with actual Tempest hardware when possible

#### Breaking Changes
- Document all breaking changes prominently in CHANGES.md
- Provide migration instructions
- Update README.md examples
- Consider version compatibility

### 10. Troubleshooting Development Issues

#### Common Problems
- InfluxDB connection errors: Check URL, token, and network
- Port binding issues: Verify firewall and network configuration
- Missing dependencies: Update requirements.txt and test installation
- Environment variable issues: Test parsing and precedence

#### Debug Mode
Always test with `--debug` flag enabled:
```bash
python3 main.py --debug --influxdb-token your-token
```

This shows detailed logging for development and troubleshooting.

---

## Quick Reference

### Before Every Commit:
1. Run syntax checks
2. Update README.md
3. Update CHANGES.md  
4. Update TODO.md
5. Test changes
6. Git commit with detailed message

### File Update Order:
1. Code (main.py)
2. Documentation (README.md, CHANGES.md, TODO.md)
3. Git commit

### Documentation Standards:
- README.md: User-facing documentation
- CHANGES.md: Detailed technical changelog
- TODO.md: Task and status tracking
- DEVELOPMENT.md: This development guide

Following these practices ensures the project remains maintainable, well-documented, and professional.
