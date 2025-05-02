#!/bin/bash

# Обновление системы
apt update && apt upgrade -y
apt install -y python3 python3-pip python3-venv nginx git sqlite3 curl ufw certbot python3-certbot-nginx

# Создание пользователя
adduser --gecos "" appuser
usermod -aG sudo appuser

# Настройка проекта
su - appuser -c "
cd /home/appuser
git clone <your-repo-url> crm-cond || mkdir crm-cond
cd crm-cond
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn gunicorn sqlalchemy python-multipart pydantic
"

# Настройка Gunicorn
cat <<EOT > /etc/systemd/system/crm-cond.service
[Unit]
Description=Gunicorn instance to serve CRM Cond
After=network.target

[Service]
User=appuser
Group=www-data
WorkingDirectory=/home/appuser/crm-cond
Environment="PATH=/home/appuser/crm-cond/venv/bin"
ExecStart=/home/appuser/crm-cond/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app -b 0.0.0.0:8000

[Install]
WantedBy=multi-user.target
EOT

systemctl start crm-cond
systemctl enable crm-cond

# Настройка Nginx
cat <<EOT > /etc/nginx/sites-available/crm-cond
server {
    listen 80;
    server_name <your-domain-or-ip>;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static/ {
        alias /home/appuser/crm-cond/static/;
    }
}
EOT

ln -s /etc/nginx/sites-available/crm-cond /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Настройка брандмауэра
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable

# Настройка резервного копирования
mkdir /home/appuser/backups
echo "0 2 * * * cp /home/appuser/crm-cond/database.db /home/appuser/backups/database_\$(date +\\%F).db" | crontab -u appuser -

echo "Настройка завершена. Установите SSL с помощью: sudo certbot --nginx -d <your-domain>"
echo "Проверьте приложение по адресу: http://<server-ip>/finance"