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

# Dynamic user cache - automatically populated
_user_cache = {}
_cache_timestamp = None
_cache_duration = 3600  # Cache for 1 hour

# Custom field mappings (you'll need to replace these GIDs with your actual custom field GIDs)
asana_custom_fields = {
    "Clients": "1200882907169711",      # Clients field
    "Platform": "1206936878420527",     # Platform field (multi-enum)
    "Priority": "1199170187515380",     # Priority field
    "Task Progress": "1200841656461302", # Task Progress field
    "Status": "1200907941118113",       # Status field
    "Effort": "1200907941118107",       # Effort field
}

# Custom field options mappings (for enum/dropdown fields)
# Replace with your actual option GIDs from Asana
asana_field_options = {
    "Clients": {
        "Toyota Norcal": "1200882907169712",
        "VSP": "1200882907169713",
        "Upwork": "1200886612503481",
        "McD": "1200886612503484",
        "SCCBS": "1200886612503489",
        "DCCU": "1200886612504515",
        "Workrise": "1200886612504519",
        "Edwards": "1200886612504523",
        "H&L": "1200886588859928",
        "AAA": "1200894863268356",
        "OMCA": "1201000955909543",
        "TNTP": "1202825105164617",
        "NC Wesleyan University (Liaison)": "1203145583060478",
        "Hub Garage": "1203247286336143",
        "Toyota + McD": "1204261931716483",
        "DuckHorn": "1208345915618445",
        "Toyota KC": "1208524887452169",
        "Qualified": "1209674556515681",
        "New Business/Not Listed Above": "1210702117547501",
        "Grocery Outlet": "1211333012050767"
    },
    "Platform": {
        # Platform options from your Platform field (multi-enum)
        "Nexxen / Amobee": "1206936878420530",
        "Amazon": "1206936878420531",
        "The Trade Desk": "1206936878420532",
        "CM360 (Direct Buys / PMAX)": "1206936878420533",
        "SA360 (Search)": "1206936878420534",
        "Google Ads (Youtube)": "1206936878420535",
        "Pinterest": "1206936878420536",
        "Meta": "1206936878420537",
        "TikTok": "1206936878420538",
        "Snapchat": "1206936878420539",
        "Reddit": "1206936878420540",
        "LinkedIn": "1206936878420541",
        "Twitter / X": "1206936878420542",
        "AdMedia (Search)": "1206936878420543",
        "Yelp": "1206937011155710",
        "Next Door": "1206937011155711"
    },
    "Priority": {
        "Low": "1199170187515383",
        "Medium": "1199170187515382",
        "High": "1199170187515381"
    },
    "Task Progress": {
        "Not Started": "1200841656461303",
        "In Progress": "1200841656461304",
        "Waiting": "1200841656461305",
        "Deferred": "1200841656461306",
        "Done": "1200841656461307"
    },
    "Status": {
        "Complete": "1200907941118114",
        "Blocked": "1200907941118115",
        "In Progress": "1200907941118116"
    },
    "Effort": {
        "Small": "1200907941118108",
        "Medium": "1200907941118109",
        "Large": "1200907941118110"
    }
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

def get_custom_field_value(field_name: str, value: str) -> str:
    """
    Get the option GID for a custom field enum value.
    
    Args:
        field_name: The name of the custom field (e.g., 'client', 'platform', 'priority')
        value: The option value (e.g., 'web', 'high', 'acme corp')
        
    Returns:
        The option GID if found, otherwise the original value
    """
    if not value:
        return ""
    
    # Convert to lowercase for case-insensitive matching
    value_lower = value.lower()
    
    # Check if we have options for this field
    if field_name in asana_field_options:
        field_options = asana_field_options[field_name]
        
        # Try exact match first
        if value_lower in field_options:
            return field_options[value_lower]
        
        # Try partial match
        for option_name, option_gid in field_options.items():
            if value_lower in option_name.lower() or option_name.lower() in value_lower:
                return option_gid
    
    # If no match found, return original value (might be a GID already)
    return value

def _fetch_workspace_users():
    """
    Fetch and cache workspace users with detailed error handling.
    """
    global _user_cache, _cache_timestamp
    import time
    
    # Check if cache is still valid
    current_time = time.time()
    if _cache_timestamp and (current_time - _cache_timestamp) < _cache_duration and _user_cache:
        return _user_cache
    
    if not users_api:
        print("Error: users_api not initialized")
        return {}
    
    try:
        # Get workspace with better error handling
        me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
        if not me.get('workspaces'):
            print("Error: No workspaces found for current user")
            return {}
        
        workspace_gid = me['workspaces'][0]['gid']
        print(f"Debug: Using workspace GID: {workspace_gid}")
        
        # Fetch users with better error handling
        users_response = users_api.get_users_for_workspace(
            workspace_gid=workspace_gid,
            opts={'opt_fields': 'gid,name,email'}
        )
        
        # Handle both list and dict responses
        if isinstance(users_response, dict) and 'data' in users_response:
            users = users_response['data']
        elif isinstance(users_response, list):
            users = users_response
        else:
            users = [users_response] if users_response else []
        
        print(f"Debug: Found {len(users)} users in workspace")
        
        # Build cache with multiple lookup keys
        _user_cache = {}
        for user in users:
            if not isinstance(user, dict):
                continue
                
            name = user.get('name', '').strip()
            email = user.get('email', '').strip()
            gid = user.get('gid', '').strip()
            
            if not gid:
                continue
                
            print(f"Debug: Processing user - Name: '{name}', Email: '{email}', GID: {gid}")
            
            # Add exact name
            if name:
                _user_cache[name.lower()] = gid
                
                # Add first name + last initial (e.g., "John D" for "John Doe")
                name_parts = name.split()
                if len(name_parts) >= 2:
                    first_last_initial = f"{name_parts[0]} {name_parts[-1][0]}".lower()
                    _user_cache[first_last_initial] = gid
                    
                    # Add first name only
                    _user_cache[name_parts[0].lower()] = gid
            
            # Add email
            if email:
                _user_cache[email.lower()] = gid
            
            # Add GID (for direct lookups)
            _user_cache[gid] = gid
        
        _cache_timestamp = current_time
        print(f"Debug: User cache built with {len(_user_cache)} entries")
        return _user_cache
        
    except Exception as e:
        print(f"Error fetching workspace users: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return _user_cache if _user_cache else {}

def resolve_assignee(assignee: str) -> str:
    """
    Intelligently resolve assignee name to GID with fuzzy matching.
    
    Args:
        assignee: Full name, partial name, email, or GID
        
    Returns:
        The assignee GID, or original value if not found
    """
    if not assignee:
        return ""
    
    assignee_lower = assignee.lower().strip()
    
    # If it looks like a GID, return as-is
    if assignee.isdigit() and len(assignee) > 10:
        return assignee
    
    # Fetch/update user cache
    user_cache = _fetch_workspace_users()
    
    # Exact match
    if assignee_lower in user_cache:
        return user_cache[assignee_lower]
    
    # Fuzzy matching for partial names
    best_match = None
    best_score = 0
    
    for cached_key, gid in user_cache.items():
        if cached_key == gid:  # Skip GID entries
            continue
            
        # Check if assignee is contained in cached name
        if assignee_lower in cached_key:
            score = len(assignee_lower) / len(cached_key)  # Prefer longer matches
            if score > best_score:
                best_match = gid
                best_score = score
        
        # Check if cached name is contained in assignee
        elif cached_key in assignee_lower:
            score = len(cached_key) / len(assignee_lower)
            if score > best_score:
                best_match = gid
                best_score = score
    
    # Return best match if confidence is high enough
    if best_match and best_score > 0.3:
        return best_match
    
    # If no match found, assume it's already a GID or email
    return assignee

def _build_task_data(name: str = "", notes: str = "", project: str = "", assignee: str = "", 
                    due_date: str = "", priority: str = "", client: str = "", platform: str = "", 
                    status: str = "", effort: str = "", completed: str = "", new_name: str = "") -> dict:
    """
    Build task data dictionary with all validations and transformations.
    """
    from datetime import datetime, timedelta
    
    task_data = {}
    
    # Basic fields
    if name:
        task_data['name'] = name
    if new_name:
        task_data['name'] = new_name
    if notes:
        task_data['notes'] = notes
    if completed and completed.lower() in ['true', 'false']:
        task_data['completed'] = completed.lower() == 'true'
    
    # Project
    if project:
        project_gid = asana_projects.get(project, project)
        task_data['projects'] = [project_gid]
    
    # Assignee with intelligent resolution
    if assignee:
        task_data['assignee'] = resolve_assignee(assignee)
    
    # Due date with flexible parsing
    if due_date:
        formatted_date = _parse_due_date(due_date)
        if formatted_date:
            task_data['due_on'] = formatted_date
    
    # Priority
    if priority:
        priority_map = {'low': 'Low', 'medium': 'Medium', 'high': 'High', 'urgent': 'Urgent'}
        if priority.lower() in priority_map:
            task_data['priority'] = priority_map[priority.lower()]
    
    # Custom fields
    custom_fields = {}
    field_mappings = [
        (client, "Clients"), (platform, "Platform"), 
        (status, "Status"), (effort, "Effort")
    ]
    
    for value, field_name in field_mappings:
        if value and field_name in asana_custom_fields:
            option_gid = get_custom_field_value(field_name, value)
            if option_gid:
                custom_fields[asana_custom_fields[field_name]] = option_gid
    
    if custom_fields:
        task_data['custom_fields'] = custom_fields
    
    return task_data

def _parse_due_date(due_date: str) -> str:
    """
    Parse due date with support for relative and absolute formats.
    """
    if not due_date:
        return ""
    
    from datetime import datetime, timedelta
    
    # Handle relative dates
    if due_date.lower() in ['today', 'now']:
        return datetime.now().strftime('%Y-%m-%d')
    elif due_date.lower() == 'tomorrow':
        return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    elif due_date.lower().endswith('days'):
        try:
            days = int(due_date.lower().replace('days', '').strip())
            return (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
        except ValueError:
            pass
    
    # Try various date formats
    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%d/%m/%Y', '%Y/%m/%d', '%m/%d/%y', '%m-%d-%y']:
        try:
            return datetime.strptime(due_date, fmt).strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    return due_date  # Return as-is if no format matched

@mcp.tool()
def create_asana_task(
    name: str, 
    notes: str = "", 
    project: str = "", 
    assignee: str = "", 
    due_date: str = "",
    priority: str = "",
    client: str = "",
    platform: str = "",
    status: str = "",
    effort: str = ""
) -> str:
    """
    Create a new task in Asana with intelligent assignee matching.
    
    Args:
        name: The name/title of the task
        notes: Detailed description of the task (optional)
        project: Project name or GID (optional)
        assignee: Full name, partial name, email, or GID (optional)
        due_date: Due date - supports 'today', 'tomorrow', '5 days', YYYY-MM-DD, MM/DD/YYYY, etc. (optional)
        priority: 'low', 'medium', 'high', or 'urgent' (optional)
        client: Client name (optional)
        platform: Platform name (optional)
        status: Status (optional)
        effort: Effort level (optional)
        
    Returns:
        Success message with task details or error message
    """
    if not tasks_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        task_data = _build_task_data(
            name=name, notes=notes, project=project, assignee=assignee,
            due_date=due_date, priority=priority, client=client, 
            platform=platform, status=status, effort=effort
        )
        
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
    assignee: str = "",
    priority: str = "",
    client: str = "",
    platform: str = "",
    status: str = "",
    effort: str = ""
) -> str:
    """
    Update an existing Asana task. Can find task by name within a project or use direct GID.
    
    Args:
        task_name_or_gid: Either the task name to search for or the direct GID of the task
        project: Project name (e.g. "Analytics Team Status") or GID to search within (required if using task name)
        new_name: New name/title for the task (optional)
        notes: New description for the task (optional)
        completed: Mark task as completed - 'true' or 'false' (optional)
        due_date: New due date in various formats - YYYY-MM-DD, MM/DD/YYYY, 'today', 'tomorrow', '5 days' (optional)
        assignee: Full name, partial name, email, or GID (optional)
        priority: New priority - 'low', 'medium', 'high', or 'urgent' (optional)
        client: Client name for the task (optional)
        platform: Platform for the task (optional)
        status: Status for the task (optional)
        effort: Effort level for the task (optional)
        
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
        
        # Build update data using shared function
        task_data = _build_task_data(
            new_name=new_name, notes=notes, assignee=assignee, due_date=due_date,
            priority=priority, client=client, platform=platform, 
            status=status, effort=effort, completed=completed
        )
        
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
def list_custom_field_options() -> str:
    """
    List all available options for custom fields (client, platform, priority).
    
    Returns:
        List of available options for each custom field
    """
    options_info = "📋 Available Custom Field Options:\n\n"
    
    for field_name, field_options in asana_field_options.items():
        options_info += f"**{field_name.title()}:**\n"
        if field_options:
            for option_name, option_gid in field_options.items():
                configured = "✅" if not option_gid.startswith("REPLACE_") else "❌"
                options_info += f"  {configured} {option_name}\n"
        else:
            options_info += "  No options configured\n"
        options_info += "\n"
    
    options_info += """💡 **Usage Examples:**
• create_asana_task("Fix bug", client="acme corp", platform="web")
• update_asana_task("Fix bug", project="Engineering", client="tech solutions")

⚙️ **Configuration Status:**
❌ = Option GID needs to be configured
✅ = Option GID is configured

To configure option GIDs, replace the placeholder values in asana_field_options dictionary."""
    
    return options_info

@mcp.tool()
def find_team_member_gid(full_name: str) -> str:
    """
    Search for a team member by their full name and return their GID.
    
    Args:
        full_name: The full name of the team member to search for
        
    Returns:
        The team member's GID and details, or error message if not found
    """
    if not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    if not full_name or not full_name.strip():
        return "Error: Please provide a name to search for."
    
    try:
        # Force refresh cache to get latest users
        global _cache_timestamp
        _cache_timestamp = None  # Force refresh
        user_cache = _fetch_workspace_users()
        
        if not user_cache:
            return "❌ Unable to fetch team members from workspace. Please check your Asana access token and permissions."
        
        search_name = full_name.lower().strip()
        
        # Try exact match first
        if search_name in user_cache:
            gid = user_cache[search_name]
            return f"✅ **Found exact match!**\nName: {full_name}\nGID: {gid}\n\nYou can now use '{full_name}' as assignee in create_asana_task() and update_asana_task()."
        
        # Try partial matches
        matches = []
        for cached_name, gid in user_cache.items():
            if cached_name == gid:  # Skip GID entries
                continue
            if search_name in cached_name or cached_name in search_name:
                matches.append((cached_name, gid))
        
        if matches:
            result = f"🔍 **Found {len(matches)} potential match(es) for '{full_name}':**\n\n"
            for cached_name, gid in matches[:5]:  # Show top 5 matches
                result += f"• **{cached_name.title()}** → GID: {gid}\n"
            
            if len(matches) == 1:
                result += f"\n✅ **Best match:** {matches[0][0].title()}\nGID: {matches[0][1]}\n"
            
            return result
        else:
            # Show available team members for reference
            result = f"❌ **No matches found for '{full_name}'**\n\n📋 **Available team members:**\n"
            
            # Get actual user details for display
            me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
            workspace_gid = me['workspaces'][0]['gid']
            users_response = users_api.get_users_for_workspace(
                workspace_gid=workspace_gid,
                opts={'opt_fields': 'gid,name,email'}
            )
            
            # Handle response format
            if isinstance(users_response, dict) and 'data' in users_response:
                users = users_response['data']
            elif isinstance(users_response, list):
                users = users_response
            else:
                users = [users_response] if users_response else []
            
            for user in users[:10]:  # Show first 10 users
                name = user.get('name', 'No name')
                gid = user.get('gid', '')
                result += f"• **{name}** (GID: {gid})\n"
            
            if len(users) > 10:
                result += f"... and {len(users) - 10} more team members\n"
            
            return result
        
    except Exception as e:
        return f"Error searching for team member: {str(e)}"

@mcp.tool()
def test_assignee_resolution(test_name: str) -> str:
    """
    Test the assignee resolution system with various name formats.
    
    Args:
        test_name: Name to test (e.g., "John", "Jane Smith", "john@company.com")
        
    Returns:
        Resolution result showing what GID would be used
    """
    if not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        resolved_gid = resolve_assignee(test_name)
        
        # Get user cache to show available options
        user_cache = _fetch_workspace_users()
        
        result = f"🔍 **Testing assignee resolution for: '{test_name}'**\n\n"
        result += f"✅ **Resolved to GID:** {resolved_gid}\n\n"
        
        # Show if we found a match in cache
        found_match = False
        for cached_key, gid in user_cache.items():
            if gid == resolved_gid and cached_key != gid:
                result += f"📝 **Matched against:** {cached_key}\n"
                found_match = True
                break
        
        if not found_match and resolved_gid != test_name:
            result += "📝 **Match type:** Direct GID or email\n"
        elif not found_match:
            result += "📝 **Match type:** No match found (returned as-is)\n"
        
        result += "\n💡 **Available team members for reference:**\n"
        
        # Show first few team members as examples
        me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
        workspace_gid = me['workspaces'][0]['gid']
        users = users_api.get_users_for_workspace(
            workspace_gid=workspace_gid,
            opts={'opt_fields': 'gid,name,email'}
        )
        
        for i, user in enumerate(users[:3]):  # Show first 3 users
            name = user.get('name', 'No name')
            result += f"• {name}\n"
            if name:
                name_parts = name.split()
                if len(name_parts) >= 2:
                    result += f"  - Try: '{name_parts[0]}' or '{name_parts[0]} {name_parts[-1][0]}'\n"
        
        if len(users) > 3:
            result += f"... and {len(users) - 3} more team members\n"
        
        return result
        
    except Exception as e:
        return f"Error testing assignee resolution: {str(e)}"

@mcp.tool()
def get_team_members() -> str:
    """
    Get team members from your workspace with intelligent name matching.
    
    Returns:
        List of team members showing how they can be referenced
    """
    if not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Force refresh cache and get users
        global _cache_timestamp
        _cache_timestamp = None  # Force refresh
        user_cache = _fetch_workspace_users()
        
        if not user_cache:
            return "❌ No team members found or unable to fetch from workspace. Please check your Asana access token and permissions."
        
        # Get actual user details
        me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
        workspace_gid = me['workspaces'][0]['gid']
        users_response = users_api.get_users_for_workspace(
            workspace_gid=workspace_gid,
            opts={'opt_fields': 'gid,name,email'}
        )
        
        # Handle response format
        if isinstance(users_response, dict) and 'data' in users_response:
            users = users_response['data']
        elif isinstance(users_response, list):
            users = users_response
        else:
            users = [users_response] if users_response else []
        
        if not users:
            return f"❌ No users found in workspace {workspace_gid}. Please check your permissions."
        
        result = f"👥 **Team Members ({len(users)} found):**\n\n"
        
        for user in users:
            if not isinstance(user, dict):
                continue
                
            name = user.get('name', 'No name')
            email = user.get('email', 'No email')
            gid = user.get('gid', 'No GID')
            
            result += f"**{name}**\n"
            result += f"  • Full name: \"{name}\"\n"
            
            if name and name != 'No name':
                name_parts = name.split()
                if len(name_parts) >= 2:
                    result += f"  • Short form: \"{name_parts[0]} {name_parts[-1][0]}\"\n"
                    result += f"  • First name: \"{name_parts[0]}\"\n"
            
            if email and email != 'No email':
                result += f"  • Email: \"{email}\"\n"
            
            result += f"  • GID: {gid}\n\n"
        
        result += "💡 **Usage Examples:**\n"
        result += '• create_asana_task("Fix bug", assignee="John Doe")\n'
        result += '• create_asana_task("Fix bug", assignee="John D")\n'
        result += '• create_asana_task("Fix bug", assignee="John")\n'
        result += '• create_asana_task("Fix bug", assignee="john@company.com")\n\n'
        result += f'📋 **Workspace Info:** {workspace_gid}\n'
        result += f'💾 **Cache Status:** {len(user_cache)} entries cached\n\n'
        result += '💡 **Find a specific GID:** Use find_team_member_gid("Full Name") to search for someone specific.\n'
        result += '💡 **Test the resolution:** Use test_assignee_resolution("Your Name") to see how names are matched.\n'
        result += '📝 **Create subtasks:** Use create_subtask() or create_multiple_subtasks() to add subtasks under existing tasks.\n'
        
        return result
        
    except Exception as e:
        return f"Error getting team members: {str(e)}"


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

@mcp.tool()
def create_subtask(
    parent_task_name_or_gid: str,
    subtask_name: str,
    project: str = "",
    notes: str = "",
    assignee: str = "",
    due_date: str = "",
    priority: str = "",
    client: str = "",
    platform: str = "",
    status: str = "",
    effort: str = ""
) -> str:
    """
    Create a subtask under an existing parent task.
    
    Args:
        parent_task_name_or_gid: Name or GID of the parent task
        subtask_name: Name of the new subtask
        project: Project name to search in (required if using parent task name)
        notes: Subtask description (optional)
        assignee: Full name, partial name, email, or GID (optional)
        due_date: Due date - supports various formats (optional)
        priority: 'low', 'medium', 'high', or 'urgent' (optional)
        client: Client name (optional)
        platform: Platform name (optional)
        status: Status (optional)
        effort: Effort level (optional)
        
    Returns:
        Success message with subtask details or error message
    """
    if not tasks_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Find the parent task
        parent_task_gid = None
        
        # If it looks like a GID, use it directly
        if parent_task_name_or_gid.isdigit() and len(parent_task_name_or_gid) > 10:
            parent_task_gid = parent_task_name_or_gid
        else:
            # Search for the parent task by name
            if not project:
                return "Error: Project name or GID is required when searching by task name."
            
            project_gid = asana_projects.get(project, project)
            me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
            workspace_gid = me['workspaces'][0]['gid']
            
            search_params = {
                'text': parent_task_name_or_gid,
                'projects.any': project_gid,
                'completed': False
            }
            
            tasks = tasks_api.search_tasks_for_workspace(
                workspace_gid=workspace_gid,
                opts={'opt_fields': 'name,gid'},
                **search_params
            )
            
            # Handle response format
            if isinstance(tasks, dict) and 'data' in tasks:
                tasks = tasks['data']
            elif not isinstance(tasks, list):
                tasks = [tasks] if tasks else []
            
            matching_tasks = []
            for task in tasks:
                if task['name'].lower() == parent_task_name_or_gid.lower():
                    matching_tasks.append(task)
                elif parent_task_name_or_gid.lower() in task['name'].lower():
                    matching_tasks.append(task)
            
            if not matching_tasks:
                return f"❌ No parent task found matching '{parent_task_name_or_gid}' in project '{project}'"
            elif len(matching_tasks) > 1:
                task_list = "\n".join([f"• {task['name']} (GID: {task['gid']})" for task in matching_tasks[:5]])
                return f"❌ Multiple parent tasks found:\n{task_list}\n\nPlease use a more specific name or the exact GID."
            else:
                parent_task_gid = matching_tasks[0]['gid']
        
        # Create the subtask
        subtask_data = _build_task_data(
            name=subtask_name, notes=notes, assignee=assignee, due_date=due_date,
            priority=priority, client=client, platform=platform, 
            status=status, effort=effort
        )
        
        # Add parent relationship
        subtask_data['parent'] = parent_task_gid
        
        result = tasks_api.create_task(
            body={'data': subtask_data}, 
            opts={'opt_fields': 'gid,name,parent.name,permalink_url'}
        )
        
        parent_name = result.get('parent', {}).get('name', 'Unknown')
        return f"✅ Subtask created successfully!\nSubtask: {result['name']}\nParent Task: {parent_name}\nSubtask ID: {result['gid']}\nURL: {result.get('permalink_url', 'N/A')}"
        
    except Exception as e:
        return f"Error creating subtask: {str(e)}"

@mcp.tool()
def create_multiple_subtasks(
    parent_task_name_or_gid: str,
    subtask_list: str,
    project: str = "",
    assignee: str = "",
    due_date: str = "",
    priority: str = "",
    client: str = "",
    platform: str = ""
) -> str:
    """
    Create multiple subtasks under a parent task from a list.
    
    Args:
        parent_task_name_or_gid: Name or GID of the parent task
        subtask_list: Comma-separated or newline-separated list of subtask names
        project: Project name to search in (required if using parent task name)
        assignee: Assignee for all subtasks (optional)
        due_date: Due date for all subtasks (optional)
        priority: Priority for all subtasks (optional)
        client: Client for all subtasks (optional)
        platform: Platform for all subtasks (optional)
        
    Returns:
        Summary of created subtasks or error message
    """
    if not tasks_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Parse the subtask list
        if '\n' in subtask_list:
            subtasks = [task.strip() for task in subtask_list.split('\n') if task.strip()]
        else:
            subtasks = [task.strip() for task in subtask_list.split(',') if task.strip()]
        
        if not subtasks:
            return "Error: No subtasks provided. Please provide a comma-separated or newline-separated list."
        
        # Find the parent task (same logic as create_subtask)
        parent_task_gid = None
        parent_task_name = ""
        
        if parent_task_name_or_gid.isdigit() and len(parent_task_name_or_gid) > 10:
            parent_task_gid = parent_task_name_or_gid
            # Get parent task name for display
            try:
                parent_info = tasks_api.get_task(
                    task_gid=parent_task_gid,
                    opts={'opt_fields': 'name'}
                )
                parent_task_name = parent_info.get('name', 'Unknown')
            except:
                parent_task_name = 'Unknown'
        else:
            if not project:
                return "Error: Project name or GID is required when searching by task name."
            
            project_gid = asana_projects.get(project, project)
            me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
            workspace_gid = me['workspaces'][0]['gid']
            
            search_params = {
                'text': parent_task_name_or_gid,
                'projects.any': project_gid,
                'completed': False
            }
            
            tasks = tasks_api.search_tasks_for_workspace(
                workspace_gid=workspace_gid,
                opts={'opt_fields': 'name,gid'},
                **search_params
            )
            
            # Handle response format
            if isinstance(tasks, dict) and 'data' in tasks:
                tasks = tasks['data']
            elif not isinstance(tasks, list):
                tasks = [tasks] if tasks else []
            
            matching_tasks = []
            for task in tasks:
                if task['name'].lower() == parent_task_name_or_gid.lower():
                    matching_tasks.append(task)
                elif parent_task_name_or_gid.lower() in task['name'].lower():
                    matching_tasks.append(task)
            
            if not matching_tasks:
                return f"❌ No parent task found matching '{parent_task_name_or_gid}' in project '{project}'"
            elif len(matching_tasks) > 1:
                task_list = "\n".join([f"• {task['name']} (GID: {task['gid']})" for task in matching_tasks[:5]])
                return f"❌ Multiple parent tasks found:\n{task_list}\n\nPlease use a more specific name or the exact GID."
            else:
                parent_task_gid = matching_tasks[0]['gid']
                parent_task_name = matching_tasks[0]['name']
        
        # Create all subtasks
        created_subtasks = []
        failed_subtasks = []
        
        for subtask_name in subtasks:
            try:
                subtask_data = _build_task_data(
                    name=subtask_name, assignee=assignee, due_date=due_date,
                    priority=priority, client=client, platform=platform
                )
                subtask_data['parent'] = parent_task_gid
                
                result = tasks_api.create_task(
                    body={'data': subtask_data}, 
                    opts={'opt_fields': 'gid,name'}
                )
                
                created_subtasks.append(f"✅ {result['name']} (ID: {result['gid']})")
                
            except Exception as e:
                failed_subtasks.append(f"❌ {subtask_name}: {str(e)}")
        
        # Build result summary
        result_msg = f"📋 **Subtask Creation Summary**\n"
        result_msg += f"**Parent Task:** {parent_task_name}\n\n"
        
        if created_subtasks:
            result_msg += f"**✅ Successfully Created ({len(created_subtasks)}):**\n"
            result_msg += "\n".join(created_subtasks) + "\n\n"
        
        if failed_subtasks:
            result_msg += f"**❌ Failed ({len(failed_subtasks)}):**\n"
            result_msg += "\n".join(failed_subtasks) + "\n\n"
        
        result_msg += f"**Total:** {len(created_subtasks)} created, {len(failed_subtasks)} failed"
        
        return result_msg
        
    except Exception as e:
        return f"Error creating multiple subtasks: {str(e)}"

@mcp.tool()
def list_subtasks(parent_task_name_or_gid: str, project: str = "") -> str:
    """
    List all subtasks of a parent task.
    
    Args:
        parent_task_name_or_gid: Name or GID of the parent task
        project: Project name to search in (required if using parent task name)
        
    Returns:
        List of subtasks or error message
    """
    if not tasks_api or not users_api:
        return "Error: Asana client not initialized. Please check the access token."
    
    try:
        # Find the parent task (same logic as create_subtask)
        parent_task_gid = None
        parent_task_name = ""
        
        if parent_task_name_or_gid.isdigit() and len(parent_task_name_or_gid) > 10:
            parent_task_gid = parent_task_name_or_gid
            try:
                parent_info = tasks_api.get_task(
                    task_gid=parent_task_gid,
                    opts={'opt_fields': 'name'}
                )
                parent_task_name = parent_info.get('name', 'Unknown')
            except:
                parent_task_name = 'Unknown'
        else:
            if not project:
                return "Error: Project name or GID is required when searching by task name."
            
            project_gid = asana_projects.get(project, project)
            me = users_api.get_user(user_gid='me', opts={'opt_fields': 'gid,workspaces'})
            workspace_gid = me['workspaces'][0]['gid']
            
            search_params = {
                'text': parent_task_name_or_gid,
                'projects.any': project_gid,
                'completed': False
            }
            
            tasks = tasks_api.search_tasks_for_workspace(
                workspace_gid=workspace_gid,
                opts={'opt_fields': 'name,gid'},
                **search_params
            )
            
            # Handle response format
            if isinstance(tasks, dict) and 'data' in tasks:
                tasks = tasks['data']
            elif not isinstance(tasks, list):
                tasks = [tasks] if tasks else []
            
            matching_tasks = []
            for task in tasks:
                if task['name'].lower() == parent_task_name_or_gid.lower():
                    matching_tasks.append(task)
                elif parent_task_name_or_gid.lower() in task['name'].lower():
                    matching_tasks.append(task)
            
            if not matching_tasks:
                return f"❌ No parent task found matching '{parent_task_name_or_gid}' in project '{project}'"
            elif len(matching_tasks) > 1:
                task_list = "\n".join([f"• {task['name']} (GID: {task['gid']})" for task in matching_tasks[:5]])
                return f"❌ Multiple parent tasks found:\n{task_list}\n\nPlease use a more specific name or the exact GID."
            else:
                parent_task_gid = matching_tasks[0]['gid']
                parent_task_name = matching_tasks[0]['name']
        
        # Get subtasks
        subtasks = tasks_api.get_subtasks_for_task(
            task_gid=parent_task_gid,
            opts={'opt_fields': 'name,gid,completed,due_on,assignee.name'}
        )
        
        # Handle response format
        if isinstance(subtasks, dict) and 'data' in subtasks:
            subtasks = subtasks['data']
        elif not isinstance(subtasks, list):
            subtasks = [subtasks] if subtasks else []
        
        if not subtasks:
            return f"📋 **Parent Task:** {parent_task_name}\n\n❌ No subtasks found."
        
        result = f"📋 **Parent Task:** {parent_task_name}\n"
        result += f"📝 **Subtasks ({len(subtasks)}):**\n\n"
        
        for subtask in subtasks:
            status = "✅" if subtask.get('completed') else "❌"
            name = subtask.get('name', 'No name')
            gid = subtask.get('gid', '')
            due = subtask.get('due_on', 'No due date')
            assignee = subtask.get('assignee', {}).get('name', 'Unassigned')
            
            result += f"{status} **{name}** (GID: {gid})\n"
            result += f"   📅 Due: {due} | 👤 Assigned: {assignee}\n\n"
        
        return result
        
    except Exception as e:
        return f"Error listing subtasks: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)