# PBI Semantic Agent - VS Code Chat Extension

Quick setup for creating a VS Code extension with chat interface for your deployed agent.

## Quick Start: Install AI Toolkit Extension

The fastest way to interact with your agent in VS Code is using the **AI Toolkit** extension:

1. **Install Extension**:
   ```
   Ctrl+Shift+X → Search "AI Toolkit" → Install
   ```
   Or: `code --install-extension ms-windows-ai-studio.windows-ai-studio`

2. **Add Custom Agent**:
   - Open AI Toolkit sidebar
   - Click "Add agent"
   - Enter endpoint: `https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke`

3. **Chat with Your Agent**:
   - Open chat panel in AI Toolkit
   - Select your agent
   - Start chatting!

---

## Option 2: Create Simple Web Chat UI (Gradio)

Run a local chat interface:

```bash
pip install gradio requests
```

Save as `chat-ui.py`:

```python
import gradio as gr
import requests
import json

AGENT_URL = "https://pbi-semantic-agent.delightfulisland-ec56bced.eastus.azurecontainerapps.io/invoke"

def chat_with_agent(message, history):
    """Send message to agent and return response"""
    
    # Parse message for data source info
    # Simple example - in production, use better parsing
    if "http" in message:
        # Extract URL from message
        import re
        url_match = re.search(r'(https?://[^\s]+)', message)
        url = url_match.group(1) if url_match else None
        
        if url:
            payload = {
                "schema_source": {
                    "type": "csv",
                    "url": url
                },
                "model_name": "ChatModel",
                "dry_run": True,
                "generation_options": {
                    "auto_detect_relationships": True,
                    "create_date_hierarchies": True,
                    "suggest_measures": True
                }
            }
            
            try:
                response = requests.post(AGENT_URL, json=payload, timeout=30)
                result = response.json()
                
                if response.status_code == 200:
                    return f"✅ Model generated!\n\n**Tables**: {len(result.get('tables', []))}\n**Relationships**: {len(result.get('relationships', []))}\n\nCheck /docs for full details."
                else:
                    return f"❌ Error: {result.get('detail', {}).get('error_message', 'Unknown error')}"
                    
            except Exception as e:
                return f"❌ Failed to call agent: {str(e)}"
    
    return "Please provide a data source URL. Example: 'Generate model from https://yourdata.com/file.csv'"

# Create Gradio interface
demo = gr.ChatInterface(
    chat_with_agent,
    title="🤖 PBI Semantic Modeling Agent",
    description="Chat with your Power BI semantic modeling agent",
    examples=[
        "Generate model from https://example.com/sales.csv",
        "Help me understand the agent capabilities"
    ]
)

if __name__ == "__main__":
    demo.launch()
```

Run: `python chat-ui.py`
Access: http://localhost:7860

---

## Option 3: GitHub Copilot Custom Agent (Advanced)

Create a GitHub Copilot Chat participant (requires Copilot subscription):

See: https://code.visualstudio.com/api/extension-guides/chat

---

## Option 4: Use AI Foundry Studio Chat

1. Go to: https://ai.azure.com
2. Open project: `pbi-semantic-agent-project`
3. Navigate to "Playground" or "Chat"
4. Configure to use custom endpoint
5. Chat with agent through web UI

---

## Best Option for You:

**Use AI Toolkit Extension** - It's already installed in your VS Code and supports custom agent endpoints!

Want me to create the Gradio chat UI or help you configure AI Toolkit?
