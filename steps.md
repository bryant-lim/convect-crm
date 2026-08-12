# Frappe CRM Setup & Deployment Guide

Choose the method that matches your deployment scenario.

---

## Method A: Direct Fresh Setup on VPS (Easiest for clean setup)

Use this method if you want to deploy a fresh, clean CRM directly on your Hostinger VPS without developing locally first.

### Step 1: SSH into your VPS
```bash
ssh root@72.61.119.91
```

### Step 2: Create project directory and configure permissions
Ensure the host directories exist and have correct owner permissions for the container user (UID 1000):
```bash
mkdir -p convect-crm
cd convect-crm
mkdir -p frappe-bench db-data
chown -R 1000:1000 frappe-bench db-data
```

### Step 3: Clone the repository config files
```bash
git clone https://github.com/bryant-lim/convect-crm.git .
```

### Step 4: Start the containers
```bash
docker compose up -d
```
*Note: This will take 2–3 minutes on first run as it initializes the database and pulls the bench.*

### Step 5: Monitor the setup progress
```bash
docker compose logs -f frappe
```
Wait until you see logs showing `bench start` or the web services running.

### Step 6: Seed the Malaysian SME Mock Data
Run the generator script inside the container:
```bash
docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.localhost execute /workspace/generate_mock_data.py"
```
You can now access your site at `http://72.61.119.91:8000`.

---

## Method B: Syncing from Local to VPS (For migrating local work)

Use this method if you have already set up and customized your CRM locally and want to copy your exact database and files over to the VPS.

### Step 1: Stop local containers (to ensure database files are safely written)
On your local machine:
```bash
docker compose down
```

### Step 2: Sync everything (including DB and plugin files) to your VPS
```bash
rsync -avz --exclude '.git' ./ root@72.61.119.91:/root/convect-crm/
```

### Step 3: SSH into VPS, fix folder ownership permissions, and start the containers
```bash
ssh root@72.61.119.91 "cd /root/convect-crm && mkdir -p frappe-bench db-data && chown -R 1000:1000 frappe-bench db-data && docker compose up -d"
```

### Step 4: Start your local containers back up
On your local machine:
```bash
docker compose up -d
```