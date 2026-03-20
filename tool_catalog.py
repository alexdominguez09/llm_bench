"""
Complete catalog of all tools available to the opencode agent.
Organized by MCP server/namespace.
"""

TOOL_CATALOG = {
    "filesystem": {
        "category": "File System Operations",
        "description": "File system manipulation and access tools",
        "tools": [
            {
                "name": "filesystem_read_text_file",
                "description": "Read file contents as text with encoding handling",
                "use_case": "Reading configuration files, scripts, documentation"
            },
            {
                "name": "filesystem_read_media_file",
                "description": "Read image/audio file as base64 with MIME type",
                "use_case": "Processing images, audio files, media content"
            },
            {
                "name": "filesystem_read_multiple_files",
                "description": "Read multiple files simultaneously",
                "use_case": "Batch file processing, comparing multiple files"
            },
            {
                "name": "filesystem_write_file",
                "description": "Create/overwrite file with new content",
                "use_case": "Creating configuration files, scripts, documentation"
            },
            {
                "name": "filesystem_edit_file",
                "description": "Make line-based edits to text file (returns git-style diff)",
                "use_case": "Modifying code, configuration files, documentation"
            },
            {
                "name": "filesystem_create_directory",
                "description": "Create directory or ensure it exists",
                "use_case": "Setting up project structure, organizing files"
            },
            {
                "name": "filesystem_list_directory",
                "description": "Get detailed listing of files/directories in path",
                "use_case": "Exploring directory structure, finding files"
            },
            {
                "name": "filesystem_list_directory_with_sizes",
                "description": "Get listing with file sizes",
                "use_case": "Analyzing disk usage, finding large files"
            },
            {
                "name": "filesystem_directory_tree",
                "description": "Get recursive tree view of files/directories as JSON",
                "use_case": "Project structure analysis, documentation generation"
            },
            {
                "name": "filesystem_move_file",
                "description": "Move/rename files and directories",
                "use_case": "Reorganizing files, renaming projects"
            },
            {
                "name": "filesystem_search_files",
                "description": "Recursively search for files matching pattern",
                "use_case": "Finding specific files, searching for patterns"
            },
            {
                "name": "filesystem_get_file_info",
                "description": "Get detailed metadata about file/directory",
                "use_case": "Checking file properties, permissions, timestamps"
            },
            {
                "name": "filesystem_list_allowed_directories",
                "description": "List directories server is allowed to access",
                "use_case": "Understanding accessible paths, security boundaries"
            }
        ]
    },
    
    "github": {
        "category": "GitHub Repository Management",
        "description": "GitHub repository and project management tools",
        "tools": [
            {
                "name": "github_create_repository",
                "description": "Create new GitHub repository",
                "use_case": "Setting up new projects, code repositories"
            },
            {
                "name": "github_get_file_contents",
                "description": "Get contents of file or directory from GitHub",
                "use_case": "Reading code, documentation from repositories"
            },
            {
                "name": "github_create_or_update_file",
                "description": "Create or update file in GitHub repository",
                "use_case": "Pushing code changes, updating documentation"
            },
            {
                "name": "github_delete_file",
                "description": "Delete file from GitHub repository",
                "use_case": "Removing outdated files, cleaning repositories"
            },
            {
                "name": "github_list_issues",
                "description": "List issues in GitHub repository",
                "use_case": "Tracking bugs, feature requests, project tasks"
            },
            {
                "name": "github_issue_read",
                "description": "Get information about specific issue",
                "use_case": "Reading issue details, comments, status"
            },
            {
                "name": "github_issue_write",
                "description": "Create or update issue in GitHub repository",
                "use_case": "Reporting bugs, creating feature requests"
            },
            {
                "name": "github_list_pull_requests",
                "description": "List pull requests in GitHub repository",
                "use_case": "Reviewing code changes, tracking merges"
            },
            {
                "name": "github_pull_request_read",
                "description": "Get information on specific pull request",
                "use_case": "Reviewing PR details, comments, changes"
            },
            {
                "name": "github_create_pull_request",
                "description": "Create new pull request in GitHub repository",
                "use_case": "Proposing code changes, merging features"
            },
            {
                "name": "github_merge_pull_request",
                "description": "Merge pull request in GitHub repository",
                "use_case": "Completing code reviews, merging changes"
            },
            {
                "name": "github_list_branches",
                "description": "List branches in GitHub repository",
                "use_case": "Managing development branches, releases"
            },
            {
                "name": "github_create_branch",
                "description": "Create new branch in GitHub repository",
                "use_case": "Starting new features, hotfixes"
            },
            {
                "name": "github_list_commits",
                "description": "Get list of commits of a branch",
                "use_case": "Reviewing commit history, tracking changes"
            },
            {
                "name": "github_get_commit",
                "description": "Get details for a commit",
                "use_case": "Analyzing specific changes, code reviews"
            },
            {
                "name": "github_get_latest_release",
                "description": "Get latest release in GitHub repository",
                "use_case": "Checking latest versions, release notes"
            },
            {
                "name": "github_get_release_by_tag",
                "description": "Get specific release by tag name",
                "use_case": "Finding specific versions, release details"
            },
            {
                "name": "github_request_copilot_review",
                "description": "Request GitHub Copilot code review for PR",
                "use_case": "Automated code review, quality checks"
            },
            {
                "name": "github_search_code",
                "description": "Fast code search across ALL GitHub repositories",
                "use_case": "Finding code examples, libraries, patterns"
            },
            {
                "name": "github_search_issues",
                "description": "Search for issues in GitHub repositories",
                "use_case": "Finding related issues, bug reports"
            },
            {
                "name": "github_search_pull_requests",
                "description": "Search for pull requests in GitHub repositories",
                "use_case": "Finding related PRs, code changes"
            },
            {
                "name": "github_search_repositories",
                "description": "Find GitHub repositories by name, description, topics",
                "use_case": "Discovering projects, finding examples"
            },
            {
                "name": "github_search_users",
                "description": "Find GitHub users by username, profile",
                "use_case": "Finding developers, contributors"
            }
        ]
    },
    
    "memory": {
        "category": "Knowledge Graph Management",
        "description": "Knowledge graph and memory management tools",
        "tools": [
            {
                "name": "memory_create_entities",
                "description": "Create entities in knowledge graph",
                "use_case": "Storing structured information, relationships"
            },
            {
                "name": "memory_create_relations",
                "description": "Create relations between entities",
                "use_case": "Defining relationships, connections between concepts"
            },
            {
                "name": "memory_add_observations",
                "description": "Add observations to entities",
                "use_case": "Adding facts, details to existing knowledge"
            },
            {
                "name": "memory_delete_entities",
                "description": "Delete entities and relations",
                "use_case": "Cleaning up outdated information"
            },
            {
                "name": "memory_delete_observations",
                "description": "Delete specific observations",
                "use_case": "Removing incorrect or outdated facts"
            },
            {
                "name": "memory_delete_relations",
                "description": "Delete relations",
                "use_case": "Removing incorrect relationships"
            },
            {
                "name": "memory_read_graph",
                "description": "Read entire knowledge graph",
                "use_case": "Retrieving all stored knowledge"
            },
            {
                "name": "memory_search_nodes",
                "description": "Search for nodes in knowledge graph",
                "use_case": "Finding specific information, concepts"
            },
            {
                "name": "memory_open_nodes",
                "description": "Open specific nodes by name",
                "use_case": "Accessing detailed information about entities"
            }
        ]
    },
    
    "brave-search": {
        "category": "Web Search",
        "description": "Web and local search capabilities",
        "tools": [
            {
                "name": "brave-search_brave_web_search",
                "description": "Web search using Brave Search API",
                "use_case": "General web searches, news, articles, information"
            },
            {
                "name": "brave-search_brave_local_search",
                "description": "Search for local businesses and places",
                "use_case": "Finding restaurants, services, local information"
            }
        ]
    },
    
    "context7": {
        "category": "Documentation Search",
        "description": "Documentation and library lookup tools",
        "tools": [
            {
                "name": "context7_resolve-library-id",
                "description": "Resolve package/product name to Context7 library ID",
                "use_case": "Finding library documentation, API references"
            },
            {
                "name": "context7_query-docs",
                "description": "Retrieve and query up-to-date documentation",
                "use_case": "Looking up API usage, code examples, documentation"
            }
        ]
    },
    
    "puppeteer": {
        "category": "Browser Automation",
        "description": "Browser control and automation tools",
        "tools": [
            {
                "name": "puppeteer_puppeteer_navigate",
                "description": "Navigate to URL",
                "use_case": "Visiting websites, web pages"
            },
            {
                "name": "puppeteer_puppeteer_screenshot",
                "description": "Take screenshot of page or element",
                "use_case": "Capturing web pages, visual documentation"
            },
            {
                "name": "puppeteer_puppeteer_click",
                "description": "Click element on page",
                "use_case": "Interacting with web interfaces, buttons"
            },
            {
                "name": "puppeteer_puppeteer_fill",
                "description": "Fill out input field",
                "use_case": "Filling forms, search boxes"
            },
            {
                "name": "puppeteer_puppeteer_select",
                "description": "Select element with Select tag",
                "use_case": "Choosing options from dropdowns"
            },
            {
                "name": "puppeteer_puppeteer_hover",
                "description": "Hover element on page",
                "use_case": "Triggering hover effects, tooltips"
            },
            {
                "name": "puppeteer_puppeteer_evaluate",
                "description": "Execute JavaScript in browser console",
                "use_case": "Running custom scripts, extracting data"
            }
        ]
    },
    
    "everything": {
        "category": "Utility/Demo",
        "description": "Utility and demonstration tools",
        "tools": [
            {
                "name": "everything_echo",
                "description": "Echoes back input string",
                "use_case": "Testing, debugging"
            },
            {
                "name": "everything_get-annotated-message",
                "description": "Demonstrates annotations for content metadata",
                "use_case": "Testing annotation capabilities"
            },
            {
                "name": "everything_get-env",
                "description": "Returns environment variables",
                "use_case": "Debugging MCP server configuration"
            },
            {
                "name": "everything_get-resource-links",
                "description": "Returns resource links",
                "use_case": "Testing resource management"
            },
            {
                "name": "everything_get-resource-reference",
                "description": "Returns resource reference for MCP clients",
                "use_case": "Testing resource references"
            },
            {
                "name": "everything_get-structured-content",
                "description": "Returns structured content with output schema",
                "use_case": "Testing structured data handling"
            },
            {
                "name": "everything_get-sum",
                "description": "Returns sum of two numbers",
                "use_case": "Simple calculation testing"
            },
            {
                "name": "everything_get-tiny-image",
                "description": "Returns a tiny MCP logo image",
                "use_case": "Testing image handling"
            },
            {
                "name": "everything_gzip-file-as-resource",
                "description": "Compresses file using gzip compression",
                "use_case": "Testing compression capabilities"
            },
            {
                "name": "everything_toggle-simulated-logging",
                "description": "Toggles simulated logging",
                "use_case": "Testing logging functionality"
            },
            {
                "name": "everything_toggle-subscriber-updates",
                "description": "Toggles simulated resource subscription updates",
                "use_case": "Testing subscription features"
            },
            {
                "name": "everything_trigger-long-running-operation",
                "description": "Demonstrates long running operation with progress",
                "use_case": "Testing progress reporting"
            },
            {
                "name": "everything_simulate-research-query",
                "description": "Simulates deep research operation",
                "use_case": "Testing research capabilities"
            }
        ]
    }
}

# Flattened list of all tools for easy reference
ALL_TOOLS = []
for namespace, data in TOOL_CATALOG.items():
    for tool in data["tools"]:
        ALL_TOOLS.append({
            "name": tool["name"],
            "description": tool["description"],
            "category": data["category"],
            "namespace": namespace,
            "use_case": tool["use_case"]
        })

# Count statistics
total_tools = len(ALL_TOOLS)
categories = set(tool["category"] for tool in ALL_TOOLS)
namespaces = set(tool["namespace"] for tool in ALL_TOOLS)

if __name__ == "__main__":
    print(f"Total tools available: {total_tools}")
    print(f"Categories: {', '.join(categories)}")
    print(f"Namespaces: {', '.join(namespaces)}")
    print("\nTool breakdown by category:")
    for category in sorted(categories):
        count = sum(1 for tool in ALL_TOOLS if tool["category"] == category)
        print(f"  {category}: {count} tools")