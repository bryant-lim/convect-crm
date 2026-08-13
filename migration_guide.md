# Migration Guide: Local to Hostinger VPS (crm.convect.tech)

This guide provides step-by-step instructions to migrate your local Frappe CRM setup (including database, files, WhatsApp/Chatbot integrations, custom tags columns, and secure website live chat webhook API) to your Hostinger VPS running Docker.

---

## Answers to Your Questions

### 1. Is compiling into custom apps needed?
**No.** 
- All your customization changes in the `crm` app are saved in your local git repository.
- The `frappe_whatsapp` and `frappe_whatsapp_chatbot` integrations are defined in your setup script (`init.sh`).
- When Docker starts on the VPS, `init.sh` will automatically fetch these apps via Git and install them, ensuring they are identical.

### 2. Is a manual backup of the database needed?
**Yes.**
Docker containers use volumes (`mariadb-data` and `frappe-bench`) to store the database and uploaded attachments. These files are not stored in Git. You must perform a standard Frappe site backup locally and restore it on the VPS.

### 3. Which directory to use on VPS (`/opt` or `/root`)?
**Use `/opt/convect-crm`.**
- Storing configurations in `/opt` is the standard Linux best practice for third-party application directories. 
- It keeps files organized and accessible, and prevents stuffing the `/root` user home directory with application configurations.

---

## Step-by-Step Migration Guide

### Phase 1: Local Backup

We will generate a complete backup of the database and uploaded files from the local container.

1. **Generate the backup**:
   On your local machine, open a terminal in your workspace directory and run:
   ```bash
   docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.localhost backup --with-files"
   ```
   *This command outputs the path of the backup files created inside the container.*

2. **Locate the files**:
   The backup files are saved in:
   `./sites/crm.localhost/private/backups/`
   You will find three files:
   - `[timestamp]_database.sql.gz` (Database)
   - `[timestamp]_files.tar` (Public Uploads)
   - `[timestamp]_private_files.tar` (Private Uploads)

---

### Phase 2: VPS Server Preparation

1. **Connect to your Hostinger VPS**:
   ```bash
   ssh root@your_vps_ip
   ```

