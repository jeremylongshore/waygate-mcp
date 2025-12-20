#!/usr/bin/env python3
"""
Firebase MCP Server Integration Plugin for Waygate MCP
Integrates Google's official Firebase CLI MCP server
"""

import os
import json
import logging
from typing import Dict, Any, List

from .mcp_bridge_plugin import MCPBridgePlugin

logger = logging.getLogger("waygate_mcp.firebase_mcp")

class FirebaseMCPPlugin(MCPBridgePlugin):
    """
    Firebase MCP Server integration for Waygate MCP

    Integrates Google's official Firebase CLI MCP server to provide:
    - 30+ Firebase management tools
    - Project configuration and management
    - Authentication and user management
    - Firestore database operations
    - Cloud Functions deployment
    - Firebase Hosting management
    - Real-time database operations

    This plugin bridges the Firebase CLI MCP server (experimental) with Waygate MCP,
    enabling seamless Firebase operations through the unified Waygate interface.
    """

    def __init__(self):
        super().__init__()
        self.name = "Firebase MCP Integration"
        self.version = "1.0.0"
        self.description = "Official Firebase CLI MCP server integration for DiagnosticPro platform management"

        # Firebase MCP configuration
        self.mcp_config = {
            "communication_method": "stdio",
            "server_type": "firebase",
            "credentials": {}
        }

    async def get_mcp_server_command(self) -> List[str]:
        """
        Get the command to start Firebase CLI MCP server

        Returns:
            Command to execute Firebase CLI in MCP mode
        """
        # Firebase CLI MCP server command (experimental feature)
        return [
            "npx",
            "firebase-tools@beta",
            "--experimental",
            "mcp"
        ]

    async def get_mcp_server_config(self) -> Dict[str, Any]:
        """
        Get Firebase MCP server configuration

        Returns:
            Firebase-specific configuration
        """
        return {
            "project_id": os.getenv("FIREBASE_PROJECT_ID", "diagnostic-pro-start-up"),
            "service_account_path": os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            "region": os.getenv("FIREBASE_REGION", "us-central1"),
            "features": [
                "auth",
                "firestore",
                "functions",
                "hosting",
                "storage",
                "realtime-database"
            ]
        }

    async def initialize(self):
        """Initialize Firebase MCP plugin"""
        logger.info("🔥 Initializing Firebase MCP plugin...")

        # Load Firebase credentials and configuration
        await self._load_firebase_credentials()

        # Initialize parent MCP bridge
        await super().initialize()

        logger.info(f"✅ Firebase MCP plugin initialized with {len(self.mcp_tools)} tools")

    async def _load_firebase_credentials(self):
        """Load Firebase credentials from environment"""
        try:
            # Firebase project configuration
            project_id = os.getenv("FIREBASE_PROJECT_ID")
            service_account = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

            if not project_id:
                logger.warning("⚠️ FIREBASE_PROJECT_ID not set, using default: diagnostic-pro-start-up")
                project_id = "diagnostic-pro-start-up"

            self.credentials = {
                "FIREBASE_PROJECT_ID": project_id,
                "GOOGLE_APPLICATION_CREDENTIALS": service_account,
                "FIREBASE_REGION": os.getenv("FIREBASE_REGION", "us-central1")
            }

            # Update MCP config with credentials
            self.mcp_config["credentials"] = self.credentials

            logger.debug(f"🔑 Firebase credentials loaded for project: {project_id}")

        except Exception as e:
            logger.error(f"❌ Failed to load Firebase credentials: {e}")
            raise

    async def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get Firebase-specific tools

        Returns:
            List of Firebase MCP tools with Waygate-specific enhancements
        """
        # Get tools from Firebase MCP server
        firebase_tools = await super().get_tools()

        # Add Waygate-specific tool metadata and DiagnosticPro context
        enhanced_tools = []

        for tool in firebase_tools:
            enhanced_tool = tool.copy()

            # Add DiagnosticPro-specific context and usage examples
            if tool["name"] == "firebase_auth_list_users":
                enhanced_tool["description"] += " | DiagnosticPro: List customer accounts"
                enhanced_tool["use_case"] = "diagnosticpro_user_management"

            elif tool["name"] == "firebase_firestore_get":
                enhanced_tool["description"] += " | DiagnosticPro: Get diagnostic submissions"
                enhanced_tool["use_case"] = "diagnosticpro_data_retrieval"

            elif tool["name"] == "firebase_firestore_set":
                enhanced_tool["description"] += " | DiagnosticPro: Store diagnostic results"
                enhanced_tool["use_case"] = "diagnosticpro_data_storage"

            elif tool["name"] == "firebase_functions_deploy":
                enhanced_tool["description"] += " | DiagnosticPro: Deploy diagnostic AI functions"
                enhanced_tool["use_case"] = "diagnosticpro_deployment"

            elif tool["name"] == "firebase_hosting_deploy":
                enhanced_tool["description"] += " | DiagnosticPro: Deploy customer platform"
                enhanced_tool["use_case"] = "diagnosticpro_hosting"

            # Add tool category for organization
            enhanced_tool["category"] = "firebase"
            enhanced_tool["provider"] = "google_firebase"
            enhanced_tool["integration"] = "mcp_bridge"

            enhanced_tools.append(enhanced_tool)

        # Add custom DiagnosticPro-specific tools
        enhanced_tools.extend(await self._get_diagnosticpro_tools())

        return enhanced_tools

    async def _get_diagnosticpro_tools(self) -> List[Dict[str, Any]]:
        """
        Get DiagnosticPro-specific Firebase tools

        Returns:
            Custom tools tailored for DiagnosticPro operations
        """
        return [
            {
                "name": "diagnosticpro_get_submission",
                "description": "Get a diagnostic submission from Firestore",
                "category": "diagnosticpro",
                "provider": "firebase_firestore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "submission_id": {
                            "type": "string",
                            "description": "Diagnostic submission ID"
                        }
                    },
                    "required": ["submission_id"]
                }
            },
            {
                "name": "diagnosticpro_create_order",
                "description": "Create a new order in Firestore",
                "category": "diagnosticpro",
                "provider": "firebase_firestore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "customer_email": {
                            "type": "string",
                            "description": "Customer email address"
                        },
                        "equipment_type": {
                            "type": "string",
                            "description": "Type of equipment being diagnosed"
                        },
                        "issue_description": {
                            "type": "string",
                            "description": "Description of the issue"
                        },
                        "payment_intent_id": {
                            "type": "string",
                            "description": "Stripe payment intent ID"
                        }
                    },
                    "required": ["customer_email", "equipment_type", "issue_description"]
                }
            },
            {
                "name": "diagnosticpro_get_analytics",
                "description": "Get DiagnosticPro platform analytics",
                "category": "diagnosticpro",
                "provider": "firebase_firestore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date_range": {
                            "type": "string",
                            "description": "Date range for analytics (7d, 30d, 90d)",
                            "default": "7d"
                        },
                        "metric": {
                            "type": "string",
                            "description": "Metric to retrieve (orders, revenue, users)",
                            "default": "orders"
                        }
                    }
                }
            },
            {
                "name": "diagnosticpro_deploy_functions",
                "description": "Deploy DiagnosticPro Cloud Functions",
                "category": "diagnosticpro",
                "provider": "firebase_functions",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "function_name": {
                            "type": "string",
                            "description": "Name of function to deploy (or 'all' for all functions)"
                        },
                        "environment": {
                            "type": "string",
                            "description": "Target environment (staging, production)",
                            "default": "staging"
                        }
                    },
                    "required": ["function_name"]
                }
            }
        ]

    async def execute(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute Firebase tool with DiagnosticPro-specific handling

        Args:
            tool_name: Name of the tool to execute
            parameters: Tool parameters

        Returns:
            Tool execution result with DiagnosticPro context
        """
        logger.debug(f"🔥 Executing Firebase tool: {tool_name}")

        try:
            # Handle DiagnosticPro-specific tools
            if tool_name.startswith("diagnosticpro_"):
                return await self._execute_diagnosticpro_tool(tool_name, parameters)

            # Execute standard Firebase MCP tools
            result = await super().execute(tool_name, parameters)

            # Add DiagnosticPro context to results
            if result.get("success"):
                result["context"] = {
                    "platform": "diagnosticpro",
                    "project_id": self.credentials.get("FIREBASE_PROJECT_ID"),
                    "tool_category": "firebase"
                }

            return result

        except Exception as e:
            logger.error(f"❌ Firebase tool execution failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "context": "firebase_mcp_plugin"
            }

    async def _execute_diagnosticpro_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute DiagnosticPro-specific Firebase tools

        Args:
            tool_name: DiagnosticPro tool name
            parameters: Tool parameters

        Returns:
            Tool execution result
        """
        if tool_name == "diagnosticpro_get_submission":
            return await self._get_diagnostic_submission(parameters["submission_id"])

        elif tool_name == "diagnosticpro_create_order":
            return await self._create_diagnostic_order(parameters)

        elif tool_name == "diagnosticpro_get_analytics":
            return await self._get_platform_analytics(parameters)

        elif tool_name == "diagnosticpro_deploy_functions":
            return await self._deploy_diagnostic_functions(parameters)

        else:
            return {
                "success": False,
                "error": f"Unknown DiagnosticPro tool: {tool_name}"
            }

    async def _get_diagnostic_submission(self, submission_id: str) -> Dict[str, Any]:
        """Get a diagnostic submission from Firestore"""
        # Use Firebase MCP to get document from Firestore
        result = await super().execute("firebase_firestore_get", {
            "collection": "diagnosticSubmissions",
            "document": submission_id
        })

        if result.get("success"):
            return {
                "success": True,
                "submission": result["result"],
                "submission_id": submission_id,
                "context": "diagnosticpro_platform"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get diagnostic submission: {submission_id}",
                "submission_id": submission_id
            }

    async def _create_diagnostic_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new diagnostic order in Firestore"""
        import uuid
        from datetime import datetime

        # Generate order ID
        order_id = str(uuid.uuid4())

        # Prepare order document
        order_doc = {
            "id": order_id,
            "customerEmail": order_data["customer_email"],
            "equipmentType": order_data["equipment_type"],
            "issueDescription": order_data["issue_description"],
            "paymentIntentId": order_data.get("payment_intent_id"),
            "status": "pending",
            "createdAt": datetime.utcnow().isoformat(),
            "updatedAt": datetime.utcnow().isoformat()
        }

        # Use Firebase MCP to create document in Firestore
        result = await super().execute("firebase_firestore_set", {
            "collection": "orders",
            "document": order_id,
            "data": order_doc
        })

        if result.get("success"):
            return {
                "success": True,
                "order_id": order_id,
                "order": order_doc,
                "context": "diagnosticpro_platform"
            }
        else:
            return {
                "success": False,
                "error": "Failed to create diagnostic order",
                "order_data": order_data
            }

    async def _get_platform_analytics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get DiagnosticPro platform analytics"""
        date_range = params.get("date_range", "7d")
        metric = params.get("metric", "orders")

        # Use Firebase MCP to query analytics collection
        result = await super().execute("firebase_firestore_query", {
            "collection": "analytics",
            "where": [
                ["metric", "==", metric],
                ["dateRange", "==", date_range]
            ],
            "orderBy": [["timestamp", "desc"]],
            "limit": 1
        })

        if result.get("success"):
            analytics_data = result["result"]
            return {
                "success": True,
                "analytics": analytics_data,
                "metric": metric,
                "date_range": date_range,
                "context": "diagnosticpro_analytics"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to get analytics for metric: {metric}",
                "metric": metric,
                "date_range": date_range
            }

    async def _deploy_diagnostic_functions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy DiagnosticPro Cloud Functions"""
        function_name = params["function_name"]
        environment = params.get("environment", "staging")

        # Map function names to actual function files
        function_mapping = {
            "analyze_diagnostic": "functions/analyzeDiagnostic.js",
            "generate_report": "functions/generateReport.js",
            "send_email": "functions/sendEmail.js",
            "process_payment": "functions/processPayment.js",
            "all": None  # Deploy all functions
        }

        if function_name not in function_mapping:
            return {
                "success": False,
                "error": f"Unknown function: {function_name}",
                "available_functions": list(function_mapping.keys())
            }

        # Use Firebase MCP to deploy functions
        deploy_params = {
            "only": f"functions:{function_name}" if function_name != "all" else "functions"
        }

        if environment == "production":
            deploy_params["project"] = self.credentials.get("FIREBASE_PROJECT_ID")

        result = await super().execute("firebase_functions_deploy", deploy_params)

        if result.get("success"):
            return {
                "success": True,
                "deployed_function": function_name,
                "environment": environment,
                "deployment_result": result["result"],
                "context": "diagnosticpro_deployment"
            }
        else:
            return {
                "success": False,
                "error": f"Failed to deploy function: {function_name}",
                "function_name": function_name,
                "environment": environment
            }

    def get_info(self) -> Dict[str, str]:
        """Get Firebase MCP plugin information"""
        base_info = super().get_info()
        base_info.update({
            "firebase_project": self.credentials.get("FIREBASE_PROJECT_ID", "not_configured"),
            "firebase_region": self.credentials.get("FIREBASE_REGION", "us-central1"),
            "mcp_server": "firebase_cli_experimental",
            "integration_type": "stdio_mcp_bridge"
        })
        return base_info