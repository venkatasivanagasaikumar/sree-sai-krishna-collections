# SREE SAI KRISHNA COLLECTIONS (SSK)
## PRODUCTION DEPLOYMENT RUNBOOK & OPERATIONAL PLAYBOOK

**Document Version:** 1.0.0  
**Target Host:** AWS Lightsail / Ubuntu 22.04 LTS (Mumbai `ap-south-1`)  
**Domain:** `https://sreesaikrishnacollections.com`  

---

## 1. INITIAL SERVER PROVISIONING & SETUP

### Step 1: Connect to Server via SSH
```bash
ssh -i ~/.ssh/ssk-lightsail-key.pem ubuntu@<SERVER_PUBLIC_IP>
```

### Step 2: Update System & Install Docker Compose
```bash
sudo apt-get update && sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release ufw

# Install Docker Engine & Docker Compose Plugin
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Allow current user to run docker
sudo usermod -aG docker $USER
```

### Step 3: Configure Host Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

---

## 2. DEPLOYING THE SSK APPLICATION

### Step 1: Clone Repository
```bash
sudo mkdir -p /opt/ssk-collections
sudo chown -R ubuntu:ubuntu /opt/ssk-collections
git clone https://github.com/venkatasivanagasaikumar/sree-sai-krishna-collections.git /opt/ssk-collections
cd /opt/ssk-collections
```

### Step 2: Configure Environment Files
```bash
# Copy production template
cp backend/.env.production.example backend/.env

# Generate a strong 64-char secret key:
PROD_SECRET=$(openssl rand -hex 32)
sed -i "s/REPLACE_WITH_OPENSSL_RAND_HEX_32_GENERATED_SECRET/$PROD_SECRET/g" backend/.env

# Open and insert real credentials for MongoDB Atlas, Razorpay, SMTP, and WhatsApp:
nano backend/.env
```

### Step 3: Build and Launch Containers
```bash
# Build multi-stage images and start in background
docker compose build --no-cache
docker compose up -d
```

### Step 4: Verify Running Services
```bash
docker compose ps
```
*Expected Output:*
```
NAME           IMAGE                      COMMAND                  SERVICE    STATUS              PORTS
ssk-frontend   ssk-collections-frontend   "nginx -g 'daemon of…"   frontend   Up (healthy)        0.0.0.0:80->80/tcp, 0.0.0.0:5173->80/tcp
ssk-backend    ssk-collections-backend    "uvicorn app.main:ap…"   backend    Up (healthy)        0.0.0.0:8000->8000/tcp
```

---

## 3. PROVISIONING SSL/TLS WITH CERTBOT & NGINX

### Step 1: Install Certbot
```bash
sudo apt-get install -y certbot python3-certbot-nginx
```

### Step 2: Issue Certificate for Primary & Admin Domains
```bash
sudo certbot certonly --standalone \
  -d sreesaikrishnacollections.com \
  -d www.sreesaikrishnacollections.com \
  -d admin.sreesaikrishnacollections.com \
  --agree-tos -m support@sreesaikrishnacollections.com --non-interactive
```

### Step 3: Mount Certificate into Frontend Container
The generated certificates are located in `/etc/letsencrypt/live/sreesaikrishnacollections.com/`. Mount these into `frontend/nginx.conf` or terminate SSL directly at Cloudflare Edge.

### Step 4: Test Automatic Certificate Renewal
```bash
sudo certbot renew --dry-run
```

---

## 4. OPERATIONAL INSPECTION & HEALTH MONITORING

### Health & Readiness Check Commands
```bash
# Liveness Probe (HTTP 200)
curl -f http://localhost:8000/health

# Readiness Probe (Database connectivity + collection counts)
curl -f http://localhost:8000/ready
```

### Inspecting Container Logs
```bash
# Real-time backend logs (colored JSON log stream)
docker compose logs -f backend

# Real-time Nginx web access and error logs
docker compose logs -f frontend

# View last 100 log lines with timestamps
docker compose logs --tail=100 -t backend
```

---

## 5. ZERO-DOWNTIME CODE UPDATE WORKFLOW

When updating the application with new features or patches:

```bash
cd /opt/ssk-collections

# 1. Pull latest verified commits from GitHub
git pull origin main

# 2. Build updated images
docker compose build --no-cache

# 3. Re-launch containers with zero downtime
docker compose up -d

# 4. Run post-deployment verification
curl -f http://localhost:8000/ready
```
