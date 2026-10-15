# Fullstack App: React + FastAPI + MongoDB

A small tasks app used as a complete DevOps example: three containers, local and production Docker Compose files, and a GitHub Actions pipeline that builds images, pushes them to GHCR and deploys to an Azure VM.

```
Browser ──► nginx (frontend container, port 80)
              ├── /        → React static files (Vite build)
              └── /api/*   → FastAPI (backend container, port 8000)
                                └── MongoDB (mongo container, internal only)
```

## Tech stack

| Part | Technology |
|------|-----------|
| Frontend | React 18 + Vite, served by nginx |
| Backend | Python 3.12, FastAPI, Motor (async MongoDB driver) |
| Database | MongoDB 7 (with username/password, data in a Docker volume) |
| Containers | Docker, Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |
| Hosting | Azure Virtual Machine (Ubuntu 22.04) |

## Project structure

```
.
├── backend/                  FastAPI app + Dockerfile
├── frontend/                 React app + Dockerfile + nginx.conf
├── docker-compose.yml        LOCAL: build + run all 3 services
├── docker-compose.prod.yml   PRODUCTION: pull ready images from GHCR
├── scripts/
│   ├── azure-setup.sh        creates the Azure VM (run once)
│   └── cloud-init.yml        installs Docker on the VM at first boot
├── .github/workflows/ci-cd.yml
├── .env.example
└── .env.prod.example
```

## 1. Run locally with Docker

Requirement: Docker Desktop (or Docker Engine + Compose plugin).

```bash
docker compose up --build
```

| URL | What |
|-----|------|
| http://localhost:3000 | The app |
| http://localhost:8000/api/docs | FastAPI interactive docs (Swagger) |
| http://localhost:8000/api/health | Health check |
| localhost:27017 | MongoDB (only from your machine, user `admin`, password `localpass123`) |

Useful commands:

```bash
docker compose up -d --build     # run in the background
docker compose ps                # status + health of each service
docker compose logs -f backend   # follow one service's logs
docker compose down              # stop (data is kept in the volume)
docker compose down -v           # stop AND delete the database data
```

No `.env` file is needed. To change values, copy `.env.example` to `.env`.

> **Recommended once:** generate the lock file so every build (local and CI) uses the exact same package versions, then commit it:
>
> ```bash
> cd frontend && npm install && cd ..
> git add frontend/package-lock.json
> ```
>
> The frontend Dockerfile works without it (falls back to `npm install`), but a lock file makes builds reproducible.

## 2. Run without Docker (development with hot reload)

Start only MongoDB in Docker, run the code directly on your machine:

```bash
# Terminal 1: database
docker compose up mongo

# Terminal 2: backend
cd backend
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
MONGO_USER=admin MONGO_PASSWORD=localpass123 uvicorn app.main:app --reload --port 8000

# Terminal 3: frontend
cd frontend
npm install
npm run dev                                           # http://localhost:5173
```

Vite proxies `/api` to `localhost:8000`, so no CORS or URL settings are needed.

## 3. Environment variables (backend)

| Variable | Default | Meaning |
|----------|---------|---------|
| `MONGO_HOST` | `localhost` | MongoDB host (`mongo` inside Docker) |
| `MONGO_PORT` | `27017` | MongoDB port |
| `MONGO_USER` / `MONGO_PASSWORD` | empty | Credentials (auth is skipped if the user is empty) |
| `MONGO_DB` | `appdb` | Database name |
| `CORS_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed origins |

## 4. How the CI/CD pipeline works

File: `.github/workflows/ci-cd.yml`. It runs on every push to `main` (or manually from the Actions tab).

**Job 1: Build & push images to GHCR**
1. Computes the image names: `ghcr.io/<owner>/<repo>-backend` and `-frontend` (lowercase).
2. Logs in to GHCR with the built-in `GITHUB_TOKEN` (no extra secret needed).
3. `docker compose build backend frontend` uses `docker-compose.yml`, so CI builds exactly what you build locally.
4. `docker compose push backend frontend` pushes the images tagged with the commit SHA, then `latest`.

**Job 2: Deploy to Azure** (runs only if job 1 succeeded)
1. Connects to the VM over SSH.
2. Copies `docker-compose.prod.yml` (as `docker-compose.yml`) and a freshly generated `.env` to `~/app` on the VM.
3. Logs in to GHCR on the VM, runs `docker compose pull` and `docker compose up -d`.
4. Smoke test: calls `http://<VM-IP>/api/health` until it answers (fails the pipeline otherwise and prints container logs).

## 5. First-time setup: from zero to deployed

### Step 1: Create the Azure VM

Install the [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli), then:

```bash
az login
bash scripts/azure-setup.sh
```

The script creates a resource group, an Ubuntu VM with Docker installed, opens port 80, generates an SSH key (`~/.ssh/azure_deploy`) and prints the values for the next step. Default VM size is `Standard_B2s`; if it is unavailable in your region, try `VM_SIZE=Standard_B1ms` or `LOCATION=northeurope`.

### Step 2: Create the GitHub repository and add secrets

Create a repository (for example `fullstack-app`) and add these under **Settings → Secrets and variables → Actions**:

| Secret | Value |
|--------|-------|
| `AZURE_VM_HOST` | VM public IP printed by the script |
| `AZURE_VM_USER` | `azureuser` |
| `AZURE_VM_SSH_KEY` | full content of `~/.ssh/azure_deploy` (including the BEGIN/END lines) |
| `MONGO_USER` | `admin` |
| `MONGO_PASSWORD` | a long password, letters and numbers only |

### Step 3: Push the code

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-user>/<repo>.git
git push -u origin main
```

Open the **Actions** tab and watch the two jobs. When both are green, open `http://<VM-IP>`.

## 6. Troubleshooting

| Problem | Fix |
|---------|-----|
| `denied` / `unauthorized` when the VM pulls images | Repo → Settings → Actions → General → Workflow permissions must allow packages. Alternatively make the two packages public (GitHub profile → Packages → package → Settings). |
| SSH step fails (`Permission denied (publickey)`) | `AZURE_VM_SSH_KEY` must be the **private** key with the BEGIN/END lines and a final newline. |
| Smoke test times out | `ssh -i ~/.ssh/azure_deploy azureuser@<IP>` then `cd ~/app && docker compose ps && docker compose logs`. Also confirm port 80 is open in the Azure network security group. |
| `docker: command not found` on the VM right after creation | cloud-init is still installing Docker. Wait 2 to 3 minutes and re-run the workflow. |
| Changed `MONGO_PASSWORD` but the app cannot log in | MongoDB sets the password only on first start. Either change it back, or reset the data: `docker compose down -v` on the VM (this deletes the data). |
| Port 3000/8000/27017 already in use locally | Stop the other program or change the left side of the port mapping in `docker-compose.yml`. |

## 7. Clean up Azure (to stop paying)

```bash
az group delete --name fullstack-rg --yes --no-wait
```

## API summary

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Checks API and database |
| GET | `/api/tasks` | List tasks |
| POST | `/api/tasks` | Create task `{ "title": "..." }` |
| PATCH | `/api/tasks/{id}` | Update `title` and/or `done` |
| DELETE | `/api/tasks/{id}` | Delete task |
