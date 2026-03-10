from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from contextlib import asynccontextmanager
from pathlib import Path
import asyncio
import httpx
import json
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

# Servir imagens estáticas
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

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
    
    # Verificar apenas se existe arquivo de sessão
    has_session = scraper.session_file.exists()
    
    return {
        "logged_in": has_session,
        "message": "Sessão encontrada" if has_session else "Login necessário"
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
    
    # Verificar se tem sessão salva
    if not scraper.session_file.exists():
        raise HTTPException(
            status_code=401, 
            detail="Não está logado. Use /auth/wait-login primeiro"
        )
    
    # Limpar imagens antigas
    scraper.clear_images()
    
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


@app.post("/clear-images")
async def clear_images():
    """Limpa todas as imagens salvas"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper não inicializado")
    
    try:
        scraper.clear_images()
        return {"success": True, "message": "Imagens limpas"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/scrape-stream")
async def scrape_stream(
    username: str,
    get_followers: bool = True,
    get_following: bool = True,
    max_followers: Optional[int] = None,
    max_following: Optional[int] = None
):
    """Versão SSE do scraping com progresso em tempo real"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper não inicializado")
    
    if not scraper.session_file.exists():
        raise HTTPException(status_code=401, detail="Não está logado")
    
    async def event_generator():
        try:
            # Limpar imagens
            scraper.clear_images()
            yield f"event: progress\ndata: 🗑️ Limpando imagens antigas...\n\n"
            await asyncio.sleep(0.1)
            
            # Extrair perfil
            yield f"event: progress\ndata: 📊 Extraindo dados do perfil...\n\n"
            profile_data = await scraper.get_profile_data(username)
            yield f"event: progress\ndata: ✅ Perfil extraído\n\n"
            await asyncio.sleep(0.1)
            
            # Extrair seguidores com progresso em tempo real
            if get_followers:
                yield f"event: progress\ndata: 👥 Iniciando extração de seguidores...\n\n"
                
                # Usar abordagem com modificação direta da função
                followers_count = [0]  # Lista para permitir modificação no callback
                
                async def followers_callback(count):
                    followers_count[0] = count
                
                # Iniciar extração em background
                followers_task = asyncio.create_task(
                    scraper.get_followers(username, max_followers, followers_callback)
                )
                
                # Enquanto extrai, enviar atualizações
                last_count = 0
                while not followers_task.done():
                    await asyncio.sleep(1.5)
                    current = followers_count[0]
                    if current > last_count:
                        yield f"event: progress\ndata: 👥 Extraindo seguidores... {current} extraídos\n\n"
                        last_count = current
                
                # Pegar resultado
                followers = await followers_task
                profile_data['followers'] = followers
                yield f"event: progress\ndata: ✅ {len(followers)} seguidores extraídos\n\n"
                await asyncio.sleep(0.1)
            
            # Extrair seguindo com progresso em tempo real
            if get_following:
                yield f"event: progress\ndata: 👤 Iniciando extração de seguindo...\n\n"
                
                following_count = [0]
                
                async def following_callback(count):
                    following_count[0] = count
                
                following_task = asyncio.create_task(
                    scraper.get_following(username, max_following, following_callback)
                )
                
                last_count = 0
                while not following_task.done():
                    await asyncio.sleep(1.5)
                    current = following_count[0]
                    if current > last_count:
                        yield f"event: progress\ndata: 👤 Extraindo seguindo... {current} extraídos\n\n"
                        last_count = current
                
                following = await following_task
                profile_data['following'] = following
                yield f"event: progress\ndata: ✅ {len(following)} seguindo extraídos\n\n"
                await asyncio.sleep(0.1)
            
            # Enviar dados completos
            yield f"event: complete\ndata: {json.dumps({'success': True, 'data': profile_data})}\n\n"
            
        except Exception as e:
            error_msg = json.dumps({"detail": str(e)})
            yield f"event: failure\ndata: {error_msg}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
