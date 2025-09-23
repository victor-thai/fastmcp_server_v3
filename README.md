# FastMCP Server with Asana Integration

A comprehensive Model Context Protocol (MCP) server built with FastMCP, featuring Asana task management capabilities and ready for deployment to FastMCP Cloud.

## What's Included

This repository contains a FastMCP server (`server.py`) with two categories of tools:

### 🔧 Utility Tools
- **greet**: Return a friendly greeting message
- **echo**: Echo text back to the caller
- **get_current_time**: Get the current date and time
- **calculate**: Safely evaluate mathematical expressions
- **format_json**: Format JSON strings with proper indentation

### 📋 Asana Task Management Tools
- **create_asana_task**: Create new tasks in Asana with optional project assignment, due dates, and priorities
- **update_asana_task**: Update existing tasks (name, notes, completion status, due date, priority)
- **get_asana_task**: Retrieve detailed information about a specific task
- **list_asana_projects**: List all projects accessible to the authenticated user
- **search_asana_tasks**: Search for tasks by query with optional project filtering

## Local Development

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Asana account and Personal Access Token (for Asana features)
- Prefect installation and setup (for Secret block management)

### Setup

1. Clone this repository:
   ```bash
   git clone <your-repo-url>
   cd fastmcp_server
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Prefect and create the Secret block:
   ```bash
   # Register Prefect blocks
   prefect block register --module prefect.blocks.system
   
   # Create the Asana access token secret (replace with your actual token)
   python -c "
   from prefect.blocks.system import Secret
   secret_block = Secret(value='{\"token\": \"your_asana_personal_access_token_here\"}')
   secret_block.save('asana-access-token')
   print('✅ Asana secret block created successfully')
   "
   ```

4. Test the server locally:
   ```bash
   python server.py
   ```

### Getting Your Asana Personal Access Token

1. Log in to your Asana account
2. Go to [Asana Developer Console](https://app.asana.com/0/developer-console)
3. Click "+ New access token"
4. Provide a description (e.g., "FastMCP Server")
5. Accept the API terms and create the token
6. Save the token - you'll need it for Prefect Secret block configuration

## Deployment to FastMCP Cloud

### Step 1: Prepare Your Repository

Ensure your repository contains:
- ✅ `server.py` - Your FastMCP server file with Asana integration
- ✅ `requirements.txt` - Dependencies specification (including asana client and prefect)
- ✅ `env.example` - Prefect Secret block configuration reference
- ✅ This README with documentation

**Important**: You'll need to configure the 'asana-access-token' Prefect Secret block in your deployment environment.

### Step 2: Push to GitHub

1. Commit your changes:
   ```bash
   git add .
   git commit -m "Add FastMCP server implementation"
   ```

2. Push to GitHub:
   ```bash
   git push origin main
   ```

### Step 3: Deploy on FastMCP Cloud

1. **Visit FastMCP Cloud**: Go to [https://fastmcp.cloud/](https://fastmcp.cloud/)

2. **Sign in**: Use your GitHub account to sign in

3. **Create New Project**:
   - Click "Create New Project"
   - Connect your GitHub repository
   - Configure your project:
     - **Name**: Choose a unique name (this will be part of your server URL)
     - **Entrypoint**: Set to `server.py`
     - **Authentication**: Choose public or organization-restricted access

4. **Configure Prefect Secret Block**:
   - Ensure Prefect is set up in your deployment environment
   - Create the Prefect Secret block in your deployment environment:
     ```bash
     # In your deployment environment
     prefect block register --module prefect.blocks.system
     
     # Create the secret block
     python -c "
     from prefect.blocks.system import Secret
     secret_block = Secret(value='{\"token\": \"your_asana_personal_access_token_here\"}')
     secret_block.save('asana-access-token')
     "
     ```

5. **Automatic Deployment**: FastMCP Cloud will:
   - Clone your repository
   - Install dependencies from `requirements.txt` (including Asana client and Prefect)
   - Access the configured Prefect Secret blocks
   - Build and deploy your server
   - Provide a unique URL like `https://your-project-name.fastmcp.app/mcp`

### Step 5: Access Your Server

Once deployed, your MCP server will be accessible at:
```
https://your-project-name.fastmcp.app/mcp
```

You can connect to this server using any MCP-compatible client.

## Automatic Updates

FastMCP Cloud monitors your GitHub repository and automatically redeploys when you push changes to the `main` branch. For pull requests, it creates separate test deployments.

## Customizing Your Server

To add new tools to your server:

