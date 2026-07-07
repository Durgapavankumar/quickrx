# QuickRx Voice — Deployment Guide

## Architecture Reality Check

GitHub Pages **only serves static files** — it cannot run Python, Whisper, or FastAPI.

So the deployment split is:

| Part | Where it runs | Why |
|---|---|---|
| **Frontend** (React) | GitHub Pages | Static files only — GitHub Pages handles this fine |
| **Backend** (FastAPI + Whisper) | Your Mac (locally) | Needs a real Python process running continuously |

This means: **the deployed GitHub Pages site only works when your backend is running locally on the same machine you're viewing it from.** This is fine for solo development, demos, or a single clinic laptop — it is not yet a multi-user hosted product. That would require deploying the backend to a real server (see "Next Level" at the bottom).

---

## Part 1 — One-Time GitHub Setup

### 1. Create the repository on GitHub
Go to [github.com/new](https://github.com/new), name it `quickrx` (or anything — just update `vite.config.js`'s `base` path to match), keep it **Public** (required for free GitHub Pages), don't initialize with a README (you already have one).

### 2. Push your local project to GitHub

From the `quickrx/` project root:

```bash
git init
git add .
git commit -m "Initial commit — QuickRx Voice MVP"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/quickrx.git
git push -u origin main
```

### 3. Enable GitHub Pages
On GitHub: **Settings → Pages → Build and deployment → Source → GitHub Actions**.

That's it — the workflow file already included (`.github/workflows/deploy-frontend.yml`) will automatically build and deploy the frontend every time you push changes to the `frontend/` folder.

### 4. Update two placeholders with your actual GitHub username

**`backend/app/core/config.py`** — allow your deployed frontend to call the backend:
```python
CORS_ORIGINS: list = [
    "http://localhost:5173",
    "https://YOUR-GITHUB-USERNAME.github.io",   # ← update this
]
```

**`frontend/vite.config.js`** — only if you name the repo something other than `quickrx`:
```js
base: "/YOUR-REPO-NAME/",
```

Commit and push these two changes.

---

## Part 2 — Daily Local Development

Two scripts are included so you never have to remember the setup steps:

```bash
./start-backend.sh    # Terminal 1 — starts FastAPI + Whisper on :8000
./start-frontend.sh   # Terminal 2 — starts React dev server on :5173
```

Open **http://localhost:5173** — this is your normal local dev workflow, same as before. Nothing about local development changes.

---

## Part 3 — Using the Deployed GitHub Pages Version

1. Start the backend locally: `./start-backend.sh`
2. Visit `https://YOUR-USERNAME.github.io/quickrx/`
3. The deployed frontend calls `http://localhost:8000` (set in `frontend/.env.production`) — since your backend is running on your own machine, it works exactly like the local version, just served from a public URL you can share as a link (though the person opening that link still needs the backend running on **their** machine, since `localhost` means "this device," not your Mac specifically).

**Important nuance:** sharing the GitHub Pages link with your boss will **not** let them use the live app unless the backend also runs on their machine — GitHub Pages hosts the interface, not the AI processing. To let someone else use it without setup, you'd need Part 4 below.

---

## Part 4 — Docker: One-Command Deployment Anywhere

Docker packaging is included. On any machine with Docker (a colleague's laptop,
a clinic desktop, a VPS):

```bash
git clone https://github.com/Durgapavankumar/quickrx.git
cd quickrx
docker compose up --build
```

Open **http://localhost:8080** — that's the whole setup. Details:

- **frontend** container: nginx serves the React build and proxies `/api/v1`
  to the backend container, so the browser talks to a single origin (no CORS,
  no `VITE_API_URL` juggling).
- **backend** container: FastAPI + faster-whisper on CPU. The Whisper model
  (~145 MB) downloads on the first transcription and is cached in the
  `whisper-models` volume — so the first dictation is slow, the rest are not.
- **`quickrx-data` volume**: the SQLite database, so sessions and patient
  history survive `docker compose down` / restarts.

Note: browsers only allow microphone access on `localhost` or HTTPS. Running
on a remote server therefore needs HTTPS — which Part 6 sets up automatically.

## Part 5 — Hosting Options

| Option | Cost | Effort | Notes |
|---|---|---|---|
| **Docker on a VPS + Caddy** (DigitalOcean, Hetzner, etc.) | ~$5–6/month | Low — see Part 6 | Always-on, automatic HTTPS; pick ≥2 vCPU for usable Whisper speed |
| **Render / Railway free tier** | $0 (with limits) | Low | Free tiers sleep after inactivity and are usually too slow for Whisper |
| **Keep it local-only** | $0 | None | Fine for solo dev / single-clinic demo — no changes needed |

## Part 6 — Always-On Hosted Deployment (VPS + Automatic HTTPS)

This makes the whole app reachable at a public HTTPS URL that *anyone* can use —
no local backend, no tunnels. It adds a **Caddy** reverse proxy (the `caddy`
service in `docker-compose.yml`, behind the `prod` profile) that terminates TLS
with automatic Let's Encrypt certificates and proxies to the app. Because the
frontend already proxies `/api/v1` to the backend, everything is served
same-origin over HTTPS — so there are no CORS or mixed-content issues.

### 1. Get a server
A small VPS with **≥2 vCPU and 2–4 GB RAM** (Ubuntu), and Docker installed:
```bash
curl -fsSL https://get.docker.com | sh
```

### 2. Give it an address Caddy can get a certificate for
Either point a **domain**'s DNS `A` record at the server's IP, **or** — if you
don't have a domain — use **sslip.io**, which resolves `<ip>.sslip.io` to that
IP, giving you real HTTPS on a bare server IP with nothing to buy.

### 3. Deploy
```bash
git clone https://github.com/Durgapavankumar/quickrx.git
cd quickrx
cp .env.example .env
# edit .env → set SITE_ADDRESS to your domain or <server-ip>.sslip.io
docker compose --profile prod up -d --build
```

### 4. Open it
Visit **https://your-domain/** (or `https://<ip>.sslip.io/`). The first
dictation is slow while Whisper downloads (~145 MB, cached afterwards). Sessions
and patient history persist in the `quickrx-data` volume; TLS certs persist in
`caddy-data`, so restarts are instant and don't re-request certificates.

### 5. Lock down the firewall
Allow only **22 (SSH), 80, and 443** inbound. Ports 8000/8080 are used
internally by the containers and don't need to be public.

### Optional — keep the GitHub Pages URL working too
The `github.io` site is separate and still points at `localhost`. To make it use
this hosted backend instead, set `frontend/.env.production` to
`VITE_API_URL=https://your-domain/api/v1` and push (the backend's `CORS_ORIGINS`
in `app/core/config.py` already allows `https://durgapavankumar.github.io`). Most
people just use the VPS URL directly and ignore the Pages one.

---

## Troubleshooting

**GitHub Actions build fails** → Check the Actions tab on GitHub for the error log; most common cause is a typo in `vite.config.js`.

**Deployed site loads but shows "Failed to fetch" errors** → Your local backend isn't running, or the CORS origin in `config.py` doesn't match your actual GitHub Pages URL exactly (including `https://` and no trailing slash).

**Changes to `frontend/` don't show up on GitHub Pages** → Check the Actions tab — deployment takes ~1–2 minutes after a push; hard-refresh your browser (Cmd+Shift+R) to bypass cache.
