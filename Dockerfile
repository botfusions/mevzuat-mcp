# mevzuat-mcp Dockerfile
FROM python:3.11-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Sistem paketlerini güncelle
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Proje dosyalarını kopyala
COPY . .

# Python bağımlılıklarını kur
RUN pip install --upgrade pip
RUN pip install fastmcp httpx beautifulsoup4 markitdown pydantic aiohttp

# Port'u aç
EXPOSE 8000

# Sağlık kontrolü
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/mcp || exit 1

# MCP sunucusunu başlat
CMD ["python", "-m", "fastmcp", "run", "--host", "0.0.0.0", "--port", "8000", "mcp_server_main.py"]
