# Frappe CRM Setup & Deployment Guide (Named Volumes)

Because we are using Docker named volumes, the database and site files are managed internally by Docker. Follow these steps to set up and deploy.

---

## 1. Setup on Local Dev Machine
Start the containers locally:
```bash
docker compose up -d
```
*Wait 2–3 minutes for initialization. Access the site at `http://localhost:8000` (User: `Administrator`, Pass: `admin`).*

## 2. Setup on Hostinger VPS
1. SSH into your VPS:
   ```bash
   ssh root@72.61.119.91
   ```
2. Clone the repository into a project directory:
   ```bash
   git clone https://github.com/bryant-lim/convect-crm.git convect-crm
   cd convect-crm
   ```
3. Start the containers on the VPS:
   ```bash
   docker compose up -d
   ```
   *(Wait 2–3 minutes for VPS site setup to complete).*

---

## 3. Sync Database Data (Local to VPS)

To copy your local custom changes and database entries to the VPS:

### Step A: Run backup on your local machine
```bash
docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.localhost backup --with-files"
```
*(This generates backup files inside the container).*

### Step B: Copy the backup files from the local container to your local Mac
```bash
docker compose cp frappe:/home/frappe/frappe-bench/sites/crm.localhost/private/backups/ ./backups
```

### Step C: Upload the backup directory to the VPS
```bash
scp -r ./backups root@72.61.119.91:/root/convect-crm/
```

### Step D: Copy the backup file into the VPS container
SSH into your VPS, go to `/root/convect-crm`, and run:
```bash
docker compose cp ./backups/<backup_filename>.sql.gz frappe:/home/frappe/frappe-bench/
```

### Step E: Restore the database on the VPS
Run the restore command inside the VPS container:
```bash
docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.localhost restore /home/frappe/frappe-bench/<backup_filename>.sql.gz --mariadb-root-password 123"
```
*(Restart services afterwards: `docker compose restart`)*