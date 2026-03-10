from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
import asyncio
from scraper import InstagramScraper
import os
from dotenv import load_dotenv

load_dotenv()

# Instância global do scraper
scraper: Optional[InstagramScraper] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifecycle da aplicação"""
    global scraper
    # Startup
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    scraper = InstagramScraper(headless=headless)
    await scraper.start()
    print("✅ Scraper iniciado")
    
    yield
    
    # Shutdown
    if scraper:
        await scraper.close()
    print("👋 Scraper encerrado")


app = FastAPI(title="Instagram Crawler API", lifespan=lifespan)

# CORS para o Vue.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # URL do Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    username: str
    max_followers: int = 50
    max_following: int = 50
    get_followers: bool = True
    get_following: bool = True


@app.get("/")
async def root():
    """Health check"""
    return {"status": "ok", "message": "Instagram Crawler API"}


@app.get("/auth/status")
async def auth_status():
    """Verifica se está logado no Instagram"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper não inicializado")
    
    is_logged = await scraper.is_logged_in()
    return {
        "logged_in": is_logged,
        "message": "Logado com sucesso" if is_logged else "Login necessário"
    }


@app.post("/auth/wait-login")
async def wait_login():
    """Aguarda login manual (blocking)"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper não inicializado")
    
    try:
        await scraper.wait_for_manual_login()
        return {"success": True, "message": "Login realizado e sessão salva"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape")
async def scrape_profile(request: ScrapeRequest):
    """
    Extrai dados de um perfil do Instagram
    
    - **username**: @ do usuário (com ou sem @)
    - **max_followers**: Quantidade máxima de seguidores a extrair
    - **max_following**: Quantidade máxima de seguindo a extrair
    - **get_followers**: Se deve extrair lista de seguidores
    - **get_following**: Se deve extrair lista de seguindo
    """
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper não inicializado")
    
    # Verificar se está logado
    if not await scraper.is_logged_in():
        raise HTTPException(
            status_code=401, 
            detail="Não está logado. Use /auth/wait-login primeiro"
        )
    
    try:
        # Extrair dados do perfil
        profile_data = await scraper.get_profile_data(request.username)
        
        # Extrair seguidores se solicitado
        if request.get_followers:
            followers = await scraper.get_followers(
                request.username, 
                request.max_followers
            )
            profile_data['followers'] = followers
        
        # Extrair seguindo se solicitado
        if request.get_following:
            following = await scraper.get_following(
                request.username,
                request.max_following
            )
            profile_data['following'] = following
        
        return {
            "success": True,
            "data": profile_data
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
