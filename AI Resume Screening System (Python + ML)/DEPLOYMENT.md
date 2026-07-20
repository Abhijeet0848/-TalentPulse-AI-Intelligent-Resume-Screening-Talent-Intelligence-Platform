# Production Deployment Guide

## AI Resume Screening & Candidate Ranking System (Python + ML)

This project is production-ready. You can deploy it using any of the options below:

---

## Option 1: Docker & Docker Compose (Recommended)

Docker provides an isolated, consistent containerized environment with all system dependencies pre-configured.

### Prerequisites
- [Docker Engine](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Steps
1. Clone or copy project files to your server.
2. Build and start the container in detached mode:
   ```bash
   docker compose up --build -d
   ```
3. Verify running container:
   ```bash
   docker ps
   ```
4. Access the web dashboard at `http://localhost:5000` or `http://<YOUR_SERVER_IP>:5000`.

---

## Option 2: Deploy on Render.com (1-Click Cloud Hosting)

1. Push your project repository to GitHub or GitLab.
2. Log into [Render.com](https://render.com/).
3. Click **New +** -> **Web Service**.
4. Connect your Git repository.
5. Set the following settings:
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`
6. Click **Create Web Service**. Render will automatically build and deploy your app with SSL/HTTPS!

---

## Option 3: Deploy on AWS EC2 / Linux VPS (Ubuntu/Debian)

### Prerequisites
- Ubuntu 22.04 LTS or Debian Linux VPS
- Domain or Static Public IP

### Step 1: Install System Packages
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-pip python3-venv nginx git
```

### Step 2: Set Up Project & Environment
```bash
git clone <YOUR_REPO_URL> /var/www/resume-screener
cd /var/www/resume-screener

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Systemd Service
Create service file `/etc/systemd/system/screener.service`:
```ini
[Unit]
Description=AI Resume Screening System WSGI Server
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/resume-screener
Environment="PATH=/var/www/resume-screener/venv/bin"
ExecStart=/var/www/resume-screener/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start screener
sudo systemctl enable screener
```

### Step 4: Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/screener`:
```nginx
server {
    listen 80;
    server_name your_domain.com_or_IP;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/screener /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Option 4: Local Production Test with Gunicorn

To test the production Gunicorn server locally:

```bash
gunicorn --bind 127.0.0.1:5000 --workers 2 wsgi:app
```

Navigate to `http://127.0.0.1:5000` in your browser.
