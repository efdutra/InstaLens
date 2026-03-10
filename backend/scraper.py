import asyncio
import json
import os
import re
import hashlib
import httpx
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional, Dict, List


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
        
    async def _download_image(self, url: str) -> Optional[str]:
        """Baixa imagem e salva localmente, retorna o caminho relativo"""
        if not url:
            return None
            
        try:
            # Gerar hash único para a imagem
            url_hash = hashlib.md5(url.encode()).hexdigest()
            filename = f"{url_hash}.jpg"
            filepath = self.images_dir / filename
            
            # Se já existe, retorna o caminho
            if filepath.exists():
                return f"/images/{filename}"
            
            # Baixar imagem
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    filepath.write_bytes(response.content)
                    return f"/images/{filename}"
                else:
                    print(f"❌ Erro ao baixar imagem: {response.status_code}")
                    return None
        except Exception as e:
            print(f"❌ Erro ao baixar imagem: {e}")
            return None
    
    def clear_images(self):
        """Limpa todas as imagens salvas"""
        try:
            for file in self.images_dir.glob("*.jpg"):
                file.unlink()
            print("🗑️ Imagens limpas")
        except Exception as e:
            print(f"❌ Erro ao limpar imagens: {e}")
        
    async def _ensure_browser_started(self, headless: bool = False):
        """Garante que o navegador está aberto (lazy loading)"""
        if self.browser:
            return  # Já está rodando
        
        if not self.playwright:
            self.playwright = await async_playwright().start()
        
        mode = "invisível (headless)" if headless else "visível"
        print(f"🌐 Abrindo navegador {mode}...")
        
        self.browser = await self.playwright.chromium.launch(headless=headless)
        
        # Criar contexto com ou sem sessão
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
        """Apenas inicializa (não abre navegador)"""
        print("✅ InstagramScraper inicializado")
        if self.session_file.exists():
            print("🔒 Sessão encontrada - navegador abrirá em modo invisível quando necessário")
        else:
            print("👁️ Sem sessão salva - navegador abrirá visível para login")
        
    async def close(self):
        """Fecha o browser"""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
    async def is_logged_in(self) -> bool:
        """Verifica se está logado"""
        try:
            # Verificar se não está na página de login
            current_url = self.page.url
            if '/accounts/login' in current_url:
                return False
            
            # Verificar se tem elementos que só aparecem quando logado
            selectors = [
                'a[href="/"]',
                'svg[aria-label="Página inicial"]',
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
        """Aguarda login manual do usuário - abre visível e FECHA após salvar"""
        # Abrir navegador VISÍVEL para login
        await self._ensure_browser_started(headless=False)
        
        print("\n🔐 Por favor, faça login manualmente na janela do browser...")
        print("⏳ Aguardando login...")
        
        login_detected = False
        max_attempts = 150  # 150 * 2s = 5 min
        
        for _ in range(max_attempts):
            if await self.is_logged_in():
                login_detected = True
                break
            await asyncio.sleep(2)
        
        if not login_detected:
            raise Exception("Timeout: Login não detectado após 5 minutos")
        
        print("✅ Login detectado! Salvando sessão...")
        
        # Salvar cookies
        storage_state = await self.context.storage_state()
        with open(self.session_file, 'w') as f:
            json.dump(storage_state, f)
        
        print(f"💾 Sessão salva em {self.session_file}")
        
        # FECHAR navegador completamente após login
        print("🚪 Fechando navegador...")
        await self.browser.close()
        self.browser = None
        self.context = None
        self.page = None
        print("✅ Login concluído - navegador fechado")
    
    async def get_profile_data(self, username: str) -> Dict:
        """Extrai dados do perfil"""
        # Abrir navegador HEADLESS (invisível) para scraping
        await self._ensure_browser_started(headless=True)
        
        username = username.replace('@', '')
        
        await self.page.goto(f"https://www.instagram.com/{username}/")
        await asyncio.sleep(5)
        
        # Verificar se foi redirecionado para login (sessão inválida)
        if '/accounts/login' in self.page.url:
            print("⚠️ Sessão expirada! Deletando session.json...")
            if self.session_file.exists():
                self.session_file.unlink()
            raise Exception(
                "Sessão expirada. Por favor, faça login novamente usando /auth/wait-login"
            )
        
        try:
            await self.page.wait_for_selector('header', timeout=10000)
        except:
            raise Exception(f"Perfil @{username} não encontrado")
        
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
            # Nome
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
            
            # Foto de perfil
            pic_selectors = ['header img', 'main header img']
            for selector in pic_selectors:
                pic_elem = await self.page.query_selector(selector)
                if pic_elem:
                    src = await pic_elem.get_attribute('src')
                    if src and 'profile' in src:
                        # Baixar imagem localmente
                        local_path = await self._download_image(src)
                        data["profile_pic"] = local_path if local_path else src
                        break
            
            # Contadores - extrair do texto do header
            header_text = await self.page.inner_text('header')
            lines = [line.strip() for line in header_text.split('\n') if line.strip()]
            
            for line in lines:
                line_lower = line.lower()
                if 'post' in line_lower and not data["posts_count"]:
                    data["posts_count"] = self._extract_number(line)
                elif 'seguidor' in line_lower and not data["followers_count"]:
                    data["followers_count"] = self._extract_number(line)
                elif 'seguindo' in line_lower and not data["following_count"]:
                    data["following_count"] = self._extract_number(line)
            
            # Bio - linhas que não são stats
            bio_lines = []
            skip_keywords = ['post', 'seguidor', 'seguindo', username.lower()]
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
            print(f"⚠️ Erro ao extrair dados: {e}")
        
        return data
    
    async def get_followers(self, username: str, max_followers: int = 100, progress_callback=None) -> List[Dict]:
        """Extrai lista de seguidores"""
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
            print(f"❌ Erro ao abrir lista de seguidores: {e}")
            return []
        
        followers = await self._scroll_and_extract_users(max_followers, progress_callback)
        return followers
    
    async def get_following(self, username: str, max_following: int = 100, progress_callback=None) -> List[Dict]:
        """Extrai lista de seguindo"""
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
            print(f"❌ Erro ao abrir lista de seguindo: {e}")
            return []
        
        following = await self._scroll_and_extract_users(max_following, progress_callback)
        return following
    
    async def _scroll_and_extract_users(self, max_users: int, progress_callback=None) -> List[Dict]:
        """Scroll infinito e extração de usuários"""
        users = []
        seen_usernames = set()
        
        await asyncio.sleep(3)  # Esperar modal abrir completamente
        
        # Tentar encontrar o modal/dialog
        modal = await self.page.query_selector('div[role="dialog"]')
        if not modal:
            print("❌ Modal não encontrado")
            return []
        
        print(f"📜 Iniciando scroll para carregar usuários...")
        
        previous_count = 0
        no_change_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 200
        
        while len(users) < max_users and scroll_attempts < max_scroll_attempts:
            scroll_attempts += 1
            
            # Múltiplas tentativas de seletores para encontrar usuários
            user_elements = []
            
            # Tentar diferentes seletores
            selectors = [
                'a[href^="/"][role="link"]',  # Links de perfil
                'a[href^="/"]',  # Qualquer link começando com /
                'div[role="dialog"] a',  # Todos os links no dialog
            ]
            
            for selector in selectors:
                user_elements = await modal.query_selector_all(selector)
                if user_elements:
                    break
            
            if not user_elements:
                print(f"⚠️ Nenhum elemento encontrado. Tentativa {scroll_attempts}")
                await asyncio.sleep(2)
                continue
            
            for elem in user_elements:
                try:
                    href = await elem.get_attribute('href')
                    if not href:
                        continue
                    
                    # Filtrar links inválidos
                    if any(x in href for x in ['/explore/', '/p/', '/reel/', '/tv/', '/accounts/']):
                        continue
                    
                    if href == '/' or href == '/direct/':
                        continue
                    
                    # Extrair username
                    parts = [p for p in href.strip('/').split('/') if p]
                    if not parts:
                        continue
                    
                    username = parts[0]
                    
                    # Validar username
                    if username in seen_usernames or len(username) < 2:
                        continue
                    
                    # Verificar se é um username válido (sem caracteres especiais estranhos)
                    if not re.match(r'^[a-zA-Z0-9._]+$', username):
                        continue
                    
                    seen_usernames.add(username)
                    
                    # Tentar pegar imagem e nome
                    img = await elem.query_selector('img')
                    profile_pic = ""
                    name = ""
                    
                    if img:
                        profile_pic = await img.get_attribute('src') or ""
                        name = await img.get_attribute('alt') or ""
                        # Limpar texto do alt
                        name = name.replace('Foto do perfil de', '').replace('Photo by', '').strip()
                        
                        # Baixar imagem localmente
                        if profile_pic:
                            local_path = await self._download_image(profile_pic)
                            profile_pic = local_path if local_path else profile_pic
                    
                    if not name:
                        name = username
                    
                    users.append({
                        "username": username,
                        "name": name,
                        "profile_pic": profile_pic,
                        "profile_url": f"https://www.instagram.com/{username}/"
                    })
                    
                    if len(users) >= max_users:
                        break
                        
                except Exception as e:
                    continue
            
            # Verificar progresso
            if len(users) == previous_count:
                no_change_count += 1
                if no_change_count >= 5:
                    print(f"   Não há mais usuários para carregar.")
                    break
            else:
                no_change_count = 0
                print(f"   Carregados: {len(users)} usuários...")
                # Callback de progresso
                if progress_callback:
                    await progress_callback(len(users))
                previous_count = len(users)
            
            if len(users) >= max_users:
                break
            
            # Scroll no modal - tentar múltiplas estratégias
            try:
                scrolled = await modal.evaluate('''
                    (element) => {
                        // Estratégia 1: Buscar divs dentro do dialog que tem overflow
                        let scrollableDivs = Array.from(element.querySelectorAll('div')).filter(div => {
                            const style = window.getComputedStyle(div);
                            return (style.overflowY === 'auto' || 
                                   style.overflowY === 'scroll' || 
                                   style.overflow === 'auto' ||
                                   style.overflow === 'scroll');
                        });
                        
                        // Se achou divs scrollable, pegar o primeiro com scrollHeight > clientHeight
                        for (let div of scrollableDivs) {
                            if (div.scrollHeight > div.clientHeight) {
                                const before = div.scrollTop;
                                div.scrollBy(0, 1000);  // Scroll 1000px para baixo
                                return div.scrollTop > before;  // Retorna true se scrollou
                            }
                        }
                        
                        // Estratégia 2: Scroll no dialog inteiro
                        const before = element.scrollTop;
                        element.scrollBy(0, 1000);
                        return element.scrollTop > before;
                    }
                ''')
                
                if scrolled:
                    print(f"   🔄 Scrollando...")
                else:
                    print(f"   ⚠️ Scroll não funcionou, tentando novamente...")
                
                await asyncio.sleep(2.5)
            except Exception as e:
                print(f"⚠️ Erro no scroll: {e}")
                break
        
        print(f"✅ Total extraído: {len(users)} usuários")
        return users[:max_users]
    
    def _extract_number(self, text: str) -> int:
        """Extrai número de texto"""
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
            print("✅ Já está logado!")
        
        username = input("\n📝 Digite o @ do usuário (ex: instagram): ").strip()
        
        print(f"\n🔍 Buscando dados de @{username}...")
        profile_data = await scraper.get_profile_data(username)
        
        print(f"\n👤 Perfil: {profile_data['name']}")
        print(f"📝 Bio: {profile_data['bio'][:50]}..." if profile_data['bio'] else "📝 Bio: (sem bio)")
        print(f"📸 Posts: {profile_data['posts_count']}")
        print(f"👥 Seguidores: {profile_data['followers_count']}")
        print(f"➡️ Seguindo: {profile_data['following_count']}")
        
        if input("\n❓ Extrair seguidores? (s/n): ").lower() == 's':
            max_input = input("Quantos? (Vazio = todos): ").strip()
            max_followers = int(max_input) if max_input else 999999
            followers = await scraper.get_followers(username, max_followers)
            profile_data['followers'] = followers
            print(f"✅ {len(followers)} seguidores extraídos")
        
        if input("\n❓ Extrair seguindo? (s/n): ").lower() == 's':
            max_input = input("Quantos? (Vazio = todos): ").strip()
            max_following = int(max_input) if max_input else 999999
            following = await scraper.get_following(username, max_following)
            profile_data['following'] = following
            print(f"✅ {len(following)} seguindo extraídos")
        
        output_file = f"{username}_data.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Dados salvos em {output_file}")
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
    finally:
        await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
