# IGC - Instagram Crawler

Crawler automatizado para extrair dados de perfis do Instagram usando automação de browser com Playwright.

## ✨ Funcionalidades

### 🔐 Autenticação

- ✅ Login manual com conta real do Instagram
- ✅ Sessão persistente (salva em `session.json`)
- ✅ Detecção automática de sessão expirada
- ✅ Browser visível apenas no primeiro login
- ✅ Modo headless (invisível) para scraping
- ✅ Indicador visual de status de autenticação

### 📊 Extração de Dados

- ✅ Dados do perfil (nome, username, bio, foto, contagens)
- ✅ Lista de seguidores com foto e link
- ✅ Lista de seguindo com foto e link
- ✅ Download local de imagens (resolve CORS)
- ✅ Suporte a "extrair todos" (campo vazio)
- ✅ Limite customizável por tipo de lista

### 🎨 Interface

- ✅ Interface web responsiva (mobile-first)
- ✅ Tema escuro com cores teal/cyan (#2dd4bf/#38bdf8)
- ✅ Progresso em tempo real via Server-Sent Events (SSE)
- ✅ Busca/filtro instantâneo nos resultados
- ✅ Exportação de dados em CSV
- ✅ Tabs para alternar entre seguidores/seguindo
- ✅ Contador dinâmico com filtros

---

## 🛠️ Stack Tecnológica

### Backend

- **Python 3.13+**
- **FastAPI** - Framework web async com lifespan context
- **Playwright** - Automação de navegador (Chromium)
- **httpx** - Cliente HTTP async para download de imagens
- **Pydantic** - Validação de dados
- **python-dotenv** - Gerenciamento de variáveis de ambiente

### Frontend

- **Vue.js 3** - Framework progressivo com Composition API
- **TypeScript** - Tipagem estática
- **Vite** - Build tool ultra-rápido
- **Pinia** - Gerenciamento de estado
- **SASS/SCSS** - Estilização com módulos e mixins
- **EventSource** - SSE para progresso em tempo real

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
python main.py
# ou
uvicorn main:app --host 0.0.0.0 --port 8000
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

4. **Build para produção:**

```bash
pnpm build
pnpm preview  # Preview da build
```

---

## 📡 API - Rotas Disponíveis

### `GET /`

**Descrição:** Health check da API  
**Resposta:**

```json
{
  "status": "ok",
  "message": "Instagram Crawler API"
}
```

### `GET /auth/status`

**Descrição:** Verifica se existe sessão salva  
**Resposta:**

```json
{
  "logged_in": true,
  "message": "Sessão encontrada"
}
```

### `POST /auth/wait-login`

**Descrição:** Abre navegador visível e aguarda login manual (timeout: 5 minutos)  
**Comportamento:**

- Abre Chromium visível para login
- Detecta login automaticamente
- Salva sessão em `session.json`
- **Fecha o navegador** após salvar sessão

**Resposta:**

```json
{
  "success": true,
  "message": "Login realizado e sessão salva"
}
```

### `GET /scrape-stream`

**Descrição:** Extrai dados com progresso em tempo real via SSE  
**Query Params:**

- `username` (required): Instagram username
- `get_followers` (bool): Extrair seguidores (default: true)
- `get_following` (bool): Extrair seguindo (default: true)
- `max_followers` (int?): Limite de seguidores (vazio = todos)
- `max_following` (int?): Limite de seguindo (vazio = todos)

**Eventos SSE:**

```
event: progress
data: 🗑️ Limpando imagens antigas...

event: progress
data: 📊 Extraindo dados do perfil...

event: progress
data: 👥 Extraindo seguidores... 15 extraídos

event: complete
data: {"success": true, "data": {...}}

event: failure
data: {"detail": "Erro X"}
```

### `POST /scrape` (Legacy)

**Descrição:** Extrai dados sem progresso em tempo real  
**Body:**

```json
{
  "username": "instagram",
  "max_followers": 50,
  "max_following": 50,
  "get_followers": true,
  "get_following": true
}
```

**Resposta:**

```json
{
  "success": true,
  "data": {
    "username": "instagram",
    "name": "Instagram",
    "bio": "Bio do perfil",
    "profile_pic": "/images/abc123.jpg",
    "posts_count": 123,
    "followers_count": 456000,
    "following_count": 789,
    "followers": [...],
    "following": [...]
  }
}
```

### `POST /clear-images`

**Descrição:** Remove todas as imagens baixadas do servidor  
**Resposta:**

```json
{
  "success": true,
  "message": "Imagens limpas"
}
```

### `GET /images/{filename}`

**Descrição:** Serve imagens estáticas baixadas localmente  
**Exemplo:** `http://localhost:8000/images/abc123def456.jpg`

---

## 📂 Estrutura do Projeto

```
IGC/
├── backend/
│   ├── main.py              # FastAPI server + rotas + SSE
│   ├── scraper.py           # Lógica do scraper com Playwright
│   ├── requirements.txt     # Dependências Python
│   ├── .env                 # Configurações (gitignored)
│   ├── session.json         # Sessão persistente (gitignored)
│   └── images/              # Imagens baixadas localmente
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HomePage.vue        # Componente principal
│   │   │   ├── ProfileCard.vue     # Card do perfil
│   │   │   ├── UserList.vue        # Lista de usuários
│   │   │   └── LoadingSpinner.vue  # Spinner com mensagem
│   │   ├── stores/
│   │   │   └── instagram.ts        # Pinia store (state + actions)
│   │   ├── styles/
│   │   │   ├── _variables.scss     # Variáveis SASS + mixins
│   │   │   └── main.scss           # Estilos globais
│   │   ├── types/
│   │   │   └── instagram.ts        # TypeScript interfaces
│   │   ├── App.vue
│   │   └── main.ts
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
│
└── README.md
```

---

## 🔄 Fluxos da Aplicação

### 1️⃣ Fluxo de Autenticação (Primeira Vez)

```
[USUÁRIO] → Acessa frontend
    ↓
[FRONTEND] → Verifica auth: GET /auth/status → logged_in: false
    ↓
[USUÁRIO] → Clica em "Fazer Login"
    ↓
[FRONTEND] → POST /auth/wait-login
    ↓
[BACKEND] → Abre Chromium VISÍVEL
    ↓
[USUÁRIO] → Faz login manualmente no Instagram
    ↓
[BACKEND] → Detecta login (polling a cada 2s)
    ↓
[BACKEND] → Salva session.json
    ↓
[BACKEND] → FECHA Chromium
    ↓
[FRONTEND] → Atualiza status: "Sessão ativa ✅"
```

### 2️⃣ Fluxo de Scraping

```
[USUÁRIO] → Preenche username + opções
    ↓
[USUÁRIO] → Clica "Buscar Perfil"
    ↓
[FRONTEND] → EventSource: GET /scrape-stream?username=X&...
    ↓
[BACKEND] → Verifica session.json existe
    ↓
[BACKEND] → Abre Chromium HEADLESS (invisível)
    ↓
[BACKEND] → Navega para Instagram com sessão
    ↓
[BACKEND] → SSE: "📊 Extraindo dados do perfil..."
    ↓
[BACKEND] → Extrai dados do perfil
    ↓
[BACKEND] → SSE: "✅ Perfil extraído"
    ↓
[BACKEND] → SSE: "👥 Extraindo seguidores... 8 extraídos"
    ↓
[BACKEND] → Scroll + extração (atualiza contador em tempo real)
    ↓
[BACKEND] → SSE: "✅ 23 seguidores extraídos"
    ↓
[BACKEND] → SSE: "👤 Extraindo seguindo... 12 extraídos"
    ↓
[BACKEND] → SSE: "✅ 18 seguindo extraídos"
    ↓
[BACKEND] → SSE: event:complete com dados JSON
    ↓
[FRONTEND] → Exibe resultados + busca + export
```

### 3️⃣ Modo Headless Híbrido

O navegador tem comportamento inteligente:

**Primeira Inicialização:**

- ❌ Não tem `session.json` → Browser **NÃO abre**
- ✅ Aguarda comando `/auth/wait-login` → Abre **VISÍVEL**

**Após Login:**

- ✅ Salva `session.json`
- 🚪 Fecha browser completamente

**Próximas Scraping:**

- ✅ Detecta `session.json` existe
- 👻 Abre browser **HEADLESS** (invisível)
- ⚡ Scraping acontece em background

**Se Sessão Expirar:**

- 🔍 Detecta redirecionamento para `/accounts/login`
- 🗑️ Deleta `session.json` automaticamente
- ⚠️ Retorna erro: "Sessão expirada. Faça login novamente"

---

## 🎨 Features da Interface

### Busca/Filtro em Tempo Real

- Digite no campo de busca
- Filtra instantaneamente por **username** OU **nome**
- Contador atualiza: `"Seguidores 8/45"` (8 encontrados de 45 totais)
- Case-insensitive
- Botão "✕" para limpar

### Exportação CSV

- Botão "📥 Exportar CSV"
- Gera arquivo: `instagram_USERNAME_DATA.csv`
- Formato estruturado:

  ```csv
  === PERFIL ===
  Campo,Valor
  Username,instagram
  Nome,Instagram
  ...

  === SEGUIDORES ===
  Username,Nome,URL
  user1,Nome1,https://...
  ...

  === SEGUINDO ===
  Username,Nome,URL
  user2,Nome2,https://...
  ```

### Progresso em Tempo Real

- Mensagens dinâmicas no LoadingSpinner
- Atualiza conforme backend envia eventos SSE:
  - 🗑️ Limpando imagens antigas...
  - 📊 Extraindo dados do perfil...
  - ✅ Perfil extraído
  - 👥 Extraindo seguidores... 15 extraídos
  - ✅ 23 seguidores extraídos

### Indicador de Autenticação

- Card visual antes do formulário
- ✅ Verde: "Sessão ativa no Instagram"
- 🔓 Destaque: "Você precisa fazer login" + botão

---

## ⚙️ Configurações Avançadas

### Backend (.env)

```env
# Arquivo de sessão (não alterar)
SESSION_FILE=session.json

# Tipo de navegador (chromium, firefox, webkit)
BROWSER_TYPE=chromium

# HEADLESS é ignorado - modo híbrido automático
HEADLESS=false
```

### Frontend (vite.config.ts)

Para produção, altere a `API_BASE_URL` em `stores/instagram.ts`:

```typescript
const API_BASE_URL = import.meta.env.PROD
  ? "https://seu-servidor.com:8000" // Produção
  : "http://localhost:8000"; // Desenvolvimento
```

### Deploy em Servidor

**Backend:**

```bash
# Instalar dependências sistema (Ubuntu/Debian)
sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libgbm1 libasound2

# Xvfb para headless (opcional)
sudo apt-get install -y xvfb
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &

# Rodar backend
python main.py
```

**Frontend:**

```bash
# Build
pnpm build

# Servir com nginx ou serve
npx serve -s dist -p 5173
```

**⚠️ Importante para Mobile:**

- Backend no servidor precisa liberar CORS para IP/domínio do frontend
- Frontend precisa apontar `API_BASE_URL` para IP/domínio do servidor
- Liberar portas 8000 (backend) no firewall
- Chromium roda **NO SERVIDOR**, não no celular
- Celular acessa apenas a interface web Vue.js

---

## 🔒 Segurança

- ✅ Sessão salva **localmente** em `session.json` (não enviada ao frontend)
- ✅ Imagens baixadas localmente (evita expor URLs do Instagram)
- ✅ CORS configurado apenas para `localhost:5173` (ajuste para produção)
- ⚠️ **NÃO** commitar `session.json` no git
- ⚠️ **NÃO** commitar `.env` no git
- ⚠️ Use HTTPS em produção

---

## 🚨 Troubleshooting

### Erro: "Sessão expirada"

**Causa:** Instagram invalidou a sessão salva em `session.json`

**Solução:**

```bash
cd backend
rm session.json
# Fazer login novamente via interface
```

### Erro: "playwright install"

**Causa:** Chromium não instalado

**Solução:**

```bash
cd backend
python -m playwright install chromium
```

### Imagens não carregam

**Causa:** Backend não está rodando ou CORS bloqueado

**Verificar:**

```bash
# Testar endpoint de imagens
curl http://localhost:8000/images/
# Verificar logs do backend para erros CORS
```

### Frontend não conecta ao backend

**Causa:** Porta 8000 não acessível

**Verificar:**

```bash
# Testar saúde do backend
curl http://localhost:8000/
# Resposta esperada: {"status": "ok"}
```

### Scraping trava em "Extraindo..."

**Causa:** Instagram mudou estrutura da página

**Debug:**

```bash
# Rodar backend com logs
cd backend
python main.py
# Observar logs de erros no terminal
```

### Timeout no SSE

**Causa:** Conexão SSE pode timeout em conexões lentas

**Solução:**

- Recarregar a página e tentar novamente
- Verificar estabilidade da conexão internet
- Aumentar timeout no código se necessário

---

## 🔮 Possíveis Melhorias Futuras

- [ ] **Estatísticas avançadas:** seguidores mútuos, não seguindo de volta
- [ ] **Histórico de buscas:** salvar pesquisas anteriores com data/hora
- [ ] **Comparação de perfis:** comparar dois perfis lado a lado
- [ ] **Agendamento:** scrapar perfil periodicamente (cron jobs)
- [ ] **Notificações:** alertar quando alguém deixa de seguir
- [ ] **Gráficos:** visualizar crescimento de followers ao longo do tempo
- [ ] **Mais formatos de export:** JSON, Excel, PDF
- [ ] **Dark/Light mode toggle:** alternar entre temas claro/escuro
- [ ] **Paginação:** carregar usuários sob demanda (virtual scroll)
- [ ] **Animações:** toast notifications, skeleton loading, transições
- [ ] **Rate limiting:** respeitar limites do Instagram automaticamente
- [ ] **Docker:** containerização completa com docker-compose
- [ ] **Testes:** testes unitários e de integração

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Se encontrar bugs ou tiver sugestões:

1. Abra uma **issue** descrevendo o problema/sugestão
2. Faça um **fork** do projeto
3. Crie uma **branch** para sua feature:
   ```bash
   git checkout -b feature/nova-feature
   ```
4. **Commit** suas mudanças:
   ```bash
   git commit -m 'Adiciona nova feature incrível'
   ```
5. **Push** para a branch:
   ```bash
   git push origin feature/nova-feature
   ```
6. Abra um **Pull Request** detalhado

**Diretrizes para contribuições:**

- Código limpo e bem comentado
- Seguir padrões TypeScript/Python existentes
- Testar antes de submeter PR
- Documentar novas features no README

---

## 👤 Autor

Desenvolvido com ❤️ por **Eduardo**

---

## ⭐ Agradecimentos

Bibliotecas e ferramentas que tornaram este projeto possível:

- **[Playwright](https://playwright.dev/)** - Automação de navegador poderosa e confiável
- **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido para Python
- **[Vue.js 3](https://vuejs.org/)** - Framework frontend progressivo com Composition API
- **[Pinia](https://pinia.vuejs.org/)** - State management intuitivo para Vue
- **[Vite](https://vitejs.dev/)** - Build tool extremamente rápida
- **[TypeScript](https://www.typescriptlang.org/)** - JavaScript com tipos estáticos
- **[SASS](https://sass-lang.com/)** - CSS com superpoderes
- **[Httpx](https://www.python-httpx.org/)** - Cliente HTTP assíncrono para Python

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

---

<div align="center">

**🎉 Projeto completo e pronto para uso!**

Se este projeto foi útil para você, considere dar uma ⭐ no repositório!

Para dúvidas, sugestões ou problemas, abra uma **[issue](../../issues)** no repositório.

---

**Made with ❤️ and ☕ by Eduardo**

</div>
