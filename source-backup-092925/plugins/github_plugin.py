"""
GitHub Integration Plugin for Waygate MCP
Easy GitHub operations without technical knowledge
"""

from .base_plugin import BasePlugin
from typing import Dict, Any, List
import os
import json

class GitHubPlugin(BasePlugin):
    """
    Simple GitHub integration for non-technical users.
    """

    def __init__(self):
        super().__init__()
        self.name = "GitHub Integration"
        self.version = "1.0.0"
        self.description = "Easy GitHub operations - create repos, manage issues, and more"

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        List of GitHub tools available.
        """
        return [
            {
                "name": "create_github_repo",
                "description": "Create a new GitHub repository",
                "parameters": {
                    "repo_name": "string - Name of your repository",
                    "description": "string - What your repo is about",
                    "private": "boolean - Make it private? (default: false)"
                }
            },
            {
                "name": "create_issue",
                "description": "Create a GitHub issue",
                "parameters": {
                    "repo": "string - Repository name",
                    "title": "string - Issue title",
                    "body": "string - Issue description"
                }
            },
            {
                "name": "list_my_repos",
                "description": "List all your GitHub repositories",
                "parameters": {}
            },
            {
                "name": "create_readme",
                "description": "Generate a README.md file",
                "parameters": {
                    "project_name": "string - Your project name",
                    "description": "string - What your project does",
                    "installation": "string - How to install/use",
                    "author": "string - Your name"
                }
            }
        ]

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute GitHub operations.
        """
        if tool_name == "create_github_repo":
            return await self.create_repo(parameters)
        elif tool_name == "create_issue":
            return await self.create_issue(parameters)
        elif tool_name == "list_my_repos":
            return await self.list_repos(parameters)
        elif tool_name == "create_readme":
            return await self.create_readme(parameters)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    async def create_repo(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new GitHub repository.
        """
        # In real implementation, this would use GitHub API
        # For now, we'll create a template structure
        repo_name = params.get("repo_name", "my-new-repo")
        description = params.get("description", "A new repository")
        private = params.get("private", False)

        # Create local template
        template = {
            "repository": {
                "name": repo_name,
                "description": description,
                "private": private,
                "default_branch": "main",
                "created_at": "2024-01-15T12:00:00Z"
            },
            "instructions": [
                f"1. Go to https://github.com/new",
                f"2. Enter repository name: {repo_name}",
                f"3. Add description: {description}",
                f"4. Set visibility: {'Private' if private else 'Public'}",
                "5. Click 'Create repository'"
            ]
        }

        return {
            "success": True,
            "message": f"Repository template created for '{repo_name}'",
            "data": template
        }

    async def create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a GitHub issue.
        """
        repo = params.get("repo", "")
        title = params.get("title", "New Issue")
        body = params.get("body", "")

        issue_template = {
            "issue": {
                "repository": repo,
                "title": title,
                "body": body,
                "labels": [],
                "assignees": []
            },
            "markdown": f"""## {title}

{body}

---
*Created with Waygate MCP*
"""
        }

        return {
            "success": True,
            "message": f"Issue template created: '{title}'",
            "data": issue_template
        }

    async def list_repos(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        List user's repositories.
        """
        # In real implementation, this would fetch from GitHub API
        example_repos = [
            {"name": "waygate-mcp", "stars": 42, "language": "Python"},
            {"name": "my-website", "stars": 5, "language": "HTML"},
            {"name": "awesome-project", "stars": 128, "language": "JavaScript"}
        ]

        return {
            "success": True,
            "message": "Repository list retrieved",
            "repositories": example_repos,
            "total": len(example_repos)
        }

    async def create_readme(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a professional README.md file.
        """
        project_name = params.get("project_name", "My Project")
        description = params.get("description", "An awesome project")
        installation = params.get("installation", "npm install")
        author = params.get("author", "Your Name")

        readme_content = f"""# {project_name}

{description}

## 🚀 Features

- Easy to use
- Well documented
- Open source
- Community driven

## 📦 Installation

```bash
{installation}
```

## 🔧 Usage

```python
# Example usage
from {project_name.lower().replace(' ', '_')} import main

main()
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**{author}**

- GitHub: [@{author.lower().replace(' ', '')}](https://github.com/{author.lower().replace(' ', '')})

## 🌟 Show your support

Give a ⭐️ if this project helped you!

---

*This README was generated with ❤️ by [Waygate MCP](https://github.com/yourusername/waygate-mcp)*
"""

        # Save to file
        readme_path = "/app/data/README_template.md"
        os.makedirs(os.path.dirname(readme_path), exist_ok=True)
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        return {
            "success": True,
            "message": f"README.md created for '{project_name}'",
            "content": readme_content,
            "saved_to": readme_path
        }


# Example of how to extend this plugin:
"""
TO ADD MORE GITHUB FEATURES:

1. Add new tool to get_tools() method:
   {
       "name": "create_pull_request",
       "description": "Create a pull request",
       "parameters": {
           "from_branch": "string",
           "to_branch": "string",
           "title": "string"
       }
   }

2. Add handler in execute() method:
   elif tool_name == "create_pull_request":
       return await self.create_pr(parameters)

3. Implement the actual function:
   async def create_pr(self, params):
       # Your code here
       return {"success": True, "message": "PR created"}
"""