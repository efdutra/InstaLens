# 📸 InstaLens

**Instagram Followers Scraper** - Complete system for extracting Instagram profile data with followers/following information and gender classification.

> **Self-Hosted Tool:** This is a local application. Clone the repository and run it on your own machine. Each user manages their own Instagram session privately.

---

## ⚠️ AUTHENTICATION REQUIREMENTS

### **IMPORTANT:** Login is MANDATORY

- You **MUST** log in with a **real Instagram account**
- The browser opens **on the machine where the backend is running** for manual authentication
- Session is saved locally in `session.json` for reuse

### Private vs Public Accounts

**🔒 Private Accounts:**

- You **MUST follow the target account** before scraping
- Without following, Instagram blocks access to followers/following data

**🌐 Public Accounts:**

- No need to follow the target account
- You can scrape directly

### How It Works

1. **First time:** Browser opens in **visible mode** on the backend machine for manual login
2. **After login:** Session saved → browser closes
3. **Future scrapes:** Browser runs in **headless mode** (background)
4. **Network access:** Once logged in, you can access the web interface from any device on your network
5. **If session expires:** Login again (browser will open on the backend machine)

---

## ✨ Features

- ✅ Manual authentication with real Instagram account
- ✅ Persistent session (saved in `session.json`)
- ✅ Auto-detection of expired sessions
- ✅ Profile data extraction (name, username, bio, photo, stats)
- ✅ Followers and following lists with photos
- ✅ Local image downloads (solves CORS issues)
- ✅ Real-time progress via Server-Sent Events (SSE)
- ✅ Gender classification using IBGE database (134k+ Brazilian names)
- ✅ Gender-based filtering (Male/Female/Undetermined)
- ✅ Search/filter by username or name
- ✅ Export to CSV and JSON with stats breakdown
- ✅ Responsive web interface (mobile-first)
- ✅ Dark theme with teal/cyan accent colors

---

## 📋 ToDo

- [ ] **Docker deployment:** Add Dockerfile and docker-compose.yml for easy deployment
- [ ] **Fix auto-scrolling limitation:** Currently stops around 800 followers/following (retries 5 times). Need to investigate Instagram's rate limiting and implement better handling.
- [ ] **Mutual followers analysis:** Show who follows back, who doesn't follow back, mutual connections
- [ ] **Profile comparison:** Compare two profiles side-by-side (mutual followers, unique followers)
- [ ] **Scraping history:** Save past searches with timestamps to track follower growth over time
- [ ] **Excel export:** Add .xlsx format alongside CSV/JSON
- [ ] **Charts & visualizations:** Gender distribution pie chart, follower growth timeline
- [ ] **Light/Dark theme toggle:** Currently only dark theme available
- [ ] **Virtual scroll/pagination:** Better performance for lists with 1000+ users
- [ ] **Batch scraping:** Queue multiple usernames for sequential processing

---

## 🛠️ Tech Stack

**Backend:**

- Python 3.13+ | FastAPI | Playwright (Chromium automation)
- httpx (async HTTP) | Pydantic (validation)

**Frontend:**

- Vue.js 3 (Composition API) | TypeScript
- Pinia (state management) | Vite (build tool)

**Data:**

- IBGE Names API (134,315 Brazilian names for gender classification)

---

## ⚡ Quick Install (One-Liner)

### Linux / macOS

```bash
curl -sSL https://raw.githubusercontent.com/efdutra/InstaLens/main/install.sh | bash
```

### Windows (PowerShell)

```powershell
iex (iwr -useb https://raw.githubusercontent.com/efdutra/InstaLens/main/install.ps1)
```

The installer will:

- ✅ Check for dependencies (Git, Python 3.9+, Node 18+, pnpm)
- ✅ Clone the repository to your chosen location
- ✅ Install all backend and frontend dependencies
- ✅ Launch both servers automatically
- ✅ Display a beautiful status banner when ready

**After installation completes**, access the app at `http://localhost:5173`

**Manual Installation:** If you prefer step-by-step setup, see below ⬇️

---

## 🚀 Manual Setup

### Prerequisites

- Python 3.13+
- Node.js 20+ / pnpm 9+
- 2GB+ free disk space

