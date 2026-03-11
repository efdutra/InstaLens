# 📸 IG Followers Scraper

Complete system for extracting Instagram profile data with followers/following information and gender classification.

---

## ⚠️ AUTHENTICATION REQUIREMENTS

### **IMPORTANT:** Login is MANDATORY

- You **MUST** log in with a **real Instagram account**
- The browser opens for manual authentication
- Session is saved locally in `session.json` for reuse

### Private vs Public Accounts

**🔒 Private Accounts:**

- You **MUST follow the target account** before scraping
- Without following, Instagram blocks access to followers/following data

**🌐 Public Accounts:**

- No need to follow the target account
- You can scrape directly

### How It Works

1. **First time:** Browser opens in **visible mode** for manual login
2. **After login:** Session saved → browser closes
3. **Future scrapes:** Browser runs in **headless mode** (background)
4. **If session expires:** Login again through the interface

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

## 🚀 Quick Start

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
IGC/
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
- ✅ CORS configured for `localhost:5173` (adjust for production)
- ⚠️ **DO NOT** commit `session.json` to git
- ⚠️ **DO NOT** commit `.env` to git
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
