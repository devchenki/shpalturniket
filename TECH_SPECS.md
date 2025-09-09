# Технические спецификации - Shaplych Monitoring System

## 🏗 Архитектурные решения

### Backend Architecture

#### FastAPI + SQLModel
```python
# Структура приложения
app/
├── core/           # Основные компоненты
│   ├── config.py   # Конфигурация
│   ├── db.py       # База данных
│   └── security.py # Безопасность
├── models/         # Модели данных
├── routers/        # API маршруты
├── services/       # Бизнес-логика
└── utils/          # Утилиты
```

#### Принципы проектирования
- **Clean Architecture**: Разделение на слои
- **Dependency Injection**: Слабая связанность
- **Event-Driven**: Асинхронная обработка
- **CQRS**: Разделение команд и запросов

### Frontend Architecture

#### Vue 3 + Composition API
```typescript
// Структура компонентов
src/
├── components/     # Переиспользуемые компоненты
├── views/          # Страницы приложения
├── stores/         # Pinia stores
├── composables/    # Vue composables
├── api/            # API клиент
└── utils/          # Утилиты
```

#### Принципы проектирования
- **Component-Based**: Модульная архитектура
- **Reactive State**: Централизованное состояние
- **Type Safety**: Строгая типизация
- **Performance**: Lazy loading, виртуализация

## 🗄 База данных

### Схема данных

#### Устройства
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    device_id VARCHAR(50) UNIQUE NOT NULL,
    ip VARCHAR(15) NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'Турникет',
    status VARCHAR(20) DEFAULT 'unknown',
    response_ms INTEGER,
    last_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Мероприятия