1. Edit `server.py`
2. Add new functions decorated with `@mcp.tool()`
3. Update dependencies in `requirements.txt` if needed
4. Commit and push changes
5. FastMCP Cloud will automatically redeploy

### Example: Adding a New Tool

```python
@mcp.tool()
def reverse_string(text: str) -> str:
    """
    Reverse the characters in a string.
    
    Args:
        text: The string to reverse
        
    Returns:
        The reversed string
    """
    return text[::-1]
```

## Asana Integration Usage Examples

### Creating Tasks

```python
# Basic task creation
create_asana_task(
    name="Review project proposal",
    notes="Review the Q4 project proposal and provide feedback"
)

# Task with project assignment and due date
create_asana_task(
    name="Prepare presentation",
    notes="Create slides for the client meeting",
    project_gid="1234567890123456",
    due_date="2024-01-15",
    priority="high"
)
```

### Updating Tasks

```python
# Mark task as completed
update_asana_task(
    task_gid="1234567890123456",
    completed="true"
)

# Update task details
update_asana_task(
    task_gid="1234567890123456",
    name="Updated task name",
    notes="Updated description",
    due_date="2024-01-20",
    priority="medium"
)
```

### Searching and Listing

```python
# Search for tasks
search_asana_tasks(
    query="presentation",
    completed="false"
)

# List all projects
list_asana_projects()

# Get task details
get_asana_task(task_gid="1234567890123456")
```

## Finding Project and Task GIDs

To use the Asana tools effectively, you'll need GIDs (Global IDs):

1. **Project GIDs**: Use `list_asana_projects()` to get all your project GIDs
2. **Task GIDs**: Use `search_asana_tasks()` to find tasks and get their GIDs
3. **User GIDs**: Available through the Asana web interface or API

### Getting GIDs from Asana URLs

You can also extract GIDs from Asana URLs:
- Project URL: `https://app.asana.com/0/1234567890123456/list` → Project GID: `1234567890123456`
- Task URL: `https://app.asana.com/0/1234567890123456/9876543210987654` → Task GID: `9876543210987654`

## Troubleshooting

### Asana Authentication Issues

If you're getting authentication errors:

1. **Verify your Prefect Secret block**: Make sure the 'asana-access-token' Prefect Secret block is correctly configured
2. **Check Secret format**: Ensure the Secret value is a valid JSON object with a "token" field
3. **Check token permissions**: Ensure the token has access to the projects/tasks you're trying to access
4. **Token expiration**: Personal Access Tokens don't expire, but check if the token was revoked
5. **Workspace access**: Make sure you're in the correct Asana workspace
6. **Prefect setup**: Ensure Prefect is properly installed and configured

### Common Error Messages

- `"Error: Asana client not initialized"`: The 'asana-access-token' Prefect Secret block is not configured or accessible
- `"403 Forbidden"`: Your token doesn't have permission to access the requested resource
- `"404 Not Found"`: The specified task or project GID doesn't exist or you don't have access
- `"Failed to load Asana credentials from Prefect Secret"`: The Secret block name is incorrect or the JSON format is invalid

### Prefect Secret Block Configuration Format

Your 'asana-access-token' Prefect Secret block should be configured with:

```json
{
  "token": "your_actual_asana_personal_access_token_here"
}
```

### Creating the Secret Block via Prefect UI

Alternatively, you can create the Secret block via the Prefect UI:

1. Start Prefect server: `prefect server start`
2. Open Prefect UI in your browser (usually http://localhost:4200)
3. Go to Blocks → Create Block → Secret
4. Name: `asana-access-token`
5. Value: `{"token": "your_asana_personal_access_token_here"}`
6. Save the block

### Testing Locally

To test your Asana integration locally with Prefect Secret blocks:

```bash
# Ensure Prefect blocks are registered
prefect block register --module prefect.blocks.system

# Create the secret block (replace with your actual token)
python -c "
from prefect.blocks.system import Secret
secret_block = Secret(value='{\"token\": \"your_token_here\"}')
secret_block.save('asana-access-token')
"

# Run the server
python server.py

# You should see: "✅ Asana client initialized successfully using Prefect Secret block"
```

## Support

- [FastMCP Documentation](https://fastmcp.wiki/)
- [FastMCP Cloud Deployment Guide](https://fastmcp.wiki/en/deployment/fastmcp-cloud)
- [MCP Protocol Specification](https://spec.modelcontextprotocol.io/)
- [Asana API Documentation](https://developers.asana.com/docs)
- [Asana Python Client](https://github.com/Asana/python-asana)
- [Prefect Documentation](https://docs.prefect.io/)
- [Prefect Blocks Documentation](https://docs.prefect.io/concepts/blocks/)
