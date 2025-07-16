from fastapi import FastAPI

app = FastAPI(title="Mevzuat MCP API Test", version="1.0.0")

@app.get("/")
def root():
    return {
        "message": "Mevzuat MCP API Working!", 
        "status": "online",
        "service": "mevzuat"
    }

@app.get("/search")  
def search():
    return {
        "result": "Mevzuat search test", 
        "data": ["Kanun 1", "Yönetmelik 2", "Tebliğ 3"],
        "count": 3
    }

@app.get("/health")
def health():
    return {"status": "healthy", "service": "mevzuat"}