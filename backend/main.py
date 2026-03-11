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

# Global scraper instance
scraper: Optional[InstagramScraper] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    global scraper
    # Startup
    headless = os.getenv("HEADLESS", "false").lower() == "true"
    scraper = InstagramScraper(headless=headless)
    await scraper.start()
    print("✅ Scraper started")
    
    yield
    
    # Shutdown
    if scraper:
        await scraper.close()
    print("👋 Scraper stopped")


app = FastAPI(title="Instagram Crawler API", lifespan=lifespan)

# Serve static images
images_dir = Path("images")
images_dir.mkdir(exist_ok=True)
app.mount("/images", StaticFiles(directory="images"), name="images")

# CORS configuration
# Reads from CORS_ORIGINS env variable (comma-separated)
# Example: CORS_ORIGINS=http://localhost:5173,http://192.168.1.10:5173
cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    """Check if logged in Instagram"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    # Check only if session file exists
    has_session = scraper.session_file.exists()
    
    return {
        "logged_in": has_session,
        "message": "Session found" if has_session else "Login required"
    }


@app.post("/auth/wait-login")
async def wait_login():
    """Wait for manual login (blocking)"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    try:
        await scraper.wait_for_manual_login()
        return {"success": True, "message": "Login completed and session saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/scrape")
async def scrape_profile(request: ScrapeRequest):
    """
    Extract data from an Instagram profile
    
    - **username**: User @ (with or without @)
    - **max_followers**: Maximum number of followers to extract
    - **max_following**: Maximum number of following to extract
    - **get_followers**: Whether to extract followers list
    - **get_following**: Whether to extract following list
    """
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    # Check if saved session exists
    if not scraper.session_file.exists():
        raise HTTPException(
            status_code=401, 
            detail="Not logged in. Use /auth/wait-login first"
        )
    
    # Clear old images
    scraper.clear_images()
    
    try:
        # Extract profile data
        profile_data = await scraper.get_profile_data(request.username)
        
        # Extract followers if requested
        if request.get_followers:
            followers = await scraper.get_followers(
                request.username, 
                request.max_followers
            )
            profile_data['followers'] = followers
        
        # Extract following if requested
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
    """Clear all saved images"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    try:
        scraper.clear_images()
        return {"success": True, "message": "Images cleared"}
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
    """SSE version of scraping with real-time progress"""
    if not scraper:
        raise HTTPException(status_code=500, detail="Scraper not initialized")
    
    if not scraper.session_file.exists():
        raise HTTPException(status_code=401, detail="Not logged in")
    
    async def event_generator():
        try:
            # Clear images
            scraper.clear_images()
            yield f"event: progress\ndata: 🗑️ Clearing old images...\n\n"
            await asyncio.sleep(0.1)
            
            # Extract profile
            yield f"event: progress\ndata: 📋 Extracting profile data...\n\n"
            profile_data = await scraper.get_profile_data(username)
            yield f"event: progress\ndata: ✅ Profile extracted\n\n"
            await asyncio.sleep(0.1)
            
            # Extract followers with real-time progress
            if get_followers:
                yield f"event: progress\ndata: 👥 Starting followers extraction...\n\n"
                
                # Use approach with direct function modification
                followers_count = [0]  # List to allow modification in callback
                
                async def followers_callback(count):
                    followers_count[0] = count
                
                # Start extraction in background
                followers_task = asyncio.create_task(
                    scraper.get_followers(username, max_followers, followers_callback)
                )
                
                # While extracting, send updates
                last_count = 0
                while not followers_task.done():
                    await asyncio.sleep(1.5)
                    current = followers_count[0]
                    if current > last_count:
                        yield f"event: progress\ndata: 👥 Extracting followers... {current} extracted\n\n"
                        last_count = current
                
                # Get result
                followers = await followers_task
                profile_data['followers'] = followers
                yield f"event: progress\ndata: ✅ {len(followers)} followers extracted\n\n"
                await asyncio.sleep(0.1)
            
            # Extract following with real-time progress
            if get_following:
                yield f"event: progress\ndata: 👤 Starting following extraction...\n\n"
                
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
                        yield f"event: progress\ndata: 👤 Extracting following... {current} extracted\n\n"
                        last_count = current
                
                following = await following_task
                profile_data['following'] = following
                yield f"event: progress\ndata: ✅ {len(following)} following extracted\n\n"
                await asyncio.sleep(0.1)
            
            # Send complete data
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
