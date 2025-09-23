#!/usr/bin/env python3
"""
FastMCP Server with Asana Integration
A comprehensive MCP server using FastMCP that provides utility tools and Asana task management.
"""

from fastmcp import FastMCP
from typing import Any, Optional, List, Dict
import datetime
import json
import os
import asana

# Initialize the FastMCP server
mcp = FastMCP("AsanaTaskManager")

# Initialize Asana client using environment variable
asana_client = None

try:
    # Load Asana access token from environment variable
    token = os.getenv("ASANA-ACCESS-TOKEN")['token']
    
    if not token:
        raise ValueError("ASANA-ACCESS-TOKEN environment variable not set")
    
    # Initialize Asana client with the token
    asana_client = asana.Client.access_token(token)
    print("✅ Asana client initialized successfully using environment variable")
except Exception as e:
    print(f"⚠️  Failed to load Asana credentials from environment variable: {e}")
    print("   Asana features will be disabled. Please set the ASANA-ACCESS-TOKEN environment variable.")

@mcp.tool()
def greet(name: str) -> str:
    """
    Return a friendly greeting.
    
    Args:
        name: The name of the person to greet
    
    Returns:
        A personalized greeting message
    """
    return f"Hello, {name}! Welcome to FastMCP server."

@mcp.tool()
def echo(text: str) -> str:
    """
    Echo the provided text back to the caller.
    
    Args:
        text: The text to echo back
        
    Returns:
        The same text that was provided
    """
    return text

@mcp.tool()
def get_current_time() -> str:
    """
    Get the current date and time.
    
    Returns:
        Current timestamp as a formatted string
    """
    now = datetime.datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

@mcp.tool()
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: Mathematical expression to evaluate (e.g., "2 + 3 * 4")
        
    Returns:
        The result of the calculation or an error message
    """
    try:
        # Only allow safe mathematical operations
        allowed_chars = set('0123456789+-*/.() ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression. Only numbers and +, -, *, /, (, ) are allowed."
        
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error calculating expression: {str(e)}"

@mcp.tool()
def format_json(json_string: str, indent: int = 2) -> str:
    """
    Format a JSON string with proper indentation.
    
    Args:
        json_string: The JSON string to format
        indent: Number of spaces for indentation (default: 2)
        
    Returns:
        Formatted JSON string or error message
    """
    try:
        parsed = json.loads(json_string)
        return json.dumps(parsed, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON - {str(e)}"

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
    if not asana_client:
        return "Error: Asana client not initialized. Please set the ASANA-ACCESS-TOKEN environment variable."
    
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
        
        result = asana_client.tasks.create_task(task_data)
        
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
    if not asana_client:
        return "Error: Asana client not initialized. Please set the ASANA-ACCESS-TOKEN environment variable."
    
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
        
        result = asana_client.tasks.update_task(task_gid, task_data)
        
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
    if not asana_client:
        return "Error: Asana client not initialized. Please set the ASANA-ACCESS-TOKEN environment variable."
    
    try:
        result = asana_client.tasks.get_task(
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
    if not asana_client:
        return "Error: Asana client not initialized. Please set the ASANA-ACCESS-TOKEN environment variable."
    
    try:
        # Get the authenticated user first
        me = asana_client.users.me()
        
        # Get projects for the user
        projects = asana_client.projects.get_projects(
            {'owner': me['gid']},
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
    if not asana_client:
        return "Error: Asana client not initialized. Please set the ASANA-ACCESS-TOKEN environment variable."
    
    try:
        search_params = {
            'text': query,
            'completed': completed.lower() == 'true'
        }
        
        if project_gid:
            search_params['projects.any'] = project_gid
        
        tasks = asana_client.tasks.search_tasks_for_workspace(
            asana_client.users.me()['workspaces'][0]['gid'],
            search_params,
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
    # This allows the server to be run directly for testing
    # In production, FastMCP Cloud will handle the server startup
    print("FastMCP Server with Asana Integration initialized with tools:")
    print("\n🔧 Utility Tools:")
    print("- greet: Return a friendly greeting")
    print("- echo: Echo text back")
    print("- get_current_time: Get current timestamp")
    print("- calculate: Evaluate mathematical expressions")
    print("- format_json: Format JSON with proper indentation")
    print("\n📋 Asana Task Management Tools:")
    print("- create_asana_task: Create new tasks in Asana")
    print("- update_asana_task: Update existing Asana tasks")
    print("- get_asana_task: Get details of a specific task")
    print("- list_asana_projects: List all accessible projects")
    print("- search_asana_tasks: Search for tasks by query")
    print(f"\n🔐 Asana Status: {'✅ Connected' if asana_client else '❌ Not configured'}")
    print("\nServer is ready for deployment to FastMCP Cloud!")
