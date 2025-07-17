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

# MCP import - GERÇEK DATA İÇİN
try:
    from mevzuat_mcp_server import search_mevzuat, get_mevzuat_article_tree, get_mevzuat_article_content
    MCP_AVAILABLE = True
    print("✅ MCP Server başarıyla yüklendi - Gerçek data aktif")
except ImportError as e:
    print(f"❌ MCP Server yüklenemedi: {e}")
    MCP_AVAILABLE = False
    
    # Fallback fonksiyonlar (gerçek data bulunamadığında)
    async def search_mevzuat(mevzuat_adi: str = "", page_size: int = 10, **kwargs):
        return {
            "results": [
                {
                    "id": "fallback_1", 
                    "title": f"MCP bulunamadı - arama: {mevzuat_adi}",
                    "url": "https://mevzuat.gov.tr",
                    "type": "fallback"
                }
            ],
            "total_count": 1,
            "status": "fallback_mode"
        }
    
    async def get_mevzuat_article_tree(mevzuat_id: str):
        return [{"id": "fallback_tree", "title": "MCP bulunamadı"}]
    
    async def get_mevzuat_article_content(mevzuat_id: str, madde_id: str):
        return {"content": "MCP bulunamadı"}

# Request models
class SearchRequest(BaseModel):
    query: str
    page_size: int = 10
    mevzuat_turleri: list = []
    resmi_gazete_sayisi: str = ""
    search_in_title: bool = True

@app.get("/")
def root():
    return {
        "message": "Mevzuat MCP Server for n8n",
        "status": "online",
        "mcp_available": MCP_AVAILABLE,
        "mcp_status": "REAL_DATA" if MCP_AVAILABLE else "FALLBACK_MODE",
        "endpoints": {
            "search": "/search (GET)",
            "webhook_search": "/webhook/search (POST)",
            "article_tree": "/webhook/article-tree (POST)",
            "article_content": "/webhook/article-content (POST)"
        }
    }

@app.get("/search")
async def simple_search(q: str = "güncel mevzuat", page_size: int = 10):
    try:
        # Gerçek MCP fonksiyonunu çağır
        result = await search_mevzuat(
            mevzuat_adi=q,
            page_size=page_size,
            search_in_title=True
        )
        
        return {
            "success": True, 
            "data": result, 
            "mcp_available": MCP_AVAILABLE,
            "mode": "REAL_DATA" if MCP_AVAILABLE else "FALLBACK"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mcp_available": MCP_AVAILABLE
        }

@app.post("/webhook/search")
async def webhook_search(request: SearchRequest):
    try:
        # Gerçek MCP search fonksiyonunu çağır
        result = await search_mevzuat(
            mevzuat_adi=request.query,
            page_size=request.page_size,
            search_in_title=request.search_in_title,
            mevzuat_turleri=request.mevzuat_turleri or [],
            resmi_gazete_sayisi=request.resmi_gazete_sayisi or ""
        )
        
        return {
            "success": True,
            "data": result,
            "query": request.query,
            "mcp_available": MCP_AVAILABLE,
            "mode": "REAL_DATA" if MCP_AVAILABLE else "FALLBACK"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": request.query,
            "mcp_available": MCP_AVAILABLE
        }

@app.post("/webhook/article-tree")
async def webhook_article_tree(request: dict):
    try:
        result = await get_mevzuat_article_tree(request.get("mevzuat_id"))
        return {
            "success": True,
            "data": result,
            "mcp_available": MCP_AVAILABLE
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mcp_available": MCP_AVAILABLE
        }

@app.post("/webhook/article-content")
async def webhook_article_content(request: dict):
    try:
        result = await get_mevzuat_article_content(
            request.get("mevzuat_id"),
            request.get("madde_id")
        )
        return {
            "success": True,
            "data": result,
            "mcp_available": MCP_AVAILABLE
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mcp_available": MCP_AVAILABLE
        }

@app.get("/health")
def health():
    return {
        "status": "healthy", 
        "mcp": MCP_AVAILABLE,
        "mode": "REAL_DATA" if MCP_AVAILABLE else "FALLBACK"
    }

# GitHub Actions için özel endpoint
@app.get("/github-actions-test")
async def github_actions_test():
    """GitHub Actions için optimize edilmiş endpoint"""
    try:
        result = await search_mevzuat(
            mevzuat_adi="güncel mevzuat",
            page_size=20,
            search_in_title=True
        )
        
        return {
            "success": True,
            "data": result,
            "query": "güncel mevzuat",
            "timestamp": "2025-07-17",
            "source": "github_actions",
            "mcp_available": MCP_AVAILABLE
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mcp_available": MCP_AVAILABLE
        }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host="0.0.0.0", port=port)