2. **Install Docker and Docker Compose** (if not already installed):
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   ```

3. **Set up directory**:
   Create the directory for your CRM repository under `/opt/convect-crm`:
   ```bash
   mkdir -p /opt/convect-crm
   ```

---

### Phase 3: Push Custom Code and Transfer

Since we modified the backend API and frontend views to support tags columns, tags deletion, and the live chat webhook, you must push your local code changes to your git repository (`bryant-lim/convect-crm`) and pull it on the VPS.

1. **Commit and push your changes locally**:
   ```bash
   git add -A
   git commit -m "feat: custom tags column, tag management fix, and secure live chat webhook integration"
   git push origin main
   ```

2. **Clone/Pull the repository on your VPS**:
   ```bash
   cd /opt/convect-crm
   git clone https://github.com/bryant-lim/convect-crm.git .
   ```

3. **Transfer Backup Files to VPS**:
   Using `rsync` from your local machine, transfer your backups to the VPS folder:
   ```bash
   # Run from your local terminal
   rsync -avz ./sites/crm.localhost/private/backups/ root@your_vps_ip:/opt/convect-crm/sites/crm.localhost/private/backups/
   ```

---

### Phase 4: Spin up Docker & Restore Database on VPS

1. **Modify Site Initialization in `init.sh` for Production**:
   Open `/opt/convect-crm/init.sh` on the VPS. 
   To support your production domain `crm.convect.tech`, we need the site folder name to match the domain.
   Replace instances of `crm.localhost` with `crm.convect.tech` in the setup script.
   
   *Example block in VPS `init.sh`:*
   ```bash
   bench new-site crm.convect.tech \
       --mariadb-root-password 123 \
       --admin-password admin \
       --no-mariadb-socket
   bench --site crm.convect.tech install-app crm
   bench --site crm.convect.tech install-app frappe_whatsapp
   bench --site crm.convect.tech install-app frappe_whatsapp_chatbot
   ```

2. **Start Docker containers on the VPS**:
   ```bash
   cd /opt/convect-crm
   docker compose up -d
   ```
   *Wait for the `frappe` service initialization to finish installing and setting up the apps.*

3. **Restore the database and files**:
   Find the backup filenames you copied to the VPS (located in `/opt/convect-crm/sites/crm.localhost/private/backups/`).
   Run the restore command inside the VPS container targeting your production site `crm.convect.tech`:
   ```bash
   docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.convect.tech restore \
       sites/crm.localhost/private/backups/[timestamp]_database.sql.gz \
       --with-public-files sites/crm.localhost/private/backups/[timestamp]_files.tar \
       --with-private-files sites/crm.localhost/private/backups/[timestamp]_private_files.tar"
   ```
   *Confirm the database replacement if prompted.*

4. **Run migrations and clear cache**:
   ```bash
   docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.convect.tech migrate"
   docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.convect.tech clear-cache"
   ```

---

### Phase 5: Domain Routing & SSL Setup (Nginx Reverse Proxy)

Since Frappe CRM runs on port `8000` (Vite backend/web API) and port `9000` (Socket.IO websockets), we set up Nginx on the host VPS to forward external requests on port `80` (HTTP) and `443` (HTTPS) to the containers.

1. **Install Nginx and Certbot** on the VPS host:
   ```bash
   sudo apt install -y nginx certbot python3-certbot-nginx
   ```

2. **Configure Nginx**:
   Create a config file at `/etc/nginx/sites-available/crm.convect.tech`:
   ```nginx
   server {
       listen 80;
       server_name crm.convect.tech;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }

       location /socket.io {
           proxy_pass http://127.0.0.1:9000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
           proxy_set_header Host $host;
       }
   }
   ```

3. **Enable configuration and reload Nginx**:
   ```bash
   ln -s /etc/nginx/sites-available/crm.convect.tech /etc/nginx/sites-enabled/
   nginx -t
   systemctl reload nginx
   ```

4. **Obtain SSL Certificate (HTTPS)**:
   Ensure your domain DNS `crm.convect.tech` is pointed to the Hostinger VPS IP address, then run:
   ```bash
   sudo certbot --nginx -d crm.convect.tech
   ```
   *Certbot will automatically obtain certificates and update your Nginx configuration.*

---

## Appendix A: Managing the Website Chat Domain Whitelist

To secure the Live Chat endpoint (`/api/method/crm.api.web_chat.capture_web_lead`), the CRM verifies the Origin/Referer headers against a whitelist in `site_config.json`.

### How to Edit the Whitelist on Production:

1. **Copy the config file out of the container**:
   Run this on your VPS inside `/opt/convect-crm`:
   ```bash
   docker compose cp frappe:/home/frappe/frappe-bench/sites/crm.convect.tech/site_config.json ./site_config.json
   ```

2. **Edit `site_config.json`**:
   Add or remove domain patterns from the `web_chat_allowed_origins` list (wildcards like `*.domain.com` are supported):
   ```json
   {
    ...
    "web_chat_allowed_origins": [
      "https://crm.convect.tech",
      "https://*.creativatestudio.my"
    ],
    "web_chat_secret_token": "convect-token-secret-696"
   }
   ```

3. **Copy the file back in and clear cache**:
   ```bash
   docker compose cp ./site_config.json frappe:/home/frappe/frappe-bench/sites/crm.convect.tech/site_config.json
   docker compose exec frappe bash -c "cd frappe-bench && bench --site crm.convect.tech clear-cache"
   ```
   *Clean up the temporary file on the host VPS afterward (`rm ./site_config.json`).*

---

## Appendix B: Direct Live Chat Frontend Integration

To send website live chat leads directly to the CRM, make a POST request from your chat client:

* **Method**: `POST`
* **URL**: `https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead`
* **Payload**:
  ```json
  {
    "name": "Visitor Name",
    "email": "visitor@email.com",
    "mobile_no": "+60123456789",
    "company_name": "Visitor Company",
    "source": "web_chat",
    "notes": "Initial chat summary message..."
  }
  ```

---

## Appendix C: Google Forms Webhook Integration (via Apps Script)

Since Google Forms runs server-side on Google's systems, it does not send browser Origin headers. To allow submissions, it uses the secure token (`convect-token-secret-696`) to bypass domain checks.

### How to Set It Up:

1. Open your **Google Form**.
2. Click the three dots (More) menu in the top-right corner, and select **Script editor** (Apps Script).
3. Paste the following script into the editor:

```javascript
function onFormSubmit(e) {
  var url = "https://crm.convect.tech/api/method/crm.api.web_chat.capture_web_lead";
  
  var name = "";
  var email = "";
  var mobile = "";
  var company = "";
  var message = "";
  
  // Extract answers from the Form response object
  var itemResponses = e.response.getItemResponses();
  for (var i = 0; i < itemResponses.length; i++) {
    var itemResponse = itemResponses[i];
    var questionTitle = itemResponse.getItem().getTitle().trim();
    var answer = itemResponse.getResponse();
    
    // Match your Google Form question names exactly (case-sensitive)
    if (questionTitle === "Name") {
      name = answer;
    } else if (questionTitle === "Email") {
      email = answer;
    } else if (questionTitle === "Mobile") {
      mobile = answer;
    } else if (questionTitle === "Company Name") {
      company = answer;
    } else if (questionTitle === "Message Enquiry") {
      message = answer;
    }
  }
  
  // Fallback: If Email collection is enabled in Google Form Settings
  if (!email) {
    email = e.response.getRespondentEmail();
  }
  
  // Prepare payload
  var payload = {
    "name": name,
    "email": email,
    "mobile_no": mobile,
    "company_name": company,
    "notes": message,
    "source": "web form",
    "secret_token": "convect-token-secret-696"
  };
  
  var options = {
    "method": "post",
    "contentType": "application/json",
    "payload": JSON.stringify(payload),
    "muteHttpExceptions": true
  };
  
  try {
    var response = UrlFetchApp.fetch(url, options);
    Logger.log("Response Code: " + response.getResponseCode());
    Logger.log("Response Body: " + response.getContentText());
  } catch (err) {
    Logger.log("Error: " + err.toString());
  }
}
```

4. Click **Save** (disk icon).
5. In the Apps Script sidebar on the left, click the **Triggers** icon ⏰ (alarm clock).
6. Click **Add Trigger** (bottom right):
   - **Choose which function to run**: `onFormSubmit`
   - **Choose which deployment should run**: `Head`
   - **Select event source**: `From form`
   - **Select event type**: `On form submit`
7. Click **Save** and authorize permissions when prompted.