### Backend Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python -m playwright install chromium
python main.py
```

Backend runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend runs on `http://localhost:5173`

### First Use

1. Access `http://localhost:5173`
2. Click "Login"
3. Browser opens → log in to Instagram manually
4. After login detected → browser closes → session saved
5. Enter a username and start scraping

### Mobile/Network Access

To access from your phone or other devices on the same network:

1. **Find your PC's IP address:**

   ```bash
   # Windows
   ipconfig | Select-String "IPv4"
   # Linux/Mac
   ifconfig | grep "inet "
   ```

2. **Access from mobile:** `http://YOUR_PC_IP:5173`
   - Example: `http://192.168.1.10:5173`

3. **Configure CORS** (if needed):
   - Edit `backend/.env`
   - Set `CORS_ORIGINS=*` for all devices (development only)
   - Or whitelist specific IPs: `CORS_ORIGINS=http://localhost:5173,http://192.168.1.10:5173`

**Note:** The backend automatically detects which IP you're using and connects accordingly.

---

## 📡 API Overview

| Method | Endpoint             | Description                              |
| ------ | -------------------- | ---------------------------------------- |
| GET    | `/`                  | Health check                             |
| GET    | `/auth/status`       | Check if logged in                       |
| POST   | `/auth/wait-login`   | Open browser for manual login            |
| GET    | `/scrape-stream`     | Extract data with real-time SSE progress |
| POST   | `/scrape`            | Legacy JSON endpoint                     |
| POST   | `/clear-images`      | Delete cached images                     |
| GET    | `/images/{filename}` | Serve downloaded images                  |

### Example: Scraping with SSE

```bash
curl -N "http://localhost:8000/scrape-stream?username=instagram&max_followers=50&max_following=50"
```

Real-time events:

```
event: message
data: "Clearing old images..."

event: message
data: "Extracting profile data..."

event: complete
data: {"profile": {...}, "followers": [...], "following": [...]}
```

---

## 📂 Project Structure

```
InstaLens/
├── backend/
│   ├── main.py              # FastAPI routes
│   ├── scraper.py           # Playwright scraper + gender classification
│   ├── download_names.py    # IBGE names downloader
│   ├── requirements.txt
│   └── session.json         # Instagram session (auto-created)
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── HomePage.vue       # Main interface
│   │   │   └── ProfileCard.vue    # Profile display
│   │   ├── stores/
│   │   │   └── instagram.ts       # Pinia store with SSE logic
│   │   └── main.ts
│   ├── public/
│   └── package.json
│
└── README.md
```

---

## 🔒 Security

- ✅ Session saved **locally** in `session.json` (not sent to frontend)
- ✅ Images downloaded locally (avoids exposing Instagram URLs)
- ✅ CORS configured via `.env` (default allows all origins for development)
- ⚠️ **DO NOT** commit `session.json` to git
- ⚠️ **DO NOT** commit `.env` to git
- ⚠️ Restrict `CORS_ORIGINS` in production to specific domains only
- ⚠️ Use HTTPS in production

---

## 🚨 Troubleshooting

**"Session expired" error:**

```bash
cd backend
rm session.json
# Login again through the interface
```

**"playwright install" error:**

```bash
cd backend
python -m playwright install chromium
```

**Images not loading:**

- Check if backend is running on port 8000
- Verify CORS settings in `main.py`

**Scraping stuck on "Extracting...":**

- Instagram may have changed page structure
- Check backend terminal for error messages
- Try logging in again

---

## 🎓 Educational Purpose

This project is intended **for educational purposes only**.

- Demonstrates web scraping, browser automation, real-time data streaming, and modern web development practices
- Always respect Instagram's Terms of Service
- Use responsibly and ethically
- Do not use for spam, harassment, or unauthorized data collection

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Open an **issue** describing the problem/suggestion
2. Fork the project
3. Create a feature branch: `git checkout -b feature/new-feature`
4. Commit changes: `git commit -m 'Add amazing feature'`
5. Push: `git push origin feature/new-feature`
6. Open a detailed **Pull Request**

---

## 📄 License

Project developed for educational purposes. Use responsibly.

---

Made with ❤️ using Vue.js, FastAPI, and Playwright
