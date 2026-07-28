# Security Policy

## Reporting a vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do NOT open a public issue**
2. Email the maintainer directly or use GitHub's private vulnerability reporting
3. Include steps to reproduce and potential impact
4. Allow reasonable time for a fix before public disclosure

## Scope

This project is a markdown/template workflow system. It does not contain production application code. However, the `install.sh` script and CI/CD templates may have security implications:

- **install.sh**: downloads and executes templates from this repo
- **CI/CD templates**: may handle secrets (API keys, tokens)
- **Post-commit hooks**: local scripts that run on git operations

## Best practices

- Review CI/CD templates before enabling them in your repo
- Never commit secrets or API keys
- Use GitHub Secrets for sensitive values
- Keep the wizard updated to the latest version
