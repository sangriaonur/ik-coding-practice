
import os
import json
import random # Needed for escalate_to_engineer
from openai import OpenAI
from google.colab import userdata

# Initialize OpenAI client
client = OpenAI(api_key=userdata.get('OPENAI_APIKEY'))

# --- Tool 1: Check Health ---
def get_server_health(server_id: str) -> str:
    """Returns CPU and Memory usage for a given server."""
    print(f"-> TOOL: Checking health for {server_id}...")

    metrics = {
        "payment-server-01": {"cpu": "98%", "memory": "40%", "status": "Warning"},
        "db-node-02": {"cpu": "12%", "memory": "60%", "status": "Healthy"},
        "auth-service-03": {"cpu": "45%", "memory": "95%", "status": "Critical"},
        "search-index-09": {"cpu": "10%", "memory": "15%", "status": "Error"},
        "frontend-node-04": {"cpu": "25%", "memory": "30%", "status": "Healthy"},
    }

    result = metrics.get(server_id, {"error": "Server not found. Check the ID."})
    return json.dumps(result)

# --- Tool 2: Fetch Recent Logs ---
def fetch_recent_logs(server_id: str, lines: int = 5) -> str:
    """Returns the last N lines of logs."""
    print(f"-> TOOL: Fetching last {lines} log lines for {server_id}...")

    log_database = {
        "payment-server-01": [
            "[INFO] Request received /pay/v1",
            "[WARN] CPU threshold exceeded 90%",
            "[WARN] Thread pool exhaustion",
            "[CRITICAL] Process hung, not accepting new connections",
            "[ERROR] Timeout waiting for thread"
        ],
        "db-node-02": [
            "[INFO] Backup started",
            "[INFO] Backup completed successfully",
            "[INFO] User query executed in 12ms",
            "[INFO] Health check: OK",
            "[INFO] Replication sync active"
        ],
        "auth-service-03": [
            "[INFO] Token validated user_882",
            "[WARN] Garbage collection taking too long (>5s)",
            "[ERROR] java.lang.OutOfMemoryError: Java heap space",
            "[CRITICAL] Application crashing due to memory leak",
            "[INFO] Restarting context..."
        ],
        "search-index-09": [
            "[INFO] Indexing started",
            "[ERROR] Connection refused: elastic-cluster-main:9200",
            "[ERROR] Failed to write document ID 4432",
            "[CRITICAL] Dependency Unreachable: Search Engine is down",
            "[ERROR] Retrying in 30s..."
        ],
        "frontend-node-04": [
            "[INFO] GET /home 200 OK",
            "[INFO] GET /assets/logo.png 200 OK",
            "[INFO] GET /login 200 OK",
            "[INFO] GET /api/v1/status 200 OK",
            "[INFO] Health check passed"
        ]
    }

    default_logs = ["[INFO] System stable", "[INFO] Heartbeat signal received"]

    logs = log_database.get(server_id, default_logs)
    return json.dumps({"logs": logs[:lines]})

# --- Tool 3: Restart Service ---
def restart_service(server_id: str) -> str:
    """
    Agent will restart the server when CPU hits 98% and Memory Usage hits 40%
    1. Print a message saying "-> TOOL: Restarting service..."
    2. Return a JSON string confirming the restart was successful.
       Example return: '{"status": "success", "message": "Server restarted successfully"}'
    """
    print(f"-> TOOL: RESTARTING SERVICE {server_id}...")
    return json.dumps({"status": "success", "message": f"Server {server_id} restarted successfully"})

# --- Tool 4: Escalation Tool ---
def escalate_to_engineer(summary: str) -> str:
    """
    Agent will escalate the complex issue to Engineers/Or Escalation Team
    1. Print a message saying "-> TOOL: Escalating to human..."
    2. Return a JSON string confirming the ticket was created.
    """
    ticket_id = f"INC-{random.randint(1000, 9999)}"
    print(f"-> TOOL: Escalating to human for: {summary}. Generating Ticket ID: {ticket_id}...")
    return json.dumps({"status": "success", "message": f"Escalation ticket created for: {summary}", "ticket_id": ticket_id})

# Map functions for the agent execution loop
AVAILABLE_FUNCTIONS = {
    "get_server_health": get_server_health,
    "fetch_recent_logs": fetch_recent_logs,
    "restart_service": restart_service,
    "escalate_to_engineer": escalate_to_engineer,
}

# Define Agent Schema
tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_server_health",
            "description": "Checks the current CPU and memory usage of a specific server.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server, e.g., 'payment-server-01'"}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_recent_logs",
            "description": "Retrieves the most recent log entries from a server to diagnose errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server."},
                    "lines": {"type": "integer", "description": "Number of log lines to fetch."}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "restart_service",
            "description": "Restarts a specified server to resolve performance or stability issues. Used when CPU or memory usage is critically high.",
            "parameters": {
                "type": "object",
                "properties": {
                    "server_id": {"type": "string", "description": "The ID of the server to be restarted."}
                },
                "required": ["server_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_engineer",
            "description": "Escalates the issue to a human engineer when automated fixes fail or the error is unknown or complex, providing a summary of the problem.",
            "parameters": {
                "type": "object",
                "properties": {
                     "summary": {"type": "string", "description": "A concise summary of the issue requiring escalation."}
                },
                "required": ["summary"]
            }
        }
    }
]

# The Agent Execution Loop
def run_it_agent(user_issue: str):
    print(f"\n--- New Incident: {user_issue} ---")

    messages = [
        {"role": "system", "content": "You are a Level 1 IT Responder. Investigate server issues. "
                                      "If CPU or Memory is > 90%, restart the service. If logs show critical dependency errors (like connection refused) that a restart won't fix, escalate to an engineer."},
        {"role": "user", "content": user_issue}
    ]

    while True:
        print("\n[AI Thinking...]")
        response = client.chat.completions.create(
            model="gpt-4o", # Model changed to gpt-4o as per previous instructions to resolve access error
            messages=messages,
            tools=tools_schema,
            tool_choice="auto"
        )

        response_msg = response.choices[0].message
        messages.append(response_msg)

        if response_msg.tool_calls:
            for tool_call in response_msg.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # Retrieve the actual python function based on name
                function_to_call = AVAILABLE_FUNCTIONS.get(func_name)

                if function_to_call:
                    # Execute the function
                    tool_output = function_to_call(**func_args)

                    # Append the result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": func_name,
                        "content": tool_output
                    })

        else:
            print(f"\n[FINAL RESPONSE]: {response_msg.content}")
            break
