import asyncio
import json
import os
import re
import hashlib
import httpx
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional, Dict, List, Tuple


class InstagramScraper:
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.context = None
        self.session_file = Path("session.json")
        self.images_dir = Path("images")
        self.images_dir.mkdir(exist_ok=True)
        
        # Load name caches for gender classification
        self.names_male = {}
        self.names_female = {}
        self._load_names_cache()
        
        # Load name caches for gender classification
        self.names_male = {}
        self.names_female = {}
        self._load_names_cache()
    
    def _load_names_cache(self):
        """Load IBGE name caches"""
        try:
            male_file = Path("names_cache_male.json")
            female_file = Path("names_cache_female.json")
            
            if male_file.exists():
                with open(male_file, 'r', encoding='utf-8') as f:
                    self.names_male = json.load(f)
                print(f"✅ {len(self.names_male)} male names loaded")
            else:
                print("⚠️ Male names cache not found")
            
            if female_file.exists():
                with open(female_file, 'r', encoding='utf-8') as f:
                    self.names_female = json.load(f)
                print(f"✅ {len(self.names_female)} female names loaded")
            else:
                print("⚠️ Female names cache not found")
        except Exception as e:
            print(f"❌ Error loading names caches: {e}")
    
    def classify_gender(self, full_name: str) -> str:
        """Classify gender based on first name
        
        Args:
            full_name: User's full name
            
        Returns:
            'M' for male, 'F' for female, 'I' for undetermined
        """
        if not full_name:
            return 'I'
        
        # Get first name and normalize
        first_name = full_name.split()[0].lower().strip()
        
        # Check full name in caches
        if first_name in self.names_male:
            return 'M'
        elif first_name in self.names_female:
            return 'F'
        
        # If not found, try prefixes (for cases like "caiomini" -> "caio")
        # Test prefixes from 4 to 8 characters
        if len(first_name) > 4:
            for length in range(min(8, len(first_name)), 3, -1):
                prefix = first_name[:length]
                if prefix in self.names_male:
                    return 'M'
                elif prefix in self.names_female:
                    return 'F'
        
        return 'I'
        
    async def _download_image(self, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Download image and save locally, returns (local_path, original_url)"""
        if not url:
            return None
            
        try:
            # Generate unique hash for image
            url_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{url_hash}.jpg"
            filepath = self.images_dir / filename
            
            # If already exists, return path
            if filepath.exists():
                return (f"/images/{filename}", url)
            
            # Download image
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    filepath.write_bytes(response.content)
                    return (f"/images/{filename}", url)
                else:
                    print(f"❌ Error downloading image: {response.status_code}")
                    return (None, url)
        except Exception as e:
            print(f"❌ Error downloading image: {e}")
            return (None, url)
    
    def clear_images(self):
        """Clears all saved images"""
        try:
            for file in self.images_dir.glob("*.jpg"):
                file.unlink()
            print("🗑️ Images cleared")
        except Exception as e:
            print(f"❌ Error clearing images: {e}")
        
    async def _ensure_browser_started(self, headless: bool = False):
        """Ensures browser is open (lazy loading)"""
        if self.browser:
            return  # Already running
        
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        mode = "invisible (headless)" if headless else "visible"
        print(f"🌐 Opening browser {mode}...")
        
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        # Create context with or without session
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                storage_state = json.load(f)
            self.context = await self.browser.new_context(storage_state=storage_state)
        else:
            self.context = await self.browser.new_context()
        
        self.page = await self.context.new_page()
        await self.page.goto("https://www.instagram.com/")
        await asyncio.sleep(3)
    
    async def start(self):
        """Just initializes (doesn't open browser)"""
        print("✅ InstagramScraper initialized")
        if self.session_file.exists():
            print("🔒 Session found - browser will open in invisible mode when needed")
        else:
            print("👁️ No saved session - browser will open visible for login")
        
    async def close(self):
        """Close browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
    async def is_logged_in(self) -> bool:
        """Check if logged in"""
        try:
            # Check if not on login page
            current_url = self.page.url
            if '/accounts/login' in current_url:
                return False
            
            # Check if has elements that only appear when logged in
            selectors = [
                'a[href="/"]',
                'svg[aria-label="Home"]',
                'svg[aria-label="Home"]',
                'a[href*="/direct/"]',
                'div[role="menubar"]',
            ]
            
            for selector in selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    return True
                except:
                    continue
            
            return False
        except:
            return False
    
    async def wait_for_manual_login(self):
        """Wait for user manual login - opens visible and CLOSES after saving"""
        # Open VISIBLE browser for login
        await self._ensure_browser_started(headless=False)
        
        print("\n🔐 Please login manually in the browser window...")
        print("⏳ Waiting for login...")
        
        login_detected = False
        max_attempts = 150  # 150 * 2s = 5 min
        
        for _ in range(max_attempts):
            if await self.is_logged_in():
                login_detected = True
                break
            await asyncio.sleep(2)
        
        if not login_detected:
            raise Exception("Timeout: Login not detected after 5 minutes")
        
        print("✅ Login detected! Saving session...")
        
        # Save cookies
        storage_state = await self.context.storage_state()
        with open(self.session_file, 'w') as f:
            json.dump(storage_state, f)
        
        print(f"💾 Session saved in {self.session_file}")
        
        # CLOSE browser completely after login
        print("🚪 Closing browser...")
        await self.browser.close()
        self.browser = None
        self.context = None
        self.page = None
        print("✅ Login completed - browser closed")
    
    async def get_profile_data(self, username: str) -> Dict:
        """Extract profile data"""
        # Open browser HEADLESS (invisible) for scraping
        await self._ensure_browser_started(headless=True)
        
        username = username.replace('@', '')
        
        await self.page.goto(f"https://www.instagram.com/{username}/")
        await asyncio.sleep(5)
        
        # Check if redirected to login (invalid session)
        if '/accounts/login' in self.page.url:
            print("⚠️ Session expired! Deleting session.json...")
            if self.session_file.exists():
                self.session_file.unlink()
            raise Exception(
                "Session expired. Please login again using /auth/wait-login"
            )
        
        try:
            await self.page.wait_for_selector('header', timeout=10000)
        except:
            raise Exception(f"Profile @{username} not found")
        
        data = {
            "username": username,
            "name": "",
            "bio": "",
            "profile_pic": "",
            "posts_count": 0,
            "followers_count": 0,
            "following_count": 0,
            "followers": [],
            "following": []
        }
        
        try:
            # Name
            name_selectors = [
                'header section h1',
                'header section h2',
                'header h1',
                'main header h1',
                'main header h2'
            ]
            for selector in name_selectors:
                name_elem = await self.page.query_selector(selector)
                if name_elem:
                    text = await name_elem.inner_text()
                    if text and text.strip() and text != username:
                        data["name"] = text.strip()
                        break
            
            if not data["name"]:
                data["name"] = username
            
            # Profile picture
            pic_selectors = ['header img', 'main header img']
            for selector in pic_selectors:
                pic_elem = await self.page.query_selector(selector)
                if pic_elem:
                    src = await pic_elem.get_attribute('src')
                    if src and 'profile' in src:
                        # Download image locally
                        local_path, original_url = await self._download_image(src)
                        data["profile_pic"] = local_path if local_path else src
                        data["profile_pic_url"] = original_url
                        break
            
            # Counters - extract from header text
            header_text = await self.page.inner_text('header')
            lines = [line.strip() for line in header_text.split('\n') if line.strip()]
            
            for line in lines:
                line_lower = line.lower()
                if 'post' in line_lower and not data["posts_count"]:
                    data["posts_count"] = self._extract_number(line)
                elif 'seguidor' in line_lower and not data["followers_count"]:  # Portuguese: "seguidores"
                    data["followers_count"] = self._extract_number(line)
                elif 'seguindo' in line_lower and not data["following_count"]:  # Portuguese: "seguindo"
                    data["following_count"] = self._extract_number(line)
            
            # Bio - lines that are not stats
            bio_lines = []
            skip_keywords = ['post', 'seguidor', 'seguindo', username.lower()]  # Portuguese keywords from Instagram UI
            for line in lines:
                line_clean = line.lower()
                if any(kw in line_clean for kw in skip_keywords):
                    continue
                if line.replace(',', '').replace('.', '').isdigit():
                    continue
                if len(line) > 10 and line != data["name"]:
                    bio_lines.append(line)
            
            if bio_lines:
                data["bio"] = '\n'.join(bio_lines[:3])
                
        except Exception as e:
            print(f"⚠️ Error extracting data: {e}")
        
        return data
    
    async def get_followers(self, username: str, max_followers: Optional[int] = None, progress_callback=None) -> List[Dict]:
        """Extract followers list"""
        username = username.replace('@', '')
        await self.page.goto(f"https://www.instagram.com/{username}/")
        await asyncio.sleep(2)
        
        try:
            followers_btn = await self.page.query_selector('a[href*="/followers/"]')
            if not followers_btn:
                followers_btn = await self.page.query_selector('header section ul li:nth-child(2) a')
            
            await followers_btn.click()
            await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ Error opening followers list: {e}")
            return []
        
        followers = await self._scroll_and_extract_users(max_followers, progress_callback)
        return followers
    
    async def get_following(self, username: str, max_following: Optional[int] = None, progress_callback=None) -> List[Dict]:
        """Extract following list"""
        username = username.replace('@', '')
        await self.page.goto(f"https://www.instagram.com/{username}/")
        await asyncio.sleep(2)
        
        try:
            following_btn = await self.page.query_selector('a[href*="/following/"]')
            if not following_btn:
                following_btn = await self.page.query_selector('header section ul li:nth-child(3) a')
            
            await following_btn.click()
            await asyncio.sleep(3)
        except Exception as e:
            print(f"❌ Error opening following list: {e}")
            return []
        
        following = await self._scroll_and_extract_users(max_following, progress_callback)
        return following
    
    async def _scroll_and_extract_users(self, max_users: Optional[int], progress_callback=None) -> List[Dict]:
        """Infinite scroll and user extraction"""
        users = []
        seen_usernames = set()
        
        await asyncio.sleep(3)  # Wait for modal to fully open
        
        # Try to find modal/dialog
        modal = await self.page.query_selector('div[role="dialog"]')
        if not modal:
            print("❌ Modal not found")
            return []
        
        # If max_users is None, set high value for "extract all"
        if max_users is None:
            max_users = 999999
            print(f"💡 'Extract all' mode activated")
        else:
            print(f"💡 Maximum limit: {max_users} users")
        
        print(f"📜 Starting scroll to load users...")
        
        previous_count = 0
        no_change_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 200
        
        while len(users) < max_users and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Multiple selector attempts to find users
            user_elements = []
            
            # Try different selectors
            selectors = [
                'a[href^="/"][role="link"]',  # Profile links
                'a[href^="/"]',  # Any link starting with /
                'div[role="dialog"] a',  # All links in dialog
            ]
            
            for selector in selectors:
                user_elements = await modal.query_selector_all(selector)
                if user_elements:
                    break
            
            if not user_elements:
                print(f"⚠️ No elements found. Attempt {scroll_attempts}")
                await asyncio.sleep(2)
                continue
            
            for elem in user_elements:
                try:
                    href = await elem.get_attribute('href')
                    if not href:
                        continue
                    
                    # Filter invalid links
                    if any(x in href for x in ['/explore/', '/p/', '/reel/', '/tv/', '/accounts/']):
                        continue
                    
                    if href == '/' or href == '/direct/':
                        continue
                    
                    # Extract username
                    parts = [p for p in href.strip('/').split('/') if p]
                    if not parts:
                        continue
                    
                    username = parts[0]
                    
                    # Validate username
                    if username in seen_usernames or len(username) < 2:
                        continue
                    
                    # Check if is a valid username (no strange special characters)
                    if not re.match(r'^[a-zA-Z0-9._]+$', username):
                        continue
                    
                    seen_usernames.add(username)
                    
                    # Try to get image and name
                    img = await elem.query_selector('img')
                    profile_pic = ""
                    name = ""
                    
                    if img:
                        profile_pic_url = await img.get_attribute('src') or ""
                        name = await img.get_attribute('alt') or ""
                        
                        # Clean alt text (Portuguese and English)
                        name = name.replace('Foto do perfil de', '').strip()
                        name = name.replace('Photo by', '').strip()
                        name = name.replace("'s profile picture", '').strip()
                        name = name.replace('profile picture', '').strip()
                        
                        # If resulting name is empty or too short, use username
                        if not name or len(name) < 2:
                            name = username
                        
                        # If name still looks like username (has _, numbers), try to extract name
                        if '_' in name or any(char.isdigit() for char in name):
                            # Try to get first part before numbers/underscores
                            parts = re.split(r'[_\d]', name)
                            first_part = parts[0] if parts and len(parts[0]) > 1 else name
                            if len(first_part) > 1:
                                name = first_part
                        
                        # Download image locally
                        profile_pic = profile_pic_url
                        if profile_pic_url:
                            local_path, original_url = await self._download_image(profile_pic_url)
                            profile_pic = local_path if local_path else profile_pic_url
                            profile_pic_url = original_url
                    
                    if not name:
                        name = username
                    
                    # Classify gender
                    gender = self.classify_gender(name)
                    
                    users.append({
                        "username": username,
                        "name": name,
                        "profile_pic": profile_pic,
                        "profile_pic_url": profile_pic_url,
                        "profile_url": f"https://www.instagram.com/{username}/",
                        "gender": gender
                    })
                    
                    if len(users) >= max_users:
                        break
                        
                except Exception as e:
                    continue
            
            # Check progress
            if len(users) == previous_count:
                no_change_count += 1
                if no_change_count >= 5:
                    print(f"   No more users to load.")
                    break
            else:
                no_change_count = 0
                print(f"   Loaded: {len(users)} users...")
                # Progress callback
                if progress_callback:
                    await progress_callback(len(users))
                previous_count = len(users)
            
            if len(users) >= max_users:
                break
            
            # Scroll in modal - try multiple strategies
            try:
                scrolled = await modal.evaluate('''
                    (element) => {
                        // Strategy 1: Find divs inside dialog that have overflow
                        let scrollableDivs = Array.from(element.querySelectorAll('div')).filter(div => {
                            const style = window.getComputedStyle(div);
                            return (style.overflowY === 'auto' || 
                                   style.overflowY === 'scroll' || 
                                   style.overflow === 'auto' ||
                                   style.overflow === 'scroll');
                        });
                        
                        // If found scrollable divs, get first one with scrollHeight > clientHeight
                        for (let div of scrollableDivs) {
                            if (div.scrollHeight > div.clientHeight) {
                                const before = div.scrollTop;
                                div.scrollBy(0, 1000);  // Scroll 1000px down
                                return div.scrollTop > before;  // Return true if scrolled
                            }
                        }
                        
                        // Strategy 2: Scroll in entire dialog
                        const before = element.scrollTop;
                        element.scrollBy(0, 1000);
                        return element.scrollTop > before;
                    }
                ''')
                
                if scrolled:
                    print(f"   🔄 Scrolling...")
                else:
                    print(f"   ⚠️ Scroll didn't work, trying again...")
                
                await asyncio.sleep(2.5)
            except Exception as e:
                print(f"⚠️ Error scrolling: {e}")
                break
        
        print(f"✅ Total extracted: {len(users)} users")
        return users[:max_users]
    
    def _extract_number(self, text: str) -> int:
        """Extract number from text"""
        numbers = re.findall(r'[\d.,]+', text)
        if numbers:
            num_str = numbers[0].replace('.', '').replace(',', '')
            try:
                return int(num_str)
            except:
                return 0
        return 0
    

# Teste standalone
async def main():
    scraper = InstagramScraper(headless=False)
    
    try:
        await scraper.start()
        
        if not await scraper.is_logged_in():
            await scraper.wait_for_manual_login()
        else:
            print("✅ Already logged in!")
        
        username = input("\n📝 Enter user @ (ex: instagram): ").strip()
        
        print(f"\n🔍 Searching data for @{username}...")
        profile_data = await scraper.get_profile_data(username)
        
        print(f"\n👤 Profile: {profile_data['name']}")
        print(f"📝 Bio: {profile_data['bio'][:50]}..." if profile_data['bio'] else "📝 Bio: (no bio)")
        print(f"📸 Posts: {profile_data['posts_count']}")
        print(f"👥 Followers: {profile_data['followers_count']}")
        print(f"➡️ Following: {profile_data['following_count']}")
        
        if input("\n❓ Extract followers? (y/n): ").lower() == 'y':
            max_input = input("How many? (Empty = all): ").strip()
            max_followers = int(max_input) if max_input else 999999
            followers = await scraper.get_followers(username, max_followers)
            profile_data['followers'] = followers
            print(f"✅ {len(followers)} followers extracted")
        
        if input("\n❓ Extract following? (y/n): ").lower() == 'y':
            max_input = input("How many? (Empty = all): ").strip()
            max_following = int(max_input) if max_input else 999999
            following = await scraper.get_following(username, max_following)
            profile_data['following'] = following
            print(f"✅ {len(following)} following extracted")
        
        output_file = f"{username}_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Data saved in {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
