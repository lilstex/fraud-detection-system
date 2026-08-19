# Deployment Guide

This document covers two deployment paths for the Fraud Detection System:

1. **Render** (recommended — free tier, no server management)
2. **A Linux VPS** (for full control, e.g. DigitalOcean, Hetzner, AWS Lightsail)

Both paths produce a public URL you can share with your supervisor.

---

## Path A — Render (easiest)

Render reads the `render.yaml` file at the repo root and provisions both the
backend and the frontend as separate services.

### 1. Push the code to GitHub

```bash
cd fraud-detection-system
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/fraud-detection-system.git
git push -u origin main
```

### 2. Create a Render account

Sign up at https://render.com (free tier is enough for the prototype).

### 3. Create a Blueprint

- Click **New +** → **Blueprint**.
- Select your GitHub repository.
- Render reads `render.yaml` and shows both services.
- Click **Apply**.

Render will then:

- Build the backend, generate synthetic data, train the models, seed the DB,
  and start uvicorn. The first build takes 5–10 minutes because of the
  training step.
- Build the frontend and publish the static bundle.

### 4. Wire the two services together

Once the backend is deployed, Render assigns it a URL such as
`https://fraud-detection-api.onrender.com`.

- In the Render dashboard, open the **fraud-detection-web** service.
- Under **Environment**, edit `VITE_API_BASE` to match the backend URL above.
- Trigger a manual redeploy of the frontend so the new API URL is baked in.

Similarly, open the **fraud-detection-api** service and update
`CORS_ORIGINS` to include your frontend URL, e.g.
`https://fraud-detection-web.onrender.com`.

### 5. Test

Open the frontend URL in your browser and sign in with:

- `analyst / analyst123`
- or `admin / admin123`

### Notes on the Render free tier

- The free web service **spins down after 15 minutes of inactivity** and takes
  30–60 seconds to wake on the next request. Fine for a demo but noticeable
  during a live presentation. Upgrade to the **Starter** plan (~$7/month) to
  keep it always-on.
- The SQLite DB **does not persist** across free-tier deploys (the filesystem
  is ephemeral). For a real deployment, switch to Render's managed PostgreSQL
  add-on and set `DATABASE_URL` to the connection string it gives you. No
  application code changes are needed because SQLAlchemy handles the abstraction.

---

## Path B — Linux VPS (Ubuntu 22.04)

This path uses Docker Compose so it works identically on any Linux VPS with
Docker installed.

### 1. Provision a VPS

Any provider works. Recommended minimum for the prototype:

- **1 vCPU, 2 GB RAM, 25 GB SSD**
- Ubuntu 22.04 LTS
- A public IP address

DigitalOcean ($4/month), Hetzner (€4/month), Linode ($5/month), or AWS
Lightsail ($5/month) all fit.

### 2. Install Docker and Docker Compose

```bash
# SSH into the VPS
ssh root@YOUR_VPS_IP

# Install Docker
curl -fsSL https://get.docker.com | sh

# Enable and start the daemon
systemctl enable --now docker

# Verify
docker --version
docker compose version
```

### 3. Clone the repo

```bash
cd /opt
git clone https://github.com/<your-username>/fraud-detection-system.git
cd fraud-detection-system
```

### 4. Configure environment variables

```bash
cp .env.example .env
nano .env  # edit SECRET_KEY to a long random string
```

Generate a strong secret with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 5. Start the stack

```bash
docker compose up -d --build
```

Wait a few minutes for the backend to bootstrap (data generation + training).
Watch the logs:

```bash
docker compose logs -f backend
```

You'll see the training script complete before the API starts.

### 6. Test

Once ready:

```bash
curl http://YOUR_VPS_IP:8000/health
```

Open a browser to `http://YOUR_VPS_IP:3000` to reach the dashboard.

### 7. Front the app with Nginx and HTTPS (optional but recommended)

Install nginx and certbot:

```bash
apt update && apt install -y nginx certbot python3-certbot-nginx
```

Create `/etc/nginx/sites-available/fraud-detection`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable it and reload:

```bash
ln -s /etc/nginx/sites-available/fraud-detection /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

Issue an HTTPS certificate (free, from Let's Encrypt):

```bash
certbot --nginx -d your-domain.com
```

Certbot updates the nginx config to serve HTTPS and auto-renews the certificate.

### 8. Managing the deployed stack

```bash
# View logs
docker compose logs -f

# Restart after code changes
git pull
docker compose up -d --build

# Stop everything
docker compose down

# Retrain the model (once new data is available)
docker compose exec backend python scripts/train_models.py
docker compose restart backend
```

---

## Migrating to PostgreSQL

For anything beyond the prototype, replace SQLite with PostgreSQL. The schema
is compatible.

### With Render

- Add a **PostgreSQL** service in the Render dashboard.
- Copy the internal connection string.
- Set it as `DATABASE_URL` on the backend service.
- Redeploy — SQLAlchemy handles the switch.

### With a VPS

Add a Postgres service to `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: fraud
      POSTGRES_PASSWORD: change-me
      POSTGRES_DB: fraud_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

  backend:
    environment:
      DATABASE_URL: postgresql://fraud:change-me@postgres:5432/fraud_db
    depends_on:
      - postgres

volumes:
  postgres_data:
```

Then `docker compose up -d --build`.

---

## Troubleshooting

### Backend won't start — "Model not loaded"

Run the training step manually:

```bash
docker compose exec backend python scripts/train_models.py
docker compose restart backend
```

### Frontend shows a blank page

Check that `VITE_API_BASE` points to the correct backend URL and that
`CORS_ORIGINS` on the backend includes the frontend URL. Rebuild the frontend
after changing `VITE_API_BASE`.

### "401 Unauthorized" on every request

Your JWT expired (24 hours). Sign out and back in.

### Slow first response on Render

The free tier spins the service down after 15 min of inactivity. First
request after that wakes it up — takes 30–60 seconds. Upgrade to Starter to
avoid this during a live demo.

---

## Costs summary

| Path        | Setup effort | Cost / month | HTTPS | Persistent DB |
|-------------|--------------|--------------|-------|---------------|
| Render free | Very low     | $0           | ✅    | ❌ (ephemeral) |
| Render Starter | Very low  | ~$7         | ✅    | ✅ (with Postgres add-on ~$7 extra) |
| DigitalOcean VPS | Medium  | $4–6        | ✅ (Let's Encrypt) | ✅ |
| Hetzner VPS | Medium       | ~€4         | ✅ (Let's Encrypt) | ✅ |

For a supervisor demo, **Render free** is the easiest starting point. For
longer-term work, **VPS + Postgres** gives you full control.
