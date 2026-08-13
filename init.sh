#!/bin/bash

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, starting services..."
    cd frappe-bench
    bench start
else
    echo "Creating new bench..."
    # If the directory exists but frappe is not present (incomplete initialization), clean it up first
    if [ -d "frappe-bench" ]; then
        echo "Removing incomplete frappe-bench directory..."
        find frappe-bench -mindepth 1 -maxdepth 1 ! -name 'apps' -exec rm -rf {} +
        if [ -d "frappe-bench/apps" ]; then
            find frappe-bench/apps -mindepth 1 -maxdepth 1 ! -name 'crm' -exec rm -rf {} +
        fi
    fi

    # Initialize the bench in a temp directory because the mount point 'frappe-bench/apps/crm' already exists
    echo "Initializing bench in temp directory..."
    bench init --skip-redis-config-generation frappe-bench-temp --version version-15
    
    echo "Moving bench files (including hidden configs) to final directory..."
    # Move all files and folders (including hidden ones starting with .) EXCEPT "apps"
    find frappe-bench-temp -mindepth 1 -maxdepth 1 ! -name 'apps' -exec mv -t frappe-bench/ {} +
    
    # Move the frappe app folder
    mkdir -p frappe-bench/apps
    mv frappe-bench-temp/apps/frappe frappe-bench/apps/
    rm -rf frappe-bench-temp

    cd frappe-bench

    # Use containers instead of localhost
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379

    # Remove redis, watch from Procfile
    sed -i '/redis/d' ./Procfile
    sed -i '/watch/d' ./Procfile

    if [ ! -d "apps/crm" ]; then
        bench get-app crm --branch main
    fi
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