# PR Creation and Linking

This module provides functionality for creating GitHub pull requests and linking them to bead IDs in the beads issue tracking system.

## Features

- **GitHub PR Creation**: Create pull requests using the GitHub API
- **Bead Integration**: Automatically link PRs to bead IDs
- **CLI Interface**: Command-line tools for PR management
- **Error Handling**: Robust error handling and reporting
- **Environment Configuration**: Easy setup via environment variables

## Installation

The PR creation functionality is part of the `agentic-coder` package. Ensure you have the required dependencies:

```bash
pip install requests
```

## Configuration

Set the following environment variables:

```bash
export GITHUB_TOKEN='your_github_personal_access_token'
export GITHUB_OWNER='repository_owner'
export GITHUB_REPO='repository_name'
export GITHUB_API_URL='https://api.github.com'  # Optional
```

### GitHub Token

Create a personal access token with the following scopes:
- `repo` - Full control of private repositories
- `pull_requests` - Access to pull requests

## Usage

### CLI Commands

#### Create a PR for a Bead

```bash
python -m src.pr_cli create-pr \\
    --head 'feature-branch' \\
    --title 'Implement feature XYZ' \\
    --bead 'AC-123'
```

#### Create a PR Without Bead

```bash
python -m src.pr_cli create-pr \\
    --head 'feature-branch' \\
    --title 'Implement feature XYZ' \\
    --body 'Detailed description of changes'
```

#### Link Existing PR to Bead

```bash
python -m src.pr_cli link-pr 123 AC-456
```

#### List PRs for a Bead

```bash
python -m src.pr_cli list-bead-prs AC-123
```

### Python API

#### Basic Usage

```python
from src.pr_creation_service import create_pr_service_from_env

# Create service from environment
service = create_pr_service_from_env()
if not service:
    print("Missing environment configuration")
    exit(1)

# Create PR for a bead
result = service.create_pr_for_bead(
    bead_id='AC-123',
    head_branch='feature-branch',
    title='Implement feature XYZ',
    body='Detailed description'
)

if result.success:
    print(f"PR created: {result.pr_info.pr_url}")
else:
    print(f"Error: {result.error_message}")
```

#### Advanced Usage

```python
from src.github_pr_client import GitHubPRClient, GitHubConfig
from src.pr_creation_service import PRCreationService
from beadsclient.client import BeadsClient

# Manual configuration
config = GitHubConfig(
    token='your_token',
    owner='repo_owner',
    repo='repo_name'
)

github_client = GitHubPRClient(config)
beads_client = BeadsClient()

service = PRCreationService(github_client, beads_client)

# Create PR
result = service.create_pr_for_bead(
    bead_id='AC-123',
    head_branch='feature-branch',
    title='Feature implementation',
    body='Changes described in bead AC-123'
)

# Link existing PR
link_result = service.link_pr_to_bead(pr_number=42, bead_id='AC-123')

# Get PRs for bead
prs = service.get_prs_for_bead('AC-123')
for pr in prs:
    print(f"#{pr.pr_number}: {pr.title}")
```

## Components

### GitHubPRClient

Low-level GitHub API client for PR operations:

```python
from src.github_pr_client import GitHubPRClient, GitHubConfig

config = GitHubConfig(
    token='your_token',
    owner='owner',
    repo='repo'
)

client = GitHubPRClient(config)

# Create PR
pr_info = client.create_pr(
    title='PR title',
    head='feature-branch',
    base='main',
    body='PR description',
    bead_id='AC-123'
)

# Get PR info
pr_info = client.get_pr(123)

# List PRs
prs = client.list_prs(state='open')

# Add comment
client.add_pr_comment(123, 'Review feedback')

# Update PR with bead link
client.update_pr_with_bead_link(123, 'AC-123')
```

### PRCreationService

High-level service that integrates GitHub PR creation with bead tracking:

```python
from src.pr_creation_service import PRCreationService

service = PRCreationService(github_client, beads_client)

# Create PR for bead
result = service.create_pr_for_bead(
    bead_id='AC-123',
    head_branch='feature-branch'
)

# Create PR without bead
result = service.create_pr_without_bead(
    title='Feature implementation',
    head_branch='feature-branch'
)

# Link existing PR to bead
result = service.link_pr_to_bead(pr_number=123, bead_id='AC-123')

# Get PRs for bead
prs = service.get_prs_for_bead('AC-123')
```

### Data Structures

#### PRInfo

```python
@dataclass
class PRInfo:
    pr_number: int
    pr_url: str
    title: str
    body: str
    head_branch: str
    base_branch: str
    bead_id: Optional[str] = None
```

#### PRCreationResult

```python
@dataclass
class PRCreationResult:
    success: bool
    pr_info: Optional[PRInfo] = None
    error_message: Optional[str] = None
    bead_updated: bool = False
```

## Examples

See `example_pr_creation.py` for comprehensive examples of using the PR creation functionality.

Run the example:

```bash
python example_pr_creation.py
```

This will demonstrate:
- Environment setup
- Creating PRs for beads
- Linking existing PRs to beads
- Listing PRs for beads

## Error Handling

All operations return structured results with error information:

```python
result = service.create_pr_for_bead(bead_id='AC-123', head_branch='feature')

if not result.success:
    print(f"Failed to create PR: {result.error_message}")
    # Handle error appropriately
```

Common error scenarios:
- Missing environment variables
- Invalid GitHub token
- Insufficient permissions
- Branch not found
- Bead not found
- Network issues

## Testing

Run the example script to test the functionality:

```bash
python example_pr_creation.py
```

This will verify your environment configuration and demonstrate the available features.

## Integration with Workflow

The PR creation functionality integrates seamlessly with the existing workflow:

1. **Create a bead**: `bd create --title "Feature implementation"`
2. **Implement the feature**: Work on your branch
3. **Create PR**: Use the PR creation service to create and link the PR
4. **Track progress**: The PR is now linked to the bead for tracking

## Security

- GitHub tokens are sensitive - store them securely
- Use environment variables or secure credential management
- Grant minimum required scopes to tokens
- Rotate tokens regularly

## Troubleshooting

### Common Issues

**401 Unauthorized**
- Check your GitHub token is valid
- Verify token has required scopes

**404 Not Found**
- Check repository owner and name
- Verify repository exists and you have access

**422 Validation Failed**
- Check branch names exist
- Verify PR title and body meet GitHub requirements

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

When contributing to this module:

1. Ensure all imports are relative
2. Add comprehensive error handling
3. Include tests for new functionality
4. Update documentation

## License

This module is part of the agentic-coder project and follows the same license terms.