from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import os

app = FastAPI(title="Mevzuat MCP Server for n8n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP import güvenli hale getir
try:
    from mevzuat_mcp_server import search_mevzuat, get_mevzuat_article_tree, get_mevzuat_article_content
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    
    async def search_mevzuat(**kwargs):
        return {
            "results": [
                {"id": "test1", "title": "Test İş Kanunu", "url": "test1.html"},
                {"id": "test2", "title": "Test Borçlar Kanunu", "url": "test2.html"}
            ],
            "total_count": 2
        }
    
    async def get_mevzuat_article_tree(mevzuat_id: str):
        return [{"id": "art1", "title": "Test Madde 1"}]
    
    async def get_mevzuat_article_content(mevzuat_id: str, madde_id: str):
        return {"content": "Test madde içeriği"}

# Request models
class SearchRequest(BaseModel):
    query: str
    page_size: int = 10

@app.get("/")
def root():
    return {
        "message": "Mevzuat MCP Server for n8n",
        "status": "online",
        "mcp_available": MCP_AVAILABLE,
        "endpoints": {
            "search": "/search (GET)",
            "webhook_search": "/webhook/search (POST)",
            "sse": "/sse",
            "mcp": "/mcp"
        }
    }

@app.get("/search")
async def simple_search(q: str = "test"):
    result = await search_mevzuat(mevzuat_adi=q, page_size=5)
    return {"success": True, "data": result, "mcp_available": MCP_AVAILABLE}

@app.post("/webhook/search")
async def webhook_search(request: SearchRequest):
    result = await search_mevzuat(mevzuat_adi=request.query, page_size=request.page_size)
    return {"success": True, "data": result, "query": request.query}

@app.get("/health")
def health():
    return {"status": "healthy", "mcp": MCP_AVAILABLE}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)