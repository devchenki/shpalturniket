# Примеры использования - Shaplych Monitoring System

## 📋 Содержание

- [Быстрый старт](#быстрый-старт)
- [API примеры](#api-примеры)
- [Конфигурация](#конфигурация)
- [Сценарии использования](#сценарии-использования)
- [Интеграции](#интеграции)
- [Troubleshooting](#troubleshooting)

## 🚀 Быстрый старт

### 1. Установка и запуск

```bash
# Клонирование репозитория
git clone https://github.com/your-repo/shaplych-monitoring.git
cd shaplych-monitoring

# Запуск через batch файл (Windows)
start.bat

# Или через PowerShell
.\start.ps1

# Открыть браузер
# http://localhost:5181
```

### 2. Первоначальная настройка

#### Настройка Telegram бота
1. Создайте бота через [@BotFather](https://t.me/BotFather)
2. Получите токен бота
3. Перейдите в **Telegram → Настройки**
4. Вставьте токен и нажмите **Сохранить**
5. Добавьте ваш chat_id в список получателей

#### Настройка устройств
1. Перейдите в **Устройства**
2. Нажмите **Добавить устройство**
3. Заполните данные:
   - **ID устройства**: T001
   - **IP адрес**: 192.168.1.100
   - **Описание**: Турникет вход
   - **Категория**: Турникет
4. Нажмите **Сохранить**

### 3. Создание мероприятия

```bash
# Перейдите в "Мероприятия"
# 1. Создайте категорию мероприятия
# 2. Выберите устройства для мероприятия
# 3. Сохраните конфигурацию
```

## 🔌 API примеры

### Управление устройствами

#### Получить список устройств
```bash
curl -X GET "http://127.0.0.1:8771/api/devices" \
  -H "Content-Type: application/json"
```

```json
{
  "devices": [
    {
      "id": 1,
      "device_id": "T001",
      "ip": "192.168.1.100",
      "description": "Турникет вход",
      "category": "Турникет",
      "status": "online",
      "response_ms": 45,
      "last_check": "2025-09-09T13:30:00Z"
    }
  ]
}
```

#### Создать устройство
```bash
curl -X POST "http://127.0.0.1:8771/api/devices" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "T002",
    "ip": "192.168.1.101",
    "description": "Турникет выход",
    "category": "Турникет"
  }'
```

#### Ping устройства
```bash
curl -X POST "http://127.0.0.1:8771/api/ping/T001" \
  -H "Content-Type: application/json"
```

### Управление Telegram ботом

#### Получить статус бота
```bash
curl -X GET "http://127.0.0.1:8771/api/bot/status" \
  -H "Content-Type: application/json"
```

#### Запустить бота
```bash
curl -X POST "http://127.0.0.1:8771/api/bot/start" \
  -H "Content-Type: application/json"
```

#### Получить логи бота
```bash
curl -X GET "http://127.0.0.1:8771/api/bot/logs" \
  -H "Content-Type: application/json"
```

### Управление мероприятиями

#### Создать категорию мероприятия
```bash
curl -X POST "http://127.0.0.1:8771/api/events/categories" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Конференция 2025",
    "description": "Ежегодная конференция компании"
  }'
```

#### Добавить устройства в мероприятие
```bash
curl -X POST "http://127.0.0.1:8771/api/events/categories/1/devices" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "device_id": "T001",
      "is_enabled": true
    },
    {
      "device_id": "T002",
      "is_enabled": false
    }
  ]'
```

### Server-Sent Events

#### Подключение к потоку событий
```javascript
const eventSource = new EventSource('http://127.0.0.1:8771/api/events/stream');

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Получено событие:', data);
  
  switch(data.type) {
    case 'device_status':
      updateDeviceStatus(data.data);
      break;
    case 'ping_result':
      updatePingResult(data.data);
      break;
    case 'bot_status':
      updateBotStatus(data.data);
      break;
  }
};

eventSource.onerror = function(event) {
  console.error('Ошибка SSE соединения:', event);
};
```

## ⚙️ Конфигурация

### config.json
```json
{
  "TOKEN": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
  "time_connect": "50",
  "chat_id": [123456789, 987654321]
}
```

### IP_list.json
```json
{
  "T001": ["192.168.1.100", "Турникет вход", "1"],
  "T002": ["192.168.1.101", "Турникет выход", "1"],
  "T003": ["192.168.1.102", "Турникет парковка", "0"]
}
```

### Переменные окружения
```bash
# Backend
export DATABASE_URL="sqlite:///./shaplych_monitoring.db"
export SECRET_KEY="your-secret-key-here"
export DEBUG="true"
export LOG_LEVEL="INFO"

# Frontend
export VITE_API_URL="http://127.0.0.1:8771/api"
export VITE_APP_TITLE="Shaplych Monitoring"

# Telegram Bot
export TELEGRAM_TOKEN="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
export TELEGRAM_CHAT_IDS="123456789,987654321"
```

## 🎯 Сценарии использования

### Сценарий 1: Мониторинг офисных турникетов

```python
# Настройка устройств
devices = [
    {"device_id": "T001", "ip": "192.168.1.100", "description": "Главный вход"},
    {"device_id": "T002", "ip": "192.168.1.101", "description": "Выход"},
    {"device_id": "T003", "ip": "192.168.1.102", "description": "Парковка"}
]

# Создание мероприятия
event = {
    "name": "Рабочий день",
    "description": "Обычный рабочий день",
    "devices": ["T001", "T002", "T003"]
}

# Настройка уведомлений
notifications = {
    "email": "admin@company.com",
    "telegram": True,
    "threshold": 5  # минут без ответа
}
```

### Сценарий 2: Конференция с ограниченным доступом

```python
# Создание мероприятия
conference_event = {
    "name": "Конференция 2025",
    "description": "Ежегодная конференция",
    "devices": ["T001", "T002"],  # Только главный вход и выход
    "schedule": {
        "start": "2025-09-15T09:00:00Z",
        "end": "2025-09-15T18:00:00Z"
    }
}

# Настройка уведомлений для конференции
conference_notifications = {
    "telegram": True,
    "chat_ids": [123456789, 987654321],  # Организаторы
    "alerts": ["device_offline", "high_traffic"]
}
```

### Сценарий 3: Многоуровневая система доступа

```python
# Уровни доступа
access_levels = {
    "public": ["T001"],      # Общедоступные зоны
    "staff": ["T001", "T002"],  # Сотрудники
    "vip": ["T001", "T002", "T003"]  # VIP зоны
}

# События с разными уровнями доступа
events = [
    {
        "name": "Публичное мероприятие",
        "access_level": "public",
        "devices": access_levels["public"]
    },
    {
        "name": "Корпоративное мероприятие",
        "access_level": "staff",
        "devices": access_levels["staff"]
    }
]
```

## 🔗 Интеграции

### Интеграция с внешними системами

#### Webhook для уведомлений
```python
# Настройка webhook
webhook_config = {
    "url": "https://your-system.com/webhook",
    "events": ["device_offline", "device_online"],
    "headers": {
        "Authorization": "Bearer your-token"
    }
}

# Отправка webhook
import requests

def send_webhook(event_type, data):
    payload = {
        "event": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "data": data
    }
    
    response = requests.post(
        webhook_config["url"],
        json=payload,
        headers=webhook_config["headers"]
    )
    
    return response.status_code == 200
```

#### Интеграция с Slack
```python
# Slack webhook
slack_webhook = "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"

def send_slack_notification(message):
    payload = {
        "text": f"🔔 Shaplych Alert: {message}",
        "channel": "#monitoring",
        "username": "Shaplych Bot"
    }
    
    requests.post(slack_webhook, json=payload)
```

#### Интеграция с Email
```python
import smtplib
from email.mime.text import MIMEText

def send_email_alert(subject, message, recipients):
    msg = MIMEText(message)
    msg['Subject'] = subject
    msg['From'] = "noreply@shaplych.com"
    msg['To'] = ", ".join(recipients)
    
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login("your-email@gmail.com", "your-password")
    server.send_message(msg)
    server.quit()
```

### API интеграция

#### Python клиент
```python
import requests

class ShaplychClient:
    def __init__(self, base_url="http://127.0.0.1:8771/api"):
        self.base_url = base_url
    
    def get_devices(self):
        response = requests.get(f"{self.base_url}/devices")
        return response.json()
    
    def ping_device(self, device_id):
        response = requests.post(f"{self.base_url}/ping/{device_id}")
        return response.json()
    
    def create_event(self, name, description):
        data = {"name": name, "description": description}
        response = requests.post(f"{self.base_url}/events/categories", json=data)
        return response.json()

# Использование
client = ShaplychClient()
devices = client.get_devices()
result = client.ping_device("T001")
```

#### JavaScript клиент
```javascript
class ShaplychAPI {
  constructor(baseURL = 'http://127.0.0.1:8771/api') {
    this.baseURL = baseURL;
  }
  
  async getDevices() {
    const response = await fetch(`${this.baseURL}/devices`);
    return await response.json();
  }
  
  async pingDevice(deviceId) {
    const response = await fetch(`${this.baseURL}/ping/${deviceId}`, {
      method: 'POST'
    });
    return await response.json();
  }
  
  async createEvent(name, description) {
    const response = await fetch(`${this.baseURL}/events/categories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ name, description })
    });
    return await response.json();
  }
}

// Использование
const api = new ShaplychAPI();
const devices = await api.getDevices();
const result = await api.pingDevice('T001');
```

## 🔧 Troubleshooting

### Частые проблемы

#### 1. Backend не запускается
```bash
# Проверка портов
netstat -tlnp | grep 8771

# Проверка логов
tail -f backend/logs/app.log

# Проверка зависимостей
pip list | grep fastapi
```

#### 2. Frontend не подключается к API
```bash
# Проверка CORS
curl -H "Origin: http://localhost:5181" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     http://127.0.0.1:8771/api/health

# Проверка переменных окружения
echo $VITE_API_URL
```

#### 3. Telegram бот не работает
```bash
# Проверка токена
curl -X GET "https://api.telegram.org/bot$TELEGRAM_TOKEN/getMe"

# Проверка логов
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

# Перезапуск
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

### Восстановление после сбоев

#### Восстановление базы данных
```bash
# Остановка приложения
docker-compose down

# Восстановление из резервной копии
cp backup/app.db /app/data/app.db

# Запуск приложения
docker-compose up -d
```

#### Восстановление конфигурации
```bash
# Восстановление config.json
cp backup/config.json /app/config.json

# Восстановление IP_list.json
cp backup/IP_list.json /app/IP_list.json

# Перезапуск
docker-compose restart
```

---

**Версия документа**: 1.0.0  
**Последнее обновление**: 2025-09-09  
**Автор**: Shaplych Development Team
