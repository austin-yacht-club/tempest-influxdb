# Development Guide

This document outlines best practices for developing and maintaining the Tempest Weather Station Waggle Plugin.

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
- Mark completed tasks with ✅
- Add new tasks as they're identified
- Include future enhancement ideas
- Update project status regularly

### 2. Git Workflow - Direct Commit to Main

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

#### Commit Message Format
```bash
git commit -m "Type: brief description

Detailed explanation of changes:
- What was modified
- Why it was necessary
- Technical details

Files changed:
- File names and line numbers

Benefits/Impact:
- What this improves
- Any breaking changes"
```

#### Example Good Commit
```bash
git commit -m "feat: add environment variable support for all config options

Added TEMPEST_* environment variables for every command-line argument:
- TEMPEST_UDP_PORT (default: 50222)
- TEMPEST_PUBLISH_INTERVAL (default: 60)
- TEMPEST_DEBUG (boolean)
- TEMPEST_NO_FIREWALL (boolean)

Files changed:
- main.py: parse_args() function enhanced with env var support
- README.md: comprehensive configuration tables added  
- CHANGES.md: detailed changelog entry
- TODO.md: updated task status

Testing:
- Syntax checks passing
- Manual testing with various env var combinations
- Verified CLI args override env vars as expected

Benefits:
- Better Docker/Kubernetes integration
- Easier CI/CD configuration"
```

### 3. Code Quality Standards

#### Python Best Practices
- Use context managers (`with Plugin() as plugin:`)
- Avoid global mutable state
- Use type hints where appropriate
- Follow PEP 8 style guidelines
- Use descriptive variable and function names

#### Error Handling
- Always handle exceptions gracefully
- Log errors with appropriate levels (DEBUG, INFO, WARNING, ERROR)
- Publish error status to Waggle when applicable
- Continue operation when possible (don't crash on single message errors)

#### Testing Approach
- Test error conditions (network failures, malformed data)
- Verify environment variable parsing
- Test throttling behavior
- Validate metadata structure

### 4. File Organization

#### Required Files
- `main.py` - Core application logic
- `README.md` - User documentation
- `CHANGES.md` - Detailed changelog
- `TODO.md` - Task tracking
- `DEVELOPMENT.md` - This file
- `requirements.txt` - Dependencies
- `Dockerfile` - Container configuration

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

**Check requirements**:
- No syntax errors (py_compile must succeed)
- Standard library imports work correctly
- Waggle imports are optional in development environments
- Basic code quality issues are flagged (warnings only)
- Required files (main.py, README.md, requirements.txt) are present

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

#### CHANGES.md Structure
```markdown
# Change Log

## YYYY-MM-DD - Feature Title

### Type: Description ✅

**What was changed**:
- Bullet points of changes

**Code Changes**:
- Specific file:line references

**Benefits**:
- Why this was needed

**Example Usage**:
```code
examples if relevant
```
```

#### TODO.md Structure
```markdown
# Project TODO

## Current Status: [STATUS]

## Completed Tasks
- ✅ Completed items

## In Progress
- 🔄 Current work

## Future Enhancements
- [ ] Future ideas
```

### 7. Waggle Integration Standards

#### Plugin Publishing
- Always use `scope="beehive"` for environmental data
- Include complete metadata with sensor name, units, descriptions
- Use standardized missing values (-9999.0 for numeric, "unknown" for strings)
- Add explicit UTC timestamps

#### Error Handling
- Publish plugin status for monitoring
- Handle UDP listener failures gracefully
- Log all errors with context
- Continue operation when possible

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
- Plugin initialization errors: Check Plugin() constructor requirements
- Port binding issues: Verify firewall and network configuration
- Missing dependencies: Update requirements.txt and test installation
- Environment variable issues: Test parsing and precedence

#### Debug Mode
Always test with `--debug` flag enabled:
```bash
python3 main.py --debug
```

This shows detailed logging for development and troubleshooting.

---

## Quick Reference

### Before Every Commit:
1. Run syntax checks ✅
2. Update README.md ✅
3. Update CHANGES.md ✅  
4. Update TODO.md ✅
5. Test changes ✅
6. Git commit with detailed message ✅

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
