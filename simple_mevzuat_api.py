from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
from typing import Dict, Any
import os

# MCP server'ı import et
from mevzuat_mcp_server import server

app = FastAPI(title="Mevzuat MCP Server for n8n")

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# SSE connection store
connections: Dict[str, Any] = {}

@app.get("/")
async def root():
    return {
        "message": "Mevzuat MCP Server for n8n",
        "status": "online",
        "endpoints": {
            "sse": "/sse",
            "mcp": "/mcp"
        }
    }

@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for n8n MCP Client Tool"""
    
    async def event_generator():
        # MCP server capabilities
        capabilities = {
            "protocol": "mcp",
            "version": "1.0",
            "tools": [
                {
                    "name": "search_mevzuat",
                    "description": "Search Turkish legislation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_adi": {"type": "string"},
                            "mevzuat_no": {"type": "string"},
                            "page_size": {"type": "integer", "default": 10},
                            "page_number": {"type": "integer", "default": 1}
                        }
                    }
                },
                {
                    "name": "get_mevzuat_article_tree",
                    "description": "Get article tree structure",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_id": {"type": "string"}
                        },
                        "required": ["mevzuat_id"]
                    }
                },
                {
                    "name": "get_mevzuat_article_content",
                    "description": "Get article content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "mevzuat_id": {"type": "string"},
                            "madde_id": {"type": "string"}
                        },
                        "required": ["mevzuat_id", "madde_id"]
                    }
                }
            ]
        }
        
        # Send capabilities
        yield f"data: {json.dumps(capabilities)}\n\n"
        
        # Keep connection alive
        while True:
            await asyncio.sleep(30)
            yield f"data: {json.dumps({'type': 'ping'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """MCP protocol endpoint"""
    try:
        data = await request.json()
        
        # Handle MCP protocol messages
        if data.get("method") == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "result": {
                    "tools": [
                        {
                            "name": "search_mevzuat",
                            "description": "Search Turkish legislation",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "mevzuat_adi": {"type": "string"},
                                    "mevzuat_no": {"type": "string"},
                                    "page_size": {"type": "integer", "default": 10}
                                }
                            }
                        },
                        {
                            "name": "get_mevzuat_article_tree",
                            "description": "Get article tree structure",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "mevzuat_id": {"type": "string"}
                                },
                                "required": ["mevzuat_id"]
                            }
                        },
                        {
                            "name": "get_mevzuat_article_content",
                            "description": "Get article content",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "mevzuat_id": {"type": "string"},
                                    "madde_id": {"type": "string"}
                                },
                                "required": ["mevzuat_id", "madde_id"]
                            }
                        }
                    ]
                }
            }
        
        elif data.get("method") == "tools/call":
            # Handle tool calls
            tool_name = data.get("params", {}).get("name")
            arguments = data.get("params", {}).get("arguments", {})
            
            if tool_name == "search_mevzuat":
                from mevzuat_mcp_server import search_mevzuat
                result = await search_mevzuat(**arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False)
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_mevzuat_article_tree":
                from mevzuat_mcp_server import get_mevzuat_article_tree
                result = await get_mevzuat_article_tree(**arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False)
                            }
                        ]
                    }
                }
            
            elif tool_name == "get_mevzuat_article_content":
                from mevzuat_mcp_server import get_mevzuat_article_content
                result = await get_mevzuat_article_content(**arguments)
                
                return {
                    "jsonrpc": "2.0",
                    "id": data.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False)
                            }
                        ]
                    }
                }
        
        return {
            "jsonrpc": "2.0",
            "id": data.get("id"),
            "error": {"code": -32601, "message": "Method not found"}
        }
        
    except Exception as e:
        return {
            "jsonrpc": "2.0",
            "id": data.get("id", 1),
            "error": {"code": -32603, "message": str(e)}
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)