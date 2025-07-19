from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import asyncio
import os
import sys

app = FastAPI(title="Mevzuat MCP Server for n8n")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP import - GÜVENLI YAKLAŞIM
MCP_AVAILABLE = False
search_mevzuat = None
get_mevzuat_article_tree = None
get_mevzuat_article_content = None

try:
    print("🔄 MCP Server import deneniyor...")
    sys.path.append('.')
    sys.path.append('/app')
    
    # Farklı import yöntemlerini dene
    try:
        from mevzuat_mcp_server import search_mevzuat, get_mevzuat_article_tree, get_mevzuat_article_content
        print("✅ Method 1: Direct import başarılı")
    except ImportError:
        print("❌ Method 1: Direct import başarısız, Method 2 deneniyor...")
        import mevzuat_mcp_server
        search_mevzuat = mevzuat_mcp_server.search_mevzuat
        get_mevzuat_article_tree = mevzuat_mcp_server.get_mevzuat_article_tree
        get_mevzuat_article_content = mevzuat_mcp_server.get_mevzuat_article_content
        print("✅ Method 2: Module import başarılı")
    
    # Test fonksiyonları
    if callable(search_mevzuat):
        MCP_AVAILABLE = True
        print("✅ MCP Server başarıyla yüklendi - GERÇEK DATA AKTIF")
    else:
        raise Exception("search_mevzuat fonksiyonu callable değil")
        
except ImportError as e:
    print(f"❌ MCP Server import hatası: {e}")
    print("🔄 Fallback mode aktif")
    MCP_AVAILABLE = False
except Exception as e:
    print(f"❌ MCP Server genel hatası: {e}")
    print("🔄 Fallback mode aktif")
    MCP_AVAILABLE = False

# Fallback fonksiyonları (MCP bulunamadığında)
if not MCP_AVAILABLE:
    print("🔄 Fallback fonksiyonları yükleniyor...")
    
    async def search_mevzuat(mevzuat_adi: str = "", page_size: int = 10, **kwargs):
        # Biraz daha gerçekçi fallback data
        return {
            "results": [
                {
                    "id": "fallback_001", 
                    "title": f"[FALLBACK] {mevzuat_adi} - 4857 Sayılı İş Kanunu",
                    "url": "https://mevzuat.gov.tr/MevzuatMetin/1.5.4857.pdf",
                    "type": "kanun",
                    "status": "fallback_mode"
                },
                {
                    "id": "fallback_002",
                    "title": f"[FALLBACK] {mevzuat_adi} - 6098 Sayılı Türk Borçlar Kanunu", 
                    "url": "https://mevzuat.gov.tr/MevzuatMetin/1.5.6098.pdf",
                    "type": "kanun",
                    "status": "fallback_mode"
                }
            ],
            "total_count": 2,
            "status": "fallback_mode",
            "note": "MCP server bulunamadı - fallback data"
        }
    
    async def get_mevzuat_article_tree(mevzuat_id: str):
        return [
            {"id": "fallback_tree_1", "title": "Fallback - Birinci Bölüm"},
            {"id": "fallback_tree_2", "title": "Fallback - İkinci Bölüm"}
        ]
    
    async def get_mevzuat_article_content(mevzuat_id: str, madde_id: str):
        return {
            "content": f"Fallback content for mevzuat_id: {mevzuat_id}, madde_id: {madde_id}",
            "status": "fallback_mode"
        }

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
        "system_info": {
            "python_path": sys.path[:3],  # İlk 3 path'i göster
            "current_dir": os.getcwd(),
            "files_in_dir": os.listdir(".") if os.path.exists(".") else []
        },
        "endpoints": {
            "search": "/search (GET)",
            "webhook_search": "/webhook/search (POST)",
            "article_tree": "/webhook/article-tree (POST)",
            "article_content": "/webhook/article-content (POST)",
            "debug": "/debug (GET)"
        }
    }

@app.get("/debug")
def debug_info():
    """Debug endpoint - MCP durumunu detaylı göster"""
    try:
        import importlib.util
        mcp_spec = importlib.util.find_spec("mevzuat_mcp_server")
        mcp_file_exists = os.path.exists("mevzuat_mcp_server.py")
        
        return {
            "mcp_available": MCP_AVAILABLE,
            "mcp_spec_found": mcp_spec is not None,
            "mcp_file_exists": mcp_file_exists,
            "current_directory": os.getcwd(),
            "directory_contents": os.listdir("."),
            "python_version": sys.version,
            "sys_path": sys.path,
            "search_function_type": str(type(search_mevzuat)),
            "search_function_callable": callable(search_mevzuat)
        }
    except Exception as e:
        return {"debug_error": str(e)}

@app.get("/search")
async def simple_search(q: str = "güncel mevzuat", page_size: int = 10):
    try:
        # MCP fonksiyonunu çağır
        result = await search_mevzuat(
            mevzuat_adi=q,
            page_size=page_size,
            search_in_title=True
        )
        
        return {
            "success": True, 
            "data": result, 
            "mcp_available": MCP_AVAILABLE,
            "mode": "REAL_DATA" if MCP_AVAILABLE else "FALLBACK",
            "query": q
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "mcp_available": MCP_AVAILABLE,
            "query": q
        }

@app.post("/webhook/search")
async def webhook_search(request: SearchRequest):
    try:
        # MCP search fonksiyonunu çağır
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
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)