```sql
CREATE TABLE eventcategories (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE eventdevices (
    id INTEGER PRIMARY KEY,
    event_category_id INTEGER REFERENCES eventcategories(id),
    device_id VARCHAR(50) NOT NULL,
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Темы
```sql
CREATE TABLE themepresets (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    palette JSON,
    components JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Индексы для производительности
```sql
-- Индексы для быстрого поиска
CREATE INDEX idx_devices_status ON devices(status);
CREATE INDEX idx_devices_category ON devices(category);
CREATE INDEX idx_devices_ip ON devices(ip);
CREATE INDEX idx_eventdevices_category ON eventdevices(event_category_id);
CREATE INDEX idx_eventdevices_device ON eventdevices(device_id);
```

## 🔌 API Спецификации

### RESTful API Design

#### Стандартные HTTP методы
- `GET` - Получение данных
- `POST` - Создание ресурсов
- `PUT` - Полное обновление
- `PATCH` - Частичное обновление
- `DELETE` - Удаление ресурсов

#### Стандартные коды ответов
```python
# Успешные ответы
200 OK          # Успешный запрос
201 Created     # Ресурс создан
204 No Content  # Успешно, без содержимого

# Ошибки клиента
400 Bad Request     # Неверный запрос
401 Unauthorized    # Не авторизован
403 Forbidden       # Доступ запрещен
404 Not Found       # Ресурс не найден
422 Unprocessable   # Ошибка валидации

# Ошибки сервера
500 Internal Server Error  # Внутренняя ошибка
502 Bad Gateway           # Ошибка шлюза
503 Service Unavailable   # Сервис недоступен
```

#### Формат ответов
```json
{
  "success": true,
  "data": { ... },
  "message": "Операция выполнена успешно",
  "timestamp": "2025-09-09T13:30:00Z"
}
```

### WebSocket/SSE для real-time

#### Server-Sent Events
```typescript
// Подключение к потоку событий
const eventSource = new EventSource('/api/events/stream');

eventSource.onmessage = (event) => {
  const data = JSON.parse(event.data);
  // Обработка события
};

// Типы событий
interface EventData {
  type: 'device_status' | 'ping_result' | 'bot_status' | 'heartbeat';
  timestamp: string;
  data: any;
}
```

## 🔒 Безопасность

### Аутентификация

#### JWT токены
```python
# Структура JWT payload
{
  "sub": "user_id",
  "username": "admin",
  "role": "admin",
  "permissions": ["read", "write", "admin"],
  "exp": 1640995200,
  "iat": 1640908800
}
```

#### Refresh token механизм
```python
# Двухтокенная система
access_token = create_access_token(user_id, expires_delta=timedelta(minutes=15))
refresh_token = create_refresh_token(user_id, expires_delta=timedelta(days=7))
```

### Авторизация

#### RBAC (Role-Based Access Control)
```python
# Роли пользователей
class UserRole(Enum):
    ADMIN = "admin"           # Полный доступ
    OPERATOR = "operator"     # Управление устройствами
    VIEWER = "viewer"         # Только просмотр

# Разрешения
class Permission(Enum):
    READ_DEVICES = "read:devices"
    WRITE_DEVICES = "write:devices"
    MANAGE_BOT = "manage:bot"
    VIEW_ANALYTICS = "view:analytics"
```

### Защита данных

#### Валидация входных данных
```python
# Pydantic модели для валидации
class DeviceCreate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=50)
    ip: str = Field(..., regex=r'^(\d{1,3}\.){3}\d{1,3}$')
    description: Optional[str] = Field(None, max_length=500)
    category: str = Field(default="Турникет", max_length=50)
```

#### SQL Injection защита
```python
# Использование SQLModel ORM
devices = session.exec(
    select(Device).where(Device.status == "online")
).all()
```

## 📊 Мониторинг и логирование

### Структурированные логи

#### Формат логов
```json
{
  "timestamp": "2025-09-09T13:30:00.123Z",
  "level": "INFO",
  "logger": "app.routers.devices",
  "message": "Device ping completed",
  "context": {
    "device_id": "T001",
    "ip": "192.168.1.1",
    "response_time": 45,
    "status": "online",
    "user_id": "admin"
  },
  "request_id": "req_123456789"
}
```

#### Уровни логирования
```python
# Конфигурация логирования
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False
        }
    }
}
```

### Метрики Prometheus

#### Основные метрики
```python
# Счетчики
ping_requests_total = Counter('ping_requests_total', 'Total ping requests', ['device_id', 'status'])
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])

# Гистограммы
ping_duration_seconds = Histogram('ping_duration_seconds', 'Ping duration', ['device_id'])
api_duration_seconds = Histogram('api_duration_seconds', 'API request duration', ['method', 'endpoint'])

# Gauges
devices_online = Gauge('devices_online', 'Number of online devices')
devices_offline = Gauge('devices_offline', 'Number of offline devices')
```

## 🚀 Производительность

### Backend оптимизация

#### Асинхронные операции
```python
# Асинхронный ping
async def ping_device_async(device: Device) -> PingResult:
    try:
        result = await asyncio.wait_for(
            ping(device.ip, count=1, timeout=5),
            timeout=10
        )
        return PingResult(
            device_id=device.device_id,
            status="online" if result.is_alive else "offline",
            response_time=result.avg_rtt * 1000 if result.is_alive else None
        )
    except asyncio.TimeoutError:
        return PingResult(device_id=device.device_id, status="timeout")
```

#### Кэширование
```python
# Redis кэширование
from redis import Redis
import json

redis_client = Redis(host='localhost', port=6379, db=0)

async def get_device_status_cached(device_id: str):
    cache_key = f"device_status:{device_id}"
    cached = redis_client.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # Загрузка из базы данных
    status = await load_device_status(device_id)
    
    # Кэширование на 5 минут
    redis_client.setex(cache_key, 300, json.dumps(status))
    
    return status
```

### Frontend оптимизация

#### Lazy loading
```typescript
// Ленивая загрузка компонентов
const DeviceList = defineAsyncComponent(() => import('./DeviceList.vue'))
const Analytics = defineAsyncComponent(() => import('./Analytics.vue'))

// Ленивая загрузка маршрутов
const routes = [
  {
    path: '/devices',
    component: () => import('../views/Devices.vue')
  }
]
```

#### Виртуализация списков
```typescript
// Виртуализация для больших списков
import { VirtualList } from '@tanstack/vue-virtual'

// Использование
<VirtualList
  :items="devices"
  :item-height="60"
  :container-height="400"
>
  <template #default="{ item }">
    <DeviceCard :device="item" />
  </template>
</VirtualList>
```

## 🧪 Тестирование

### Backend тестирование

#### Unit тесты
```python
# pytest тесты
import pytest
from unittest.mock import Mock, patch
from app.services.ping_service import PingService

class TestPingService:
    @pytest.fixture
    def ping_service(self):
        return PingService()
    
    @patch('icmplib.ping')
    async def test_ping_device_success(self, mock_ping, ping_service):
        # Arrange
        mock_ping.return_value.is_alive = True
        mock_ping.return_value.avg_rtt = 0.05
        
        # Act
        result = await ping_service.ping_device("192.168.1.1")
        
        # Assert
        assert result.status == "online"
        assert result.response_time == 50
```

#### Integration тесты
```python
# API тесты
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_device():
    response = client.post(
        "/api/devices",
        json={
            "device_id": "T001",
            "ip": "192.168.1.1",
            "description": "Test device"
        }
    )
    assert response.status_code == 201
    assert response.json()["device_id"] == "T001"
```

### Frontend тестирование

#### Component тесты
```typescript
// Vitest тесты
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DeviceCard from '../DeviceCard.vue'

describe('DeviceCard', () => {
  it('displays device information correctly', () => {
    const device = {
      id: 1,
      device_id: 'T001',
      ip: '192.168.1.1',
      status: 'online'
    }
    
    const wrapper = mount(DeviceCard, {
      props: { device }
    })
    
    expect(wrapper.text()).toContain('T001')
    expect(wrapper.text()).toContain('192.168.1.1')
    expect(wrapper.find('.status-online').exists()).toBe(true)
  })
})
```

#### Store тесты
```typescript
// Pinia store тесты
import { setActivePinia, createPinia } from 'pinia'
import { usePingStore } from '../stores/pingStore'

describe('pingStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })
  
  it('loads devices successfully', async () => {
    const store = usePingStore()
    await store.loadDevices()
    expect(store.devices).toHaveLength(3)
  })
})
```

## 🐳 Docker и развертывание

### Docker конфигурация

#### Backend Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование кода
COPY . .

# Создание пользователя
RUN useradd --create-home --shell /bin/bash app
USER app

# Запуск приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8771"]
```

#### Frontend Dockerfile
```dockerfile
FROM node:18-alpine as build

WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
```

#### Docker Compose
```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8771:8771"
    environment:
      - DATABASE_URL=sqlite:///./app.db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend

volumes:
  redis_data:
```

## 📈 Масштабирование

### Горизонтальное масштабирование

#### Load Balancer конфигурация
```nginx
upstream backend {
    server backend1:8771;
    server backend2:8771;
    server backend3:8771;
}

upstream frontend {
    server frontend1:80;
    server frontend2:80;
}

server {
    listen 80;
    
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Database clustering
```python
# PostgreSQL с репликацией
DATABASE_CONFIG = {
    "master": {
        "host": "db-master",
        "port": 5432,
        "database": "shaplych"
    },
    "replicas": [
        {
            "host": "db-replica1",
            "port": 5432,
            "database": "shaplych"
        },
        {
            "host": "db-replica2",
            "port": 5432,
            "database": "shaplych"
        }
    ]
}
```

## 🔧 Инструменты разработки

### IDE конфигурация

#### VS Code настройки
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "typescript.preferences.importModuleSpecifier": "relative",
  "vue.codeActions.enabled": true
}
```

#### Pre-commit hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.10.1
    hooks:
      - id: isort

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.15.0
    hooks:
      - id: eslint
        files: \.(js|ts|vue)$
```

---

**Версия документа**: 1.0  
**Последнее обновление**: 2025-09-09  
**Автор**: Shaplych Development Team
