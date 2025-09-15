"""
Example MCP Tools - Easy templates for non-technical users to copy and modify
"""

from typing import Dict, Any, List
import json
import os
from datetime import datetime

class ExampleTools:
    """
    Simple example tools that anyone can understand and modify.
    Each tool shows a common use case with clear comments.
    """

    def __init__(self):
        self.data_dir = "/app/data"
        os.makedirs(self.data_dir, exist_ok=True)

    # ============================================
    # EXAMPLE 1: Simple Note Taking
    # ============================================
    async def save_note(self, title: str, content: str, tags: List[str] = None) -> Dict[str, Any]:
        """
        Save a note with optional tags.

        Example usage:
            await save_note("Meeting Notes", "Discussed project timeline", ["work", "important"])
        """
        note = {
            "id": datetime.now().isoformat(),
            "title": title,
            "content": content,
            "tags": tags or [],
            "created_at": datetime.now().isoformat()
        }

        # Save to file (simple JSON storage)
        filename = f"{self.data_dir}/note_{note['id'].replace(':', '-')}.json"
        with open(filename, 'w') as f:
            json.dump(note, f, indent=2)

        return {
            "success": True,
            "message": f"Note '{title}' saved successfully",
            "note_id": note['id']
        }

    # ============================================
    # EXAMPLE 2: Simple To-Do List
    # ============================================
    async def add_todo(self, task: str, priority: str = "medium") -> Dict[str, Any]:
        """
        Add a task to your to-do list.

        Priority levels: low, medium, high

        Example usage:
            await add_todo("Buy groceries", "high")
        """
        todos_file = f"{self.data_dir}/todos.json"

        # Load existing todos
        todos = []
        if os.path.exists(todos_file):
            with open(todos_file, 'r') as f:
                todos = json.load(f)

        # Add new todo
        new_todo = {
            "id": len(todos) + 1,
            "task": task,
            "priority": priority,
            "completed": False,
            "created_at": datetime.now().isoformat()
        }
        todos.append(new_todo)

        # Save back to file
        with open(todos_file, 'w') as f:
            json.dump(todos, f, indent=2)

        return {
            "success": True,
            "message": f"Added todo: {task}",
            "todo_id": new_todo['id']
        }

    # ============================================
    # EXAMPLE 3: Simple Data Lookup
    # ============================================
    async def lookup_info(self, query: str) -> Dict[str, Any]:
        """
        Look up information from a simple knowledge base.

        Example usage:
            await lookup_info("office hours")
        """
        # Simple knowledge base (you can expand this)
        knowledge_base = {
            "office hours": "Monday-Friday, 9 AM - 5 PM",
            "wifi password": "Check with IT department",
            "lunch menu": "Available in the cafeteria daily",
            "emergency contact": "Call 911 or security at ext. 5555",
            "printer location": "3rd floor, near conference room B"
        }

        # Simple search
        query_lower = query.lower()
        for key, value in knowledge_base.items():
            if query_lower in key.lower():
                return {
                    "success": True,
                    "query": query,
                    "result": value
                }

        return {
            "success": False,
            "query": query,
            "message": "No information found. Try different keywords."
        }

    # ============================================
    # EXAMPLE 4: Simple Calculator
    # ============================================
    async def calculate(self, expression: str) -> Dict[str, Any]:
        """
        Perform simple calculations.

        Example usage:
            await calculate("25 * 4")
            await calculate("150 / 3")
        """
        try:
            # Only allow safe mathematical operations
            allowed_chars = "0123456789+-*/.() "
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return {
                    "success": True,
                    "expression": expression,
                    "result": result
                }
            else:
                return {
                    "success": False,
                    "error": "Invalid characters in expression"
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Calculation error: {str(e)}"
            }

    # ============================================
    # EXAMPLE 5: Simple Reminder System
    # ============================================
    async def set_reminder(self, message: str, time: str) -> Dict[str, Any]:
        """
        Set a simple reminder.

        Example usage:
            await set_reminder("Team meeting", "2024-01-15 14:00")
        """
        reminders_file = f"{self.data_dir}/reminders.json"

        # Load existing reminders
        reminders = []
        if os.path.exists(reminders_file):
            with open(reminders_file, 'r') as f:
                reminders = json.load(f)

        # Add new reminder
        new_reminder = {
            "id": len(reminders) + 1,
            "message": message,
            "time": time,
            "created_at": datetime.now().isoformat(),
            "triggered": False
        }
        reminders.append(new_reminder)

        # Save back to file
        with open(reminders_file, 'w') as f:
            json.dump(reminders, f, indent=2)

        return {
            "success": True,
            "message": f"Reminder set for {time}: {message}",
            "reminder_id": new_reminder['id']
        }

    # ============================================
    # TEMPLATE: Create Your Own Tool
    # ============================================
    async def my_custom_tool(self, param1: str, param2: str = "default") -> Dict[str, Any]:
        """
        TEMPLATE: Copy this function and modify for your needs.

        Steps to create your own tool:
        1. Copy this function
        2. Rename it (e.g., 'check_weather', 'translate_text')
        3. Change the parameters to what you need
        4. Add your logic inside
        5. Return a dictionary with your results

        Example usage:
            await my_custom_tool("value1", "value2")
        """
        # Your custom logic here
        result = f"Processing {param1} with option {param2}"

        # Always return a dictionary with success status
        return {
            "success": True,
            "message": "Your custom tool executed",
            "result": result,
            "timestamp": datetime.now().isoformat()
        }


# ============================================
# HOW TO ADD YOUR OWN TOOLS
# ============================================
"""
TO ADD A NEW TOOL:

1. Copy one of the example functions above
2. Rename it to describe what it does
3. Modify the parameters (inputs) it needs
4. Write your logic inside the function
5. Return a dictionary with your results

EXAMPLE - Weather Checker:

async def check_weather(self, city: str) -> Dict[str, Any]:
    # This is where you'd add weather API logic
    weather_data = {
        "city": city,
        "temperature": "72°F",
        "conditions": "Sunny"
    }
    return {
        "success": True,
        "weather": weather_data
    }

TIPS:
- Keep functions simple and focused on one task
- Always include error handling
- Return clear success/failure messages
- Add comments to explain what your code does
- Test your tools before deploying
"""