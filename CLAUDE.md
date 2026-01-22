# CLAUDE.md - Agentic Coder

This project uses [Gas Town](https://github.com/steveyegge/gastown) for multi-agent orchestration.

## Project Overview

**Agentic Coder** is a workspace for AI-assisted code generation using Gas Town's multi-agent coordination system.

## Gas Town Essentials

### Key Concepts
- **Mayor**: AI coordinator with workspace context
- **Polecats**: Ephemeral worker agents that spawn, execute, and terminate
- **Convoys**: Work tracking units bundling beads assigned to agents
- **Rigs**: Project containers wrapping git repositories
- **Beads**: Git-backed issue tracking (bead IDs: prefix + 5 alphanumeric chars, e.g., `gt-abc12`)

### Prerequisites
- Go 1.23+
- Git 2.25+
- beads (bd) 0.44.0+
- sqlite3
- tmux 3.0+
- Claude Code CLI (or other supported runtime)

## Common Commands

```bash
# Workspace management
gt install ~/gt --git          # Initialize workspace
gt rig add <name> <repo-url>   # Add a project
gt crew add <name> --rig <rig> # Create crew workspace

# Agent coordination
gt mayor attach                # Start the Mayor coordinator
gt agents                      # List active agents
gt sling                       # Spawn worker agents
gt prime                       # Inject context after compaction/new session

# Work tracking
gt convoy create               # Create new convoy
gt convoy list                 # List convoys
gt convoy show <id>            # Show convoy details

# Beads (issues)
bd formula list                # List available formulas
bd mol pour                    # Create new bead
bd mol list                    # List beads
```

## Development

### Build Commands
```bash
make build      # Build binary to .gt/
make install    # Install system-wide
make test       # Run tests: go test ./...
make clean      # Remove built binary
make generate   # Run go generate
```

### Code Standards
- Follow Go conventions: `gofmt`, `go vet`
- Keep functions small and focused
- Add comments for non-obvious logic
- Include tests for new functionality

### Commit Messages
- Use present tense: "Add feature" not "Added feature"
- Keep first line under 72 characters
- Reference beads: `Fix timeout bug (gt-xxx)`

## Session Management

Run `gt prime` after:
- Context compaction
- Clearing conversation
- Starting a new session

This injects full project context into the agent.

## Directory Structure (Gas Town Standard)

```
project/
├── cmd/gt/           # CLI entry point
├── internal/         # Core packages
├── .beads/           # Beads formulas and config
├── .claude/          # Claude settings and skills
├── docs/             # Documentation
├── templates/        # Template files
├── scripts/          # Utility scripts
├── Makefile          # Build automation
└── go.mod            # Go dependencies
```

## Workflow Patterns

### MEOW (Recommended)
Tell the Mayor what you want → Mayor analyzes and breaks down tasks → Convoy creation → Agent spawning → Work distribution → Progress monitoring → Completion

### Manual Mode
Use `gt config` to configure runtimes and manage agents directly for simpler workflows.

## Resources

- [Gas Town Repository](https://github.com/steveyegge/gastown)
- [Beads Documentation](https://github.com/steveyegge/beads)
