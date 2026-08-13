#!/bin/bash

if [ -d "/home/frappe/frappe-bench/apps/frappe" ] && [ -f "/home/frappe/frappe-bench/sites/common_site_config.json" ] && [ -f "/home/frappe/frappe-bench/Procfile" ]; then
    echo "Bench already exists, starting services..."
    cd frappe-bench
    bench start
else
    echo "Creating new bench..."
    # Clean up any broken/incomplete directories
    if [ -d "frappe-bench" ]; then
        echo "Removing incomplete frappe-bench directory..."
        rm -rf frappe-bench
    fi

    # Initialize the bench normally (this will succeed 100% since there are no nested mount points inside)
    echo "Initializing bench..."
    bench init --skip-redis-config-generation frappe-bench --version version-15 || exit 1
    
    cd frappe-bench

    # Link the custom crm app from the workspace mount
    echo "Symlinking custom CRM app..."
    ln -s /workspace/apps/crm apps/crm

    # Use containers instead of localhost
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    # Remove redis, watch from Procfile
    sed -i '/redis/d' ./Procfile
    sed -i '/watch/d' ./Procfile

    # Fetch other apps
    bench get-app https://github.com/shridarpatil/frappe_whatsapp.git
    bench get-app https://github.com/shridarpatil/frappe_whatsapp_chatbot.git

    echo "Setting up new site..."
    bench new-site crm.localhost \
        --mariadb-root-password 123 \
        --admin-password admin \
        --no-mariadb-socket

    bench --site crm.localhost install-app crm
    bench --site crm.localhost install-app frappe_whatsapp
    bench --site crm.localhost install-app frappe_whatsapp_chatbot
    bench --site crm.localhost set-config developer_mode 1
    bench --site crm.localhost set-config mute_emails 1
    bench --site crm.localhost set-config server_script_enabled 1
    bench --site crm.localhost clear-cache
    bench use crm.localhost

    bench start
fi