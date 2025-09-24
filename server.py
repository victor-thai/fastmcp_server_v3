from fastmcp import FastMCP
import asana
import os

# Initialize the FastMCP server
mcp = FastMCP("AsanaTaskManager")

# Initialize Asana client using access token
token = os.getenv("ASANA_ACCESS_TOKEN")

asana_projects = {
    "Analytics Team Status": "1200797787407318",
    "Engineering (Data Solutions)": "1199170187515375"
}

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
    project: str = "", 
    assignee_gid: str = "", 
    due_date: str = "",
    priority: str = ""
) -> str:
    """
    Create a new task in Asana.
    
    Args:
        name: The name/title of the task
        notes: Detailed description of the task (optional)
        project: Project name (e.g. "Analytics Team Status") or GID to add the task to (optional)
        assignee_gid: The GID of the user to assign the task to (optional)
        due_date: Due date in YYYY-MM-DD format (optional)
        priority: Task priority - 'low', 'medium', 'high', or 'urgent' (optional)
        
    Available projects:
        - Analytics Team Status
        - Engineering (Data Solutions)
        
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
        if project:
            # Check if project is a name in our mapping, otherwise use as GID
            project_gid = asana_projects.get(project, project)
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
        
        result = tasks_api.create_task(
            body={'data': task_data}, 
            opts={'opt_fields': 'gid,name,permalink_url'}
        )
        
        return f"✅ Task created successfully!\nTask ID: {result['gid']}\nName: {result['name']}\nURL: {result.get('permalink_url', 'N/A')}"
        
    except Exception as e:
        return f"Error creating task: {str(e)}"

@mcp.tool()
def update_asana_task(
    task_name_or_gid: str,
    project: str = "",
    new_name: str = "",
    notes: str = "",
    completed: str = "",
    due_date: str = "",
    priority: str = ""
) -> str:
    """
    Update an existing Asana task. Can find task by name within a project or use direct GID.
    
    Args:
        task_name_or_gid: Either the task name to search for or the direct GID of the task
        project: Project name (e.g. "Analytics Team Status") or GID to search within (required if using task name)
        new_name: New name/title for the task (optional)
        notes: New description for the task (optional)
        completed: Mark task as completed - 'true' or 'false' (optional)
        due_date: New due date in YYYY-MM-DD format (optional)
        priority: New priority - 'low', 'medium', 'high', or 'urgent' (optional)
        
    Available projects:
        - Analytics Team Status
        - Engineering (Data Solutions)
        
    Returns:
        Success message with updated task details or error message
    """
    if not tasks_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Determine if we need to search for the task or if we have a direct GID
        task_gid = None
        
        # If it looks like a GID (long number), use it directly
        if task_name_or_gid.isdigit() and len(task_name_or_gid) > 10:
            task_gid = task_name_or_gid
        else:
            # Search for the task by name within the project
            if not project:
                return "Error: Project name or GID is required when searching by task name."
            
            # Get project GID from name mapping if needed
            project_gid = asana_projects.get(project, project)
            
            # Get user's workspace to search in
            me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
            workspace_gid = me['workspaces'][0]['gid']
            
            # Search for tasks with this name in the specified project
            search_params = {
                'text': task_name_or_gid,
                'projects.any': project_gid,
                'completed': False  # Search incomplete tasks by default
            }
            
            tasks = tasks_api.search_tasks_for_workspace(
                workspace_gid=workspace_gid,
                opts={'opt_fields': 'name,gid,completed'},
                **search_params
            )
            
            # Find exact match or best match
            matching_tasks = []
            for task in tasks:
                if task['name'].lower() == task_name_or_gid.lower():
                    matching_tasks.append(task)
                elif task_name_or_gid.lower() in task['name'].lower():
                    matching_tasks.append(task)
            
            if not matching_tasks:
                return f"❌ No tasks found matching '{task_name_or_gid}' in project '{project}'"
            elif len(matching_tasks) > 1:
                task_list = "\n".join([f"• {task['name']} (GID: {task['gid']})" for task in matching_tasks[:5]])
                return f"❌ Multiple tasks found matching '{task_name_or_gid}':\n{task_list}\n\nPlease use a more specific name or the exact GID."
            else:
                task_gid = matching_tasks[0]['gid']
                print(f"✅ Found task: {matching_tasks[0]['name']} (GID: {task_gid})")
        
        # Build update data
        task_data = {}
        
        # Add fields to update if provided
        if new_name:
            task_data['name'] = new_name
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
        
        # Update the task
        result = tasks_api.update_task(
            body={'data': task_data}, 
            task_gid=task_gid, 
            opts={'opt_fields': 'gid,name,completed'}
        )
        
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
            task_gid=task_gid,
            opts={'opt_fields': 'name,notes,completed,due_on,created_at,modified_at,assignee.name,projects.name,permalink_url'}
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
        me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
        
        # Get projects for the user
        projects = projects_api.get_projects(
            opts={'opt_fields': 'name,gid,created_at,modified_at'},
            workspace=me['workspaces'][0]['gid']
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
def list_available_projects() -> str:
    """
    List the available project names and their GIDs from the local mapping.
    
    Returns:
        List of available project names that can be used in other functions
    """
    if not asana_projects:
        return "No project mappings configured."
    
    project_list = "📋 Available Projects (you can use these names in other functions):\n\n"
    for project_name, project_gid in asana_projects.items():
        project_list += f"• **{project_name}**\n  GID: {project_gid}\n\n"
    
    project_list += "💡 You can use either the project name or GID in create_asana_task and search_asana_tasks functions."
    
    return project_list

@mcp.tool()
def search_asana_tasks(query: str, project: str = "", completed: str = "false") -> str:
    """
    Search for tasks in Asana.
    
    Args:
        query: Search query to find tasks
        project: Project name (e.g. "Analytics Team Status") or GID to limit search to (optional)
        completed: Include completed tasks - 'true' or 'false' (default: 'false')
        
    Available projects:
        - Analytics Team Status
        - Engineering (Data Solutions)
        
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
        
        if project:
            # Check if project is a name in our mapping, otherwise use as GID
            project_gid = asana_projects.get(project, project)
            search_params['projects.any'] = project_gid
        
        tasks = tasks_api.search_tasks_for_workspace(
            workspace_gid=workspace_gid,
            opts={'opt_fields': 'name,gid,completed,due_on,assignee.name'},
            **search_params
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