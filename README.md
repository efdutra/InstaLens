# IGC - Instagram Crawler

Crawler automatizado para extrair dados de perfis do Instagram usando automação de browser com Playwright.

## 🛠️ Stack Tecnológica

### Backend

- **Python 3.13+**
- **FastAPI** - Framework web async
- **Playwright** - Automação de navegador (Chromium)
- **Pydantic** - Validação de dados
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend

- **Vue.js 3** - Framework progressivo
- **TypeScript** - Tipagem estática
- **Vite** - Build tool
- **Pinia** - Gerenciamento de estado
- **SASS/SCSS** - Estilização

## 📦 Funcionalidades

✅ Login manual com conta real do Instagram (sessão persistente)  
✅ Extração de dados do perfil (nome, username, bio, foto, contagens)  
✅ Lista de seguidores com foto e link  
✅ Lista de seguindo com foto e link  
✅ Interface web responsiva (mobile-first)  
✅ Tema escuro com cores teal/cyan

---

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.13 ou superior
- Node.js 18+ e pnpm
- Conta do Instagram (para login manual)

### Backend

1. **Navegue até o diretório do backend:**

```bash
cd backend
```

2. **Crie e ative o ambiente virtual:**

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências:**

```bash
pip install -r requirements.txt
playwright install chromium
```

4. **Configure o arquivo `.env`:**

```env
SESSION_FILE=session.json
HEADLESS=false
BROWSER_TYPE=chromium
```

5. **Inicie o servidor:**

```bash
uvicorn main:app --reload
```

O servidor estará rodando em: **http://localhost:8000**

### Frontend

1. **Navegue até o diretório do frontend:**

```bash
cd frontend
```

2. **Instale as dependências:**

```bash
pnpm install
```

3. **Inicie o servidor de desenvolvimento:**

```bash
pnpm dev
```

A interface estará disponível em: **http://localhost:5173**

---

## 📡 API - Rotas Disponíveis

### `GET /`

**Descrição:** Health check da API  
**Resposta:**

```json
{
  "message": "Instagram Crawler API",
  "status": "ok"
}
```

### `GET /auth/status`

**Descrição:** Verifica se o usuário está logado no Instagram  
**Resposta:**

```json
{
  "logged_in": true
}
```

### `POST /auth/wait-login`

**Descrição:** Abre o navegador e aguarda login manual (timeout: 5 minutos)  
**Resposta:**

```json
{
  "success": true,
  "message": "Login detectado com sucesso!"
}
```

### `POST /scrape`

**Descrição:** Extrai dados do perfil especificado  
**Body:**

```json
{
  "username": "motorizandomemorias",
  "max_followers": 50,
  "max_following": 50,
  "get_followers": true,
  "get_following": true
}
```

**Resposta:**

```json
{
  "profile": {
    "username": "motorizandomemorias",
    "name": "Eduardo",
    "bio": "Descrição do perfil",
    "profile_pic": "https://...",
    "posts_count": 123,
    "followers_count": 456,
    "following_count": 789
  },
  "followers": [
    {
      "username": "user123",
      "name": "Nome do Usuário",
      "profile_url": "https://instagram.com/user123",
      "profile_pic": "https://..."
    }
  ],
  "following": [...]
}
```

---

## 📂 Estrutura do Projeto

```
IGC/
├── backend/
│   ├── main.py           # FastAPI server + rotas
│   ├── scraper.py        # Lógica do scraper com Playwright
│   ├── requirements.txt  # Dependências Python
│   ├── .env              # Configurações
│   └── session.json      # Sessão persistente do Instagram
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   └── HomePage.vue
│   │   ├── styles/
│   │   │   ├── _variables.scss
│   │   │   └── main.scss
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## 🔑 Fluxo de Login

1. Execute `POST /auth/wait-login` via API ou interface
2. O navegador Chromium será aberto automaticamente
3. Faça login manualmente no Instagram
4. Aguarde até a detecção automática do login (máx. 5 minutos)
5. As credenciais são salvas em `session.json`
6. Nos próximos usos, o login será automático

---

## ⚠️ Aviso Legal

**Projeto educacional para fins de aprendizado.**

- Este projeto foi criado para estudar web scraping e automação de navegadores
- O uso de automação no Instagram pode violar os Termos de Serviço da plataforma
- Use por sua conta e risco
- Não nos responsabilizamos por banimentos ou restrições de conta

---

## 📝 Licença

Projeto educacional de código aberto.
