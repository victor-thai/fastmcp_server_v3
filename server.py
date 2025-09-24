from fastmcp import FastMCP
import asana
import os

# Initialize the FastMCP server
mcp = FastMCP("AsanaTaskManager")

# Initialize Asana client using access token
token = os.get_env("ASANA-ACCESS-TOKEN")

# Configure Asana client with access token
configuration = asana.Configuration()
configuration.access_token = token
api_client = asana.ApiClient(configuration)

# Initialize API clients
tasks_api = asana.TasksApi(api_client)
projects_api = asana.ProjectsApi(api_client)
users_api = asana.UsersApi(api_client)
    


# Asana Task Management Tools

@mcp.tool()
def create_asana_task(
    name: str, 
    notes: str = "", 
    project_gid: str = "", 
    assignee_gid: str = "", 
    due_date: str = "",
    priority: str = ""
) -> str:
    """
    Create a new task in Asana.
    
    Args:
        name: The name/title of the task
        notes: Detailed description of the task (optional)
        project_gid: The GID of the project to add the task to (optional)
        assignee_gid: The GID of the user to assign the task to (optional)
        due_date: Due date in YYYY-MM-DD format (optional)
        priority: Task priority - 'low', 'medium', 'high', or 'urgent' (optional)
        
    Returns:
        Success message with task details or error message
    """
    if not tasks_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        task_data = {
            'name': name,
            'notes': notes
        }
        
        # Add optional fields if provided
        if project_gid:
            task_data['projects'] = [project_gid]
        if assignee_gid:
            task_data['assignee'] = assignee_gid
        if due_date:
            task_data['due_on'] = due_date
        
        # Map priority to Asana's format
        priority_mapping = {
            'low': 'Low',
            'medium': 'Medium', 
            'high': 'High',
            'urgent': 'Urgent'
        }
        if priority and priority.lower() in priority_mapping:
            task_data['priority'] = priority_mapping[priority.lower()]
        
        result = tasks_api.create_task(body={'data': task_data})
        
        return f"✅ Task created successfully!\nTask ID: {result['gid']}\nName: {result['name']}\nURL: {result.get('permalink_url', 'N/A')}"
        
    except Exception as e:
        return f"Error creating task: {str(e)}"

@mcp.tool()
def update_asana_task(
    task_gid: str,
    name: str = "",
    notes: str = "",
    completed: str = "",
    due_date: str = "",
    priority: str = ""
) -> str:
    """
    Update an existing Asana task.
    
    Args:
        task_gid: The GID of the task to update
        name: New name/title for the task (optional)
        notes: New description for the task (optional)
        completed: Mark task as completed - 'true' or 'false' (optional)
        due_date: New due date in YYYY-MM-DD format (optional)
        priority: New priority - 'low', 'medium', 'high', or 'urgent' (optional)
        
    Returns:
        Success message with updated task details or error message
    """
    if not tasks_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        task_data = {}
        
        # Add fields to update if provided
        if name:
            task_data['name'] = name
        if notes:
            task_data['notes'] = notes
        if completed.lower() in ['true', 'false']:
            task_data['completed'] = completed.lower() == 'true'
        if due_date:
            task_data['due_on'] = due_date
            
        # Map priority to Asana's format
        priority_mapping = {
            'low': 'Low',
            'medium': 'Medium',
            'high': 'High', 
            'urgent': 'Urgent'
        }
        if priority and priority.lower() in priority_mapping:
            task_data['priority'] = priority_mapping[priority.lower()]
        
        if not task_data:
            return "Error: No fields provided to update. Please specify at least one field to update."
        
        result = tasks_api.update_task(task_gid, body={'data': task_data})
        
        return f"✅ Task updated successfully!\nTask ID: {result['gid']}\nName: {result['name']}\nCompleted: {result['completed']}"
        
    except Exception as e:
        return f"Error updating task: {str(e)}"

@mcp.tool()
def get_asana_task(task_gid: str) -> str:
    """
    Get details of an Asana task.
    
    Args:
        task_gid: The GID of the task to retrieve
        
    Returns:
        Task details or error message
    """
    if not tasks_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        result = tasks_api.get_task(
            task_gid,
            opt_fields=['name', 'notes', 'completed', 'due_on', 'created_at', 'modified_at', 'assignee.name', 'projects.name', 'permalink_url']
        )
        
        task_info = f"""📋 Task Details:
• ID: {result['gid']}
• Name: {result['name']}
• Completed: {'✅ Yes' if result['completed'] else '❌ No'}
• Due Date: {result.get('due_on', 'Not set')}
• Assignee: {result.get('assignee', {}).get('name', 'Unassigned')}
• Projects: {', '.join([p['name'] for p in result.get('projects', [])])}
• Created: {result.get('created_at', 'N/A')}
• Modified: {result.get('modified_at', 'N/A')}
• URL: {result.get('permalink_url', 'N/A')}

📝 Notes: {result.get('notes', 'No notes')}"""
        
        return task_info
        
    except Exception as e:
        return f"Error retrieving task: {str(e)}"

@mcp.tool()
def list_asana_projects() -> str:
    """
    List all projects accessible to the authenticated user.
    
    Returns:
        List of projects with their GIDs and names or error message
    """
    if not projects_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Get the authenticated user first
        me = users_api.get_user('me')
        
        # Get projects for the user
        projects = projects_api.get_projects(
            owner=me['gid'],
            opt_fields=['name', 'gid', 'created_at', 'modified_at']
        )
        
        if not projects:
            return "No projects found."
        
        project_list = "📁 Your Asana Projects:\n\n"
        for project in projects:
            project_list += f"• {project['name']} (GID: {project['gid']})\n"
        
        return project_list
        
    except Exception as e:
        return f"Error listing projects: {str(e)}"

@mcp.tool()
def search_asana_tasks(query: str, project_gid: str = "", completed: str = "false") -> str:
    """
    Search for tasks in Asana.
    
    Args:
        query: Search query to find tasks
        project_gid: Limit search to specific project (optional)
        completed: Include completed tasks - 'true' or 'false' (default: 'false')
        
    Returns:
        List of matching tasks or error message
    """
    if not tasks_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Get user's workspace
        me = users_api.get_user('me')
        workspace_gid = me['workspaces'][0]['gid']
        
        search_params = {
            'text': query,
            'completed': completed.lower() == 'true'
        }
        
        if project_gid:
            search_params['projects.any'] = project_gid
        
        tasks = tasks_api.search_tasks_for_workspace(
            workspace_gid,
            **search_params,
            opt_fields=['name', 'gid', 'completed', 'due_on', 'assignee.name']
        )
        
        if not tasks:
            return f"No tasks found matching '{query}'."
        
        task_list = f"🔍 Search Results for '{query}':\n\n"
        for task in tasks:
            status = "✅" if task['completed'] else "❌"
            due = task.get('due_on', 'No due date')
            assignee = task.get('assignee', {}).get('name', 'Unassigned')
            task_list += f"{status} {task['name']} (GID: {task['gid']})\n   Due: {due} | Assigned to: {assignee}\n\n"
        
        return task_list
        
    except Exception as e:
        return f"Error searching tasks: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)