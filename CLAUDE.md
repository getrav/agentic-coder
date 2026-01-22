# CLAUDE.md - AI Assistant Guidelines for Agentic Coder

This document provides essential context and guidelines for AI assistants working on the Agentic Coder project.

## Project Overview

**Agentic Coder** is a project focused on AI-assisted code generation and agentic programming workflows. The repository is in its early stages of development.

### Current Status
- **Stage**: Initial setup
- **Primary Files**: README.md, CLAUDE.md
- **Build System**: Not yet configured
- **Testing Framework**: Not yet configured

## Repository Structure

```
agentic-coder/
├── README.md          # Project description and documentation
├── CLAUDE.md          # AI assistant guidelines (this file)
└── .git/              # Git version control
```

### Planned Directory Structure (for future development)
When implementing features, follow this conventional structure:

```
agentic-coder/
├── src/               # Source code
│   ├── core/          # Core functionality and business logic
│   ├── utils/         # Utility functions and helpers
│   ├── types/         # Type definitions (if using TypeScript)
│   └── index.*        # Main entry point
├── tests/             # Test files (mirror src/ structure)
├── docs/              # Additional documentation
├── scripts/           # Build and utility scripts
├── config/            # Configuration files
├── .github/           # GitHub workflows and templates
├── package.json       # Node.js dependencies (if applicable)
├── pyproject.toml     # Python dependencies (if applicable)
└── README.md          # Project documentation
```

## Development Guidelines

### Code Style Conventions

1. **Keep it Simple**: Prefer straightforward solutions over clever abstractions
2. **Self-Documenting Code**: Use clear naming; add comments only for non-obvious logic
3. **Small Functions**: Each function should do one thing well
4. **Avoid Over-Engineering**: Don't add features, abstractions, or error handling for hypothetical scenarios

### Git Workflow

1. **Branch Naming**: Use descriptive branch names (e.g., `feature/add-parser`, `fix/memory-leak`)
2. **Commit Messages**: Write clear, concise commit messages in imperative mood
   - Good: "Add configuration parser module"
   - Avoid: "Added some stuff" or "WIP"
3. **Atomic Commits**: Each commit should represent a single logical change
4. **No Force Push to Main**: Never force push to the main branch

### File Naming Conventions

- Use lowercase with hyphens for files: `my-module.ts`, `api-client.py`
- Use PascalCase for class files if the language convention requires it
- Test files should mirror source: `src/utils/parser.ts` → `tests/utils/parser.test.ts`

### Security Practices

1. **Never commit secrets**: No API keys, passwords, or credentials in code
2. **Use environment variables**: Store sensitive config in `.env` files (gitignored)
3. **Validate inputs**: Sanitize user input at system boundaries
4. **Avoid common vulnerabilities**: Be mindful of injection attacks, XSS, CSRF

## Working with This Repository

### For AI Assistants

When working on this codebase:

1. **Read before modifying**: Always read existing code before making changes
2. **Understand context**: Check related files to understand patterns in use
3. **Minimal changes**: Make only the changes necessary to complete the task
4. **Preserve style**: Match the existing code style and conventions
5. **Test your changes**: If tests exist, run them before committing
6. **Document breaking changes**: Note any API changes that affect users

### Common Tasks

#### Adding a New Feature
1. Check for existing similar functionality
2. Create appropriate files following the directory structure
3. Write tests if a testing framework is configured
4. Update documentation if needed

#### Fixing a Bug
1. Identify the root cause by reading relevant code
2. Make the minimal fix required
3. Add a test case to prevent regression if possible
4. Don't refactor surrounding code unless explicitly requested

#### Refactoring
1. Ensure tests exist and pass before refactoring
2. Make incremental changes, testing after each step
3. Keep the same external API unless changes are requested

## Build and Test Commands

*Commands will be added once the build system is configured.*

### Placeholder Commands (update when configured)
```bash
# Install dependencies
npm install        # or: pip install -e .

# Run tests
npm test           # or: pytest

# Build project
npm run build      # or: python -m build

# Lint code
npm run lint       # or: ruff check .

# Format code
npm run format     # or: ruff format .
```

## Dependencies

*Dependencies will be documented once package management is configured.*

## Architecture Notes

*Architecture decisions and patterns will be documented as the project evolves.*

### Design Principles
- **Modularity**: Components should be loosely coupled
- **Testability**: Code should be easy to test in isolation
- **Clarity over Cleverness**: Readable code is maintainable code

## Troubleshooting

### Common Issues

*Issues and solutions will be documented as they arise.*

### Getting Help
- Check existing documentation and code comments
- Review git history for context on why code exists
- Look for related tests that demonstrate expected behavior

## Contributing

### Pull Request Guidelines
1. Keep PRs focused on a single concern
2. Provide clear descriptions of changes
3. Reference any related issues
4. Ensure all tests pass
5. Update documentation for user-facing changes

### Code Review Checklist
- [ ] Code follows project conventions
- [ ] Changes are minimal and focused
- [ ] No unnecessary refactoring
- [ ] Tests added/updated as appropriate
- [ ] Documentation updated if needed
- [ ] No secrets or sensitive data committed

---

*Last updated: 2026-01-22*
*This file should be updated as the project evolves and new conventions are established.*
