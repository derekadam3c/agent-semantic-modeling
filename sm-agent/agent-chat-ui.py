"""
Power BI Semantic Modeling Agent - Chat Interface

A simple Gradio-based chat interface to interact with your deployed agent
like you would with GitHub Copilot or ChatGPT.
"""

import gradio as gr
import requests
import json
import re
from datetime import datetime
from typing import List, Tuple

# Agent configuration
AGENT_URL = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io"
AGENT_INVOKE = f"{AGENT_URL}/invoke"
AGENT_HEALTH = f"{AGENT_URL}/health"

# System prompt to guide the chat
SYSTEM_PROMPT = """You are an AI assistant for the Power BI Semantic Modeling Agent.

Your capabilities:
- Generate Power BI semantic models from CSV, SQL, Lakehouse, or Tableau data sources
- Auto-detect relationships between tables
- Create date hierarchies
- Suggest measures and KPIs
- Generate TMDL (model definition) files
- Optimize for Direct Lake or Import mode

When users provide data source URLs, call the agent to generate models.
When users ask questions, explain the agent's capabilities and guide them.
"""


def extract_url_from_message(message: str) -> str:
    """Extract URL from user message"""
    url_pattern = r'(https?://[^\s]+\.(?:csv|xlsx|xls|parquet))'
    match = re.search(url_pattern, message, re.IGNORECASE)
    return match.group(1) if match else None


def determine_file_type(url: str) -> str:
    """Determine file type from URL"""
    url_lower = url.lower()
    if url_lower.endswith('.csv'):
        return 'csv'
    elif url_lower.endswith(('.xlsx', '.xls')):
        return 'excel'
    elif url_lower.endswith('.parquet'):
        return 'parquet'
    else:
        return 'csv'  # default


def call_agent(url: str, model_name: str = "ChatGeneratedModel", dry_run: bool = True) -> dict:
    """Call the semantic modeling agent"""
    
    file_type = determine_file_type(url)
    
    payload = {
        "schema_source": {
            "type": file_type,
            "url": url,
        },
        "model_name": model_name,
        "dry_run": dry_run,
        "generation_options": {
            "auto_detect_relationships": True,
            "create_date_hierarchies": True,
            "suggest_measures": True,
            "detect_fact_dimensions": True,
        }
    }
    
    try:
        response = requests.post(AGENT_INVOKE, json=payload, timeout=60)
        return {
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": response.json()
        }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timed out (agent took too long to respond)"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def check_agent_health() -> dict:
    """Check if agent is healthy"""
    try:
        response = requests.get(AGENT_HEALTH, timeout=10)
        return response.json()
    except:
        return {"status": "unhealthy"}


def format_agent_response(result: dict) -> str:
    """Format agent response for chat display"""
    
    if not result.get("success"):
        error_msg = result.get("error", "Unknown error")
        if isinstance(result.get("data"), dict):
            error_detail = result["data"].get("detail", {})
            if isinstance(error_detail, dict):
                error_msg = error_detail.get("error_message", error_msg)
        
        return f"❌ **Error**: {error_msg}\n\nPlease check:\n- URL is accessible\n- File format is supported (CSV, Excel, Parquet)\n- File has proper structure"
    
    data = result.get("data", {})
    
    # Format success response
    response = "✅ **Semantic Model Generated Successfully!**\n\n"
    
    # Model info
    if "model_name" in data:
        response += f"**Model Name**: {data['model_name']}\n"
    
    # Tables
    tables = data.get("tables", [])
    if tables:
        response += f"\n**Tables** ({len(tables)}):\n"
        for table in tables[:5]:  # Show first 5
            table_name = table.get("name", "Unknown")
            column_count = len(table.get("columns", []))
            response += f"  • {table_name} - {column_count} columns\n"
        if len(tables) > 5:
            response += f"  ... and {len(tables) - 5} more\n"
    
    # Relationships
    relationships = data.get("relationships", [])
    if relationships:
        response += f"\n**Relationships** ({len(relationships)}):\n"
        for rel in relationships[:5]:  # Show first 5
            from_table = rel.get("from_table", "")
            to_table = rel.get("to_table", "")
            response += f"  • {from_table} → {to_table}\n"
        if len(relationships) > 5:
            response += f"  ... and {len(relationships) - 5} more\n"
    
    # Measures
    measures = data.get("measures", [])
    if measures:
        response += f"\n**Suggested Measures** ({len(measures)}):\n"
        for measure in measures[:5]:
            measure_name = measure.get("name", "Unknown")
            response += f"  • {measure_name}\n"
        if len(measures) > 5:
            response += f"  ... and {len(measures) - 5} more\n"
    
    # Hierarchies
    hierarchies = data.get("hierarchies", [])
    if hierarchies:
        response += f"\n**Hierarchies** ({len(hierarchies)}):\n"
        for hierarchy in hierarchies[:3]:
            hier_name = hierarchy.get("name", "Unknown")
            response += f"  • {hier_name}\n"
    
    # TMDL preview
    if "tmdl" in data:
        tmdl_preview = data["tmdl"][:500]
        response += f"\n**TMDL Preview**:\n```\n{tmdl_preview}...\n```\n"
    
    response += "\n💡 **Tip**: This was a dry-run. Set `dry_run: false` to deploy to Fabric."
    
    return response


