# 1. Stop local containers (to ensure database files are safely written)
docker compose down
# 2. Sync everything (including DB and plugin files) to your VPS
rsync -avz --exclude '.git' ./ root@72.61.119.91:/root/convect-crm/
# 3. SSH into VPS, fix folder ownership permissions, and start the containers
ssh root@72.61.119.91 "cd /root/convect-crm && mkdir -p frappe-bench db-data && chown -R 1000:1000 frappe-bench db-data && docker compose up -d"
# 4. Start your local containers back up
docker compose up -d