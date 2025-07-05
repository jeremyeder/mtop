# Security Policy

## Supported Versions

The following versions of mtop are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of mtop seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### Please do NOT:
- Open a public GitHub issue for security vulnerabilities
- Post about the vulnerability on social media

### Please DO:
1. Email the project maintainer directly at the email address listed in the commit history
2. Include the following information:
   - Type of vulnerability (e.g., command injection, path traversal)
   - Full paths of source file(s) related to the vulnerability
   - Steps to reproduce the issue
   - Proof-of-concept or exploit code (if possible)
   - Impact of the vulnerability

### What to expect:
- We will acknowledge receipt of your vulnerability report within 48 hours
- We will provide a more detailed response within 7 days
- We will work on a fix and coordinate a release date with you
- We will publicly acknowledge your responsible disclosure (unless you prefer to remain anonymous)

## Security Features

mtop implements several security measures:

1. **Input Validation**: All user inputs are validated before processing
2. **No Shell Execution**: The tool operates in mock mode by default, preventing actual system commands
3. **Path Sanitization**: File paths are sanitized to prevent directory traversal attacks
4. **Dependency Scanning**: Regular dependency updates via Dependabot
5. **Static Analysis**: CodeQL scans for security vulnerabilities
6. **Type Safety**: Comprehensive type hints help prevent runtime errors

## Security Best Practices

When using mtop:

1. Always run in mock mode when testing or demonstrating
2. Review any generated YAML/JSON before applying to a cluster
3. Keep dependencies up to date
4. Run security scans regularly with `pip-audit`
5. Use virtual environments to isolate dependencies