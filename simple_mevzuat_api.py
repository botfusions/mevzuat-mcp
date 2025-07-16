from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import sys
import os

# MCP sunucu fonksiyonlarını import et
try:
    from mevzuat_mcp_server import search_mevzuat, get_mevzuat_article_tree, get_mevzuat_article_content
except ImportError:
    # Fallback function if MCP server not available
    async def search_mevzuat(**kwargs):
        return {"error": "MCP server not available"}
    
    async def get_mevzuat_article_tree(mevzuat_id: str):
        return {"error": "MCP server not available"}
    
    async def get_mevzuat_article_content(mevzuat_id: str, madde_id: str):
        return {"error": "MCP server not available"}

app = FastAPI(title="Mevzuat MCP API", version="1.0.0")

# Request modelleri
class SearchRequest(BaseModel):
    query: str
    mevzuat_adi: str = ""
    mevzuat_no: str = ""
    page_size: int = 10
    page_number: int = 1

class ArticleTreeRequest(BaseModel):
    mevzuat_id: str

class ArticleContentRequest(BaseModel):
    mevzuat_id: str
    madde_id: str  # Parametre adını düzelttik

# Ana endpoint
@app.get("/")
def root():
    return {
        "message": "Mevzuat MCP API Working!",
        "status": "online",
        "service": "mevzuat",
        "endpoints": {
            "search": "/webhook/search (POST)",
            "article_tree": "/webhook/article-tree (POST)", 
            "article_content": "/webhook/article-content (POST)",
            "health": "/health (GET)"
        }
    }

# n8n webhook endpoint'leri
@app.post("/webhook/search")
async def webhook_search(request: SearchRequest):
    try:
        # MCP search fonksiyonunu çağır - gerçek parametreler
        result = await search_mevzuat(
            mevzuat_adi=request.mevzuat_adi or request.query,
            mevzuat_no=request.mevzuat_no,
            page_size=request.page_size,
            page_number=request.page_number,
            search_in_title=True,
            sort_field="tarih",
            sort_direction="desc"
        )
        
        return {
            "success": True,
            "data": result,
            "query": request.query
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": request.query
        }

@app.post("/webhook/article-tree")
async def webhook_article_tree(request: ArticleTreeRequest):
    try:
        result = await get_mevzuat_article_tree(mevzuat_id=request.mevzuat_id)
        
        return {
            "success": True,
            "data": result,
            "mevzuat_id": request.mevzuat_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mevzuat_id": request.mevzuat_id
        }

@app.post("/webhook/article-content")
async def webhook_article_content(request: ArticleContentRequest):
    try:
        result = await get_mevzuat_article_content(
            mevzuat_id=request.mevzuat_id,
            madde_id=request.madde_id  # Parametre adını düzelttik
        )
        
        return {
            "success": True,
            "data": result,
            "mevzuat_id": request.mevzuat_id,
            "madde_id": request.madde_id
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mevzuat_id": request.mevzuat_id
        }

# Eski test endpoint'leri (geriye uyumluluk için)
@app.get("/search")
def search_test():
    return {
        "message": "Test endpoint - POST /webhook/search kullanın",
        "example": {
            "method": "POST",
            "url": "/webhook/search",
            "body": {"query": "iş kanunu"}
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "mevzuat"}

# Sunucu başlatma
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8001))  # Render PORT veya 8001
    uvicorn.run(app, host="0.0.0.0", port=port)