def chat_response(message: str, history: List[Tuple[str, str]]) -> str:
    """Process chat message and return response"""
    
    message_lower = message.lower()
    
    # Check for health check request
    if "health" in message_lower or "status" in message_lower:
        health = check_agent_health()
        status = health.get("status", "unknown")
        version = health.get("version", "unknown")
        environment = health.get("environment", "unknown")
        
        return f"🏥 **Agent Health Check**\n\n**Status**: {status}\n**Version**: {version}\n**Environment**: {environment}\n\nAgent is {'✅ operational' if status == 'healthy' else '❌ not responding'}!"
    
    # Check for help/capabilities request
    if any(word in message_lower for word in ["help", "what can you do", "capabilities", "how to"]):
        return """🤖 **Power BI Semantic Modeling Agent**

I can help you generate Power BI semantic models automatically!

**What I can do**:
✅ Generate semantic models from data sources
✅ Auto-detect relationships between tables
✅ Create date/time hierarchies
✅ Suggest measures and KPIs
✅ Generate TMDL model definitions
✅ Optimize for Direct Lake or Import mode

**Supported data sources**:
• CSV files (via URL)
• Excel files (.xlsx, .xls)
• Parquet files
• SQL databases
• Lakehouse tables
• Tableau workbooks

**How to use me**:
Just paste a data source URL in the chat! Example:
```
"Generate a model from https://example.com/sales-data.csv"
```

Or ask me specific questions about Power BI modeling!

**Try these commands**:
• "Check agent health" - Verify agent status
• "Help" - Show this message
• Paste any CSV/Excel URL to generate a model
"""
    
    # Check if message contains a URL
    url = extract_url_from_message(message)
    
    if url:
        # Extract model name if mentioned
        model_name = "ChatGeneratedModel"
        if "name" in message_lower or "call it" in message_lower:
            # Simple extraction - could be improved
            words = message.split()
            for i, word in enumerate(words):
                if word.lower() in ["name", "called", "call"] and i + 1 < len(words):
                    model_name = words[i + 1].strip('",.')
                    break
        
        # Call the agent
        thinking_msg = f"🤔 Analyzing data source: `{url}`\n\n⏳ Generating semantic model..."
        
        result = call_agent(url, model_name, dry_run=True)
        return format_agent_response(result)
    
    # General conversation fallback
    return """I'm specialized in generating Power BI semantic models. 

To help you, please:
1. **Provide a data source URL** (CSV, Excel, Parquet)
2. **Ask about my capabilities** ("What can you do?")
3. **Check my status** ("Are you healthy?")

Example: "Generate model from https://yourdata.com/sales.csv"

Need help? Just ask! 😊"""


# Create Gradio chat interface
with gr.Blocks(title="PBI Semantic Agent Chat", theme=gr.themes.Soft()) as demo:
    gr.Markdown("""
    # 🤖 Power BI Semantic Modeling Agent Chat
    
    Talk to your deployed agent like you would with Copilot!
    
    **Agent Endpoint**: https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io
    """)
    
    chatbot = gr.Chatbot(
        label="Chat with PBI Semantic Agent",
        height=500,
        avatar_images=(None, "🤖"),
    )
    
    msg = gr.Textbox(
        label="Your message",
        placeholder="Try: 'What can you do?' or paste a CSV URL...",
        lines=2,
    )
    
    with gr.Row():
        submit = gr.Button("Send", variant="primary")
        clear = gr.Button("Clear")
    
    gr.Markdown("""
    ### Quick Examples:
    - "What can you do?"
    - "Check agent health"
    - "Generate model from https://example.com/data.csv"
    - "Help me create a semantic model"
    """)
    
    gr.Markdown("""
    ### 📚 Documentation:
    - **API Docs**: [View Swagger](https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/docs)
    - **Health Check**: [Agent Status](https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/health)
    """)
    
    # Chat interactions
    def user(user_message, history):
        return "", history + [[user_message, None]]
    
    def bot(history):
        user_message = history[-1][0]
        bot_message = chat_response(user_message, history[:-1])
        history[-1][1] = bot_message
        return history
    
    msg.submit(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    submit.click(user, [msg, chatbot], [msg, chatbot], queue=False).then(
        bot, chatbot, chatbot
    )
    clear.click(lambda: None, None, chatbot, queue=False)


if __name__ == "__main__":
    print("🚀 Starting PBI Semantic Agent Chat Interface...")
    print(f"📡 Agent URL: {AGENT_URL}")
    print(f"🏥 Checking agent health...")
    
    health = check_agent_health()
    if health.get("status") == "healthy":
        print("✅ Agent is healthy and ready!")
    else:
        print("⚠️  Warning: Agent may not be responding")
    
    print("\n🌐 Launching chat interface...")
    print("💡 Access at: http://localhost:7860")
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )
