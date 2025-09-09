# Руководство по развертыванию - Shaplych Monitoring System

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [Локальная разработка](#локальная-разработка)
- [Docker развертывание](#docker-развертывание)
- [Продакшн развертывание](#продакшн-развертывание)
- [Мониторинг и логирование](#мониторинг-и-логирование)
- [Безопасность](#безопасность)
- [Резервное копирование](#резервное-копирование)
- [Устранение неполадок](#устранение-неполадок)

## 🚀 Быстрый старт

### Минимальные требования

- **ОС**: Windows 10/11, Linux (Ubuntu 20.04+), macOS 10.15+
- **Python**: 3.11+
- **Node.js**: 18+
- **RAM**: 4GB минимум, 8GB рекомендуется
- **Диск**: 2GB свободного места
- **Сеть**: Доступ к интернету для Telegram API

### Автоматическая установка (Windows)

1. **Скачайте проект**
```bash
git clone <repository-url>
cd shaplych-monitoring
```

2. **Запустите установку**
```bash
# Через batch файл
start.bat

# Или через PowerShell
.\start.ps1
```

3. **Откройте браузер**
```
http://localhost:5181
```

### Автоматическая установка (Linux/macOS)

1. **Скачайте проект**
```bash
git clone <repository-url>
cd shaplych-monitoring
```

2. **Запустите установку**
```bash
chmod +x install.sh
./install.sh
```

3. **Откройте браузер**
```
http://localhost:5181
```

## 💻 Локальная разработка

### Настройка окружения

#### 1. Backend (Python)

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (Windows)
venv\Scripts\activate

# Активация (Linux/macOS)
source venv/bin/activate

# Установка зависимостей
cd backend
pip install -r requirements.txt

# Запуск в режиме разработки
python -m uvicorn app.main:app --host 127.0.0.1 --port 8771 --reload
```

#### 2. Frontend (Node.js)

```bash
# Установка зависимостей
cd frontend
npm install

# Запуск в режиме разработки
npm run dev -- --port 5181
```

#### 3. Telegram Bot (опционально)

```bash
# Запуск бота
python advanced_bot.py
```

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Backend
DATABASE_URL=sqlite:///./shaplych_monitoring.db
SECRET_KEY=your-secret-key-here
DEBUG=true
LOG_LEVEL=INFO

# Frontend
VITE_API_URL=http://127.0.0.1:8771/api
VITE_APP_TITLE=Shaplych Monitoring

# Telegram Bot
TELEGRAM_TOKEN=your-bot-token-here
TELEGRAM_CHAT_IDS=123456789,987654321

# Redis (опционально)
REDIS_URL=redis://localhost:6379
```

### Структура конфигурации

```
shaplych-monitoring/
├── .env                    # Переменные окружения
├── config.json            # Конфигурация бота
├── IP_list.json           # Список устройств
├── backend/
│   ├── .env               # Backend переменные
│   └── app/
│       └── core/
│           └── config.py  # Конфигурация приложения
└── frontend/
    ├── .env               # Frontend переменные
    └── src/
        └── config/
            └── app.ts     # Конфигурация приложения
```

## 🐳 Docker развертывание

### Простое развертывание

#### 1. Создайте docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8771:8771"
    environment:
      - DATABASE_URL=sqlite:///./data/app.db
      - SECRET_KEY=your-secret-key
    volumes:
      - ./data:/app/data
      - ./config.json:/app/config.json
      - ./IP_list.json:/app/IP_list.json
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "5181:80"
    environment:
      - VITE_API_URL=http://localhost:8771/api
    depends_on:
      - backend
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

#### 2. Запуск

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

### Продвинутое развертывание

#### 1. Backend Dockerfile

```dockerfile
FROM python:3.11-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копирование и установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8771/api/health || exit 1

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8771"]
```

#### 2. Frontend Dockerfile

```dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Копирование package файлов
COPY package*.json ./
RUN npm ci --only=production

# Копирование исходного кода
COPY . .

# Сборка приложения
RUN npm run build

# Production stage
FROM nginx:alpine

# Копирование собранного приложения
COPY --from=build /app/dist /usr/share/nginx/html

# Копирование конфигурации nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 3. Nginx конфигурация

```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8771;
    }

    server {
        listen 80;
        server_name localhost;

        # Frontend
        location / {
            root /usr/share/nginx/html;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # API
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # WebSocket/SSE
        location /api/events/stream {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }
}
```

## 🌐 Продакшн развертывание

### Облачное развертывание

#### AWS EC2

1. **Создание EC2 инстанса**
```bash
# Ubuntu 22.04 LTS
# t3.medium (2 vCPU, 4GB RAM)
# Security Group: HTTP (80), HTTPS (443), SSH (22)
```

2. **Установка Docker**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

3. **Развертывание приложения**
```bash
# Клонирование репозитория
git clone <repository-url>
cd shaplych-monitoring

# Настройка переменных окружения
cp .env.example .env
nano .env

# Запуск приложения
docker-compose -f docker-compose.prod.yml up -d
```

#### Azure Container Instances

1. **Создание ресурсной группы**
```bash
az group create --name shaplych-rg --location eastus
```

2. **Развертывание контейнеров**
```bash
# Backend
az container create \
  --resource-group shaplych-rg \
  --name shaplych-backend \
  --image your-registry/shaplych-backend:latest \
  --ports 8771 \
  --environment-variables \
    DATABASE_URL=sqlite:///./data/app.db \
    SECRET_KEY=your-secret-key

# Frontend
az container create \
  --resource-group shaplych-rg \
  --name shaplych-frontend \
  --image your-registry/shaplych-frontend:latest \
  --ports 80 \
  --environment-variables \
    VITE_API_URL=http://shaplych-backend:8771/api
```

### Kubernetes развертывание

#### 1. Namespace и ConfigMap

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: shaplych-monitoring

---
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: shaplych-config
  namespace: shaplych-monitoring
data:
  DATABASE_URL: "sqlite:///./data/app.db"
  SECRET_KEY: "your-secret-key"
  VITE_API_URL: "http://shaplych-backend:8771/api"
```

#### 2. Backend Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shaplych-backend
  namespace: shaplych-monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shaplych-backend
  template:
    metadata:
      labels:
        app: shaplych-backend
    spec:
      containers:
      - name: backend
        image: your-registry/shaplych-backend:latest
        ports:
        - containerPort: 8771
        envFrom:
        - configMapRef:
            name: shaplych-config
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
        livenessProbe:
          httpGet:
            path: /api/health
            port: 8771
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/health
            port: 8771
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: shaplych-data-pvc
```

#### 3. Frontend Deployment

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shaplych-frontend
  namespace: shaplych-monitoring
spec:
  replicas: 2
  selector:
    matchLabels:
      app: shaplych-frontend
  template:
    metadata:
      labels:
        app: shaplych-frontend
    spec:
      containers:
      - name: frontend
        image: your-registry/shaplych-frontend:latest
        ports:
        - containerPort: 80
        envFrom:
        - configMapRef:
            name: shaplych-config
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 30
          periodSeconds: 10
```

#### 4. Services и Ingress

```yaml
# services.yaml
apiVersion: v1
kind: Service
metadata:
  name: shaplych-backend
  namespace: shaplych-monitoring
spec:
  selector:
    app: shaplych-backend
  ports:
  - port: 8771
    targetPort: 8771
  type: ClusterIP

---
apiVersion: v1
kind: Service
metadata:
  name: shaplych-frontend
  namespace: shaplych-monitoring
spec:
  selector:
    app: shaplych-frontend
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shaplych-ingress
  namespace: shaplych-monitoring
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - shaplych.yourdomain.com
    secretName: shaplych-tls
  rules:
  - host: shaplych.yourdomain.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: shaplych-backend
            port:
              number: 8771
      - path: /
        pathType: Prefix
        backend:
          service:
            name: shaplych-frontend
            port:
              number: 80
```

## 📊 Мониторинг и логирование

### Prometheus + Grafana

#### 1. Prometheus конфигурация

```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'shaplych-backend'
    static_configs:
      - targets: ['backend:8771']
    metrics_path: '/api/metrics'
    scrape_interval: 5s

  - job_name: 'shaplych-frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

#### 2. Grafana дашборд

```json
{
  "dashboard": {
    "title": "Shaplych Monitoring",
    "panels": [
      {
        "title": "API Requests",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(api_requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Device Status",
        "type": "stat",
        "targets": [
          {
            "expr": "devices_online",
            "legendFormat": "Online"
          },
          {
            "expr": "devices_offline",
            "legendFormat": "Offline"
          }
        ]
      }
    ]
  }
}
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

#### 1. Logstash конфигурация

```ruby
# logstash.conf
input {
  file {
    path => "/var/log/shaplych/*.log"
    type => "shaplych"
  }
}

filter {
  if [type] == "shaplych" {
    json {
      source => "message"
    }
    
    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "shaplych-logs-%{+YYYY.MM.dd}"
  }
}
```

#### 2. Kibana визуализации

```json
{
  "visualization": {
    "title": "API Response Times",
    "type": "histogram",
    "params": {
      "field": "response_time",
      "interval": "auto"
    }
  }
}
```

## 🔒 Безопасность

### SSL/TLS сертификаты

#### Let's Encrypt с Certbot

```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d shaplych.yourdomain.com

# Автоматическое обновление
sudo crontab -e
# Добавить: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Nginx SSL конфигурация

```nginx
server {
    listen 443 ssl http2;
    server_name shaplych.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/shaplych.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/shaplych.yourdomain.com/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000" always;

    # Остальная конфигурация...
}
```

### Firewall настройки

#### UFW (Ubuntu)

```bash
# Включение UFW
sudo ufw enable

# Разрешение SSH
sudo ufw allow ssh

# Разрешение HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Блокировка всех остальных портов
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

#### iptables (CentOS/RHEL)

```bash
# Очистка правил
iptables -F
iptables -X

# Политики по умолчанию
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Разрешение loopback
iptables -A INPUT -i lo -j ACCEPT

# Разрешение установленных соединений
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# Разрешение SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Разрешение HTTP/HTTPS
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# Сохранение правил
service iptables save
```

## 💾 Резервное копирование

### Автоматическое резервное копирование

#### Скрипт резервного копирования

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/shaplych"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# Создание директории
mkdir -p $BACKUP_DIR

# Резервное копирование базы данных
sqlite3 /app/data/app.db ".backup '$BACKUP_DIR/database_$DATE.db'"

# Резервное копирование конфигурации
cp /app/config.json "$BACKUP_DIR/config_$DATE.json"
cp /app/IP_list.json "$BACKUP_DIR/IP_list_$DATE.json"

# Резервное копирование логов
tar -czf "$BACKUP_DIR/logs_$DATE.tar.gz" /app/logs/

# Удаление старых резервных копий
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Отправка в облачное хранилище (опционально)
aws s3 sync $BACKUP_DIR s3://your-backup-bucket/shaplych/
```

#### Cron задача

```bash
# Добавление в crontab
crontab -e

# Ежедневное резервное копирование в 2:00
0 2 * * * /path/to/backup.sh
```

### Восстановление из резервной копии

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR="/backup/shaplych"
BACKUP_DATE=$1

if [ -z "$BACKUP_DATE" ]; then
    echo "Usage: $0 <backup_date>"
    echo "Available backups:"
    ls -la $BACKUP_DIR
    exit 1
fi

# Остановка приложения
docker-compose down

# Восстановление базы данных
cp "$BACKUP_DIR/database_$BACKUP_DATE.db" /app/data/app.db

# Восстановление конфигурации
cp "$BACKUP_DIR/config_$BACKUP_DATE.json" /app/config.json
cp "$BACKUP_DIR/IP_list_$BACKUP_DATE.json" /app/IP_list.json

# Восстановление логов
tar -xzf "$BACKUP_DIR/logs_$BACKUP_DATE.tar.gz" -C /

# Запуск приложения
docker-compose up -d
```

## 🔧 Устранение неполадок

### Частые проблемы

#### 1. Backend не запускается

```bash
# Проверка логов
docker-compose logs backend

# Проверка портов
netstat -tlnp | grep 8771

# Проверка зависимостей
pip list | grep fastapi
```

#### 2. Frontend не подключается к API

```bash
# Проверка CORS настроек
curl -H "Origin: http://localhost:5181" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: X-Requested-With" \
     -X OPTIONS \
     http://127.0.0.1:8771/api/health

# Проверка переменных окружения
echo $VITE_API_URL
```

#### 3. Telegram бот не работает

```bash
# Проверка токена
curl -X GET "https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe"

# Проверка логов бота
tail -f bot.log

# Проверка конфигурации
cat config.json
```

#### 4. База данных заблокирована

```bash
# Проверка процессов
ps aux | grep sqlite

# Проверка блокировок
lsof /app/data/app.db

# Перезапуск приложения
docker-compose restart backend
```

### Диагностические команды

#### Системная информация

```bash
# Информация о системе
uname -a
cat /etc/os-release

# Использование ресурсов
free -h
df -h
top

# Сетевые соединения
netstat -tlnp
ss -tlnp
```

#### Логи приложения

```bash
# Логи Docker контейнеров
docker-compose logs -f --tail=100

# Логи системных сервисов
journalctl -u docker -f

# Логи Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

#### Мониторинг производительности

```bash
# Мониторинг CPU и памяти
htop

# Мониторинг дисков
iotop

# Мониторинг сети
iftop

# Мониторинг процессов
ps aux --sort=-%cpu
```

### Контакты поддержки

- **GitHub Issues**: [Создать issue](https://github.com/your-repo/issues)
- **Email**: support@shaplych.com
- **Документация**: [Wiki](https://github.com/your-repo/wiki)
- **Discord**: [Сообщество](https://discord.gg/your-invite)

---

**Версия документа**: 1.0  
**Последнее обновление**: 2025-09-09  
**Автор**: Shaplych Development Team
