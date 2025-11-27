# Shaplych Monitoring System - Architecture Analysis

> **Comprehensive end-to-end technical analysis of the turnstile monitoring platform**  
> *Last Updated: 2024*

---

## Table of Contents

1. [System Overview](#system-overview)
2. [FastAPI Backend Architecture](#fastapi-backend-architecture)
3. [Service Layer Deep Dive](#service-layer-deep-dive)
4. [Event Streaming Pipeline](#event-streaming-pipeline)
5. [Database Architecture](#database-architecture)
6. [Configuration Management](#configuration-management)
7. [Legacy & Auxiliary Tooling](#legacy--auxiliary-tooling)
8. [Frontend Stack](#frontend-stack)
9. [Telegram Bot Integration](#telegram-bot-integration)
10. [Data Flow Analysis](#data-flow-analysis)
11. [Architecture Diagrams](#architecture-diagrams)
12. [Known Issues & Technical Debt](#known-issues--technical-debt)

---

## 1. System Overview

The **Shaplych Monitoring System** is a full-stack platform for real-time monitoring of turnstile devices across multiple locations. It combines:

- **Backend**: FastAPI + SQLModel/SQLite + asyncio background services
- **Frontend**: Vue 3 + Vuetify 3 + Pinia + Server-Sent Events (SSE)
- **Bot**: aiogram-powered Telegram bot for notifications and remote management
- **Monitoring**: Continuous ICMP ping-based availability checks with configurable intervals

**Core Capabilities**:
- Device CRUD operations and real-time status tracking
- Continuous monitoring with automatic config reloads (every 5 minutes)
- Event-driven architecture with SSE for live dashboard updates
- Event category management for grouping devices by events/locations
- Telegram bot lifecycle management (start/stop/restart) via API and UI
- Configuration surfacing for JSON files (`IP_list.json`, `config.json`)
- Analytics-rich dashboards with statistics and historical views

---

## 2. FastAPI Backend Architecture

### 2.1 Entry Point: `backend/app/main.py`

**File**: [`backend/app/main.py`](backend/app/main.py)

The `create_app()` factory initializes the FastAPI application with:
- **CORS middleware** for local/Tauri origins (`localhost:5173`, `tauri://localhost`, etc.)
- **API prefix**: `/api` for all routes
- **Automatic docs**: Swagger UI at `/api/docs`

**Startup Lifecycle**:
```python
@app.on_event("startup")
async def on_startup():
    create_db_and_tables()                                    # Initialize SQLite DB
    await monitoring_service.start()                          # Start continuous monitoring
    await event_category_service.initialize_active_categories() # Restore active categories
```

**Shutdown Lifecycle**:
```python
@app.on_event("shutdown")
async def on_shutdown():
    await monitoring_service.stop()  # Gracefully stop monitoring tasks
```

### 2.2 Router Organization

**Routers** (`backend/app/routers/`):

| Router | Prefix | Responsibility | Key Endpoints |
|--------|--------|----------------|---------------|
| `health.py` | `/api` | Health checks | `GET /health` |
| `devices.py` | `/api` | Device CRUD | `GET/POST/PUT/DELETE /devices/` |
| `ping.py` | `/api` | Ping operations | `POST /ping/all`, `GET /ping/device/{key}`, `GET /ping/ip/{ip}` |
| `monitoring.py` | `/api` | Monitoring control | `GET /monitoring/status`, `POST /monitoring/start`, `POST /monitoring/stop`, `POST /monitoring/ping-now`, `POST /monitoring/reload-config` |
| `config.py` | `/api` | Config surfacing | `GET /config`, `GET /config/devices`, `GET /config/bot` |
| `events.py` | `/api` | SSE streaming | `GET /events/stream`, `GET /events/recent`, `GET /events/stats` |
| `events_api.py` | `/api/events` | Event categories | `GET/POST/PUT/DELETE /events/categories`, `GET /events/categories/{id}/statistics` |
| `bot.py` | `/api/bot` | Telegram bot control | `GET /bot/status`, `POST /bot/start`, `POST /bot/stop`, `POST /bot/restart`, `GET/DELETE /bot/logs` |
| `themes.py` | `/api` | Theme presets | `GET/POST/PUT/DELETE /themes/` |

### 2.3 Router → Service Interaction Pattern

**Example: Monitoring Control Flow**

```
HTTP Request
    ↓
routers/monitoring.py → POST /monitoring/start
    ↓
services/monitoring.py → monitoring_service.start()
    ↓
    ├─ Load IP_list.json & config.json
    ├─ Create DeviceMonitor instances
    ├─ Spawn asyncio.Task for _monitoring_loop()
    ├─ Publish "monitoring_started" event
    └─ EventManager → SSE stream → Frontend
```

**Key Pattern**: Routers are thin HTTP adapters; business logic lives in service layer.

---

## 3. Service Layer Deep Dive

### 3.1 Monitoring Service

**File**: [`backend/app/services/monitoring.py`](backend/app/services/monitoring.py)

**Architecture**:
```
MonitoringService (singleton: monitoring_service)
    ├─ DeviceMonitor[] (per-device state machines)
    ├─ _monitoring_loop() (asyncio background task)
    ├─ Config reload timer (every 5 minutes)
    └─ Event emission via events_bus
```

**Core Classes**:

1. **`DeviceMonitor`** (lines 22-108):
   - Per-device state: `current_status`, `consecutive_failures`, `response_time`
   - `ping()` method: uses `icmplib.ping()` via `loop.run_in_executor()` (async wrapper for sync ICMP)
   - State change detection: emits `device_status_changed` events via `device_event_manager`

2. **`MonitoringService`** (lines 110-412):
   - **Configuration Loading**:
     - `_load_devices_from_config()`: reads `IP_list.json`, respects enabled flag (3rd array element)
     - `_load_ping_interval()`: reads `config.json` → `time_connect` (default: 30s, clamped: 10-300s)
   - **Main Loop** (`_monitoring_loop()`):
     ```python
     while self.is_running:
         # Check if config reload needed (every 5 minutes)
         if now - last_config_check > 300s:
             await _reload_configuration()
         
         # Parallel ping all devices
         ping_tasks = [monitor.ping() for monitor in self.monitors.values()]
         results = await asyncio.gather(*ping_tasks)
         
         # Update database
         await _update_database_status(results)
         
         # Emit events
         await device_event_manager.ping_completed(results)
         
         await asyncio.sleep(self.ping_interval)
     ```
   - **Database Sync**: `_update_database_status()` updates `Device` table with status, response_ms, last_check
   - **API Methods**:
     - `start()` / `stop()`: lifecycle control
     - `ping_all_now()`: ad-hoc immediate ping
     - `get_status()`: returns current monitor states

**Key Insight**: Monitoring runs independently of HTTP requests; routers can trigger immediate pings or reload configs.

### 3.2 Event Category Service

**File**: [`backend/app/services/event_categories.py`](backend/app/services/event_categories.py)

**Purpose**: Manages grouping of devices for specific events (e.g., "Concert Hall Entry", "Emergency Exit").

**Architecture**:
```
EventCategoryService (singleton: event_category_service)
    ├─ active_categories: Dict[category_id, metadata]
    ├─ category_monitors: Dict[category_id, device_ids[]]
    └─ Methods: create/update/delete/start_monitoring/stop_monitoring
```

**Key Features**:
- **Device Grouping**: `EventDevice` links `EventCategory` to `device_id` with `is_enabled` flag
- **Monitoring Orchestration**:
  - `start_category_monitoring()`: filters enabled devices, emits start event
  - `stop_category_monitoring()`: removes from active tracking, emits stop event
- **Statistics**: `get_category_statistics()` aggregates status from `monitoring_service.get_status()`
- **Lifecycle Integration**:
  ```python
  @app.on_event("startup")
  async def on_startup():
      await event_category_service.initialize_active_categories()
      # Restores monitoring for categories marked is_active=True
  ```

**Use Case**: Venue staff can create "Basketball Game - North Entrance" category, assign specific turnstiles, and track them separately.

### 3.3 Telegram Bot Service

**File**: [`backend/app/services/telegram_bot.py`](backend/app/services/telegram_bot.py)

**Architecture**:
```
TelegramBotService (singleton: telegram_bot_service)
    ├─ Bot (aiogram Bot instance)
    ├─ Dispatcher (aiogram Dispatcher with MemoryStorage)
    ├─ Handlers: /start, /status, /devices, /ping
    ├─ Notification subscribers (set of chat_ids)
    └─ Event listener (subscribes to events_bus for device failures)
```

**Key Methods**:
- `start()`: initializes Bot, registers handlers, starts `dp.start_polling()`
- `stop()`: gracefully stops dispatcher
- `_setup_handlers()`: registers command and callback handlers
- `_subscribe_to_events()`: listens to `device_event_manager` for `device_failure` events, sends Telegram alerts

**Authorization**:
```python
def _get_authorized_chat_ids() -> List[int]:
    # Reads config.json → chat_id
    # Filters commands to authorized users only
```

**Integration Point**: Bot listens to backend events and pushes notifications; frontend manages bot lifecycle via `/api/bot/*` endpoints.

---

## 4. Event Streaming Pipeline

### 4.1 EventManager Architecture

**File**: [`backend/app/utils/events_bus.py`](backend/app/utils/events_bus.py)

**Core Components**:

1. **`EventManager`** (lines 15-73):
   ```python
   class EventManager:
       _subscribers: List[Callable]      # Async callbacks
       _event_history: List[Dict]        # Last 100 events (ring buffer)
       
       async def subscribe(callback):    # Add SSE client
       async def unsubscribe(callback):  # Remove disconnected client
       async def publish(event):         # Fan-out to all subscribers
       get_recent_events(limit=10):      # Historical events
   ```

2. **`DeviceEventManager`** (lines 75-135):
   ```python
   class DeviceEventManager:
       _device_states: Dict[device_id, state]
       
       async def device_status_changed():  # Emits "device_status" / "device_recovery" / "device_failure"
       async def ping_completed():         # Emits "ping_completed" with aggregate stats
   ```

3. **`SSEResponse`** (lines 142-185):
   ```python
   class SSEResponse:
       queue: asyncio.Queue   # Message queue for SSE client
       
       async def send_event():      # Formats as "data: {json}\n\n"
       async def __anext__():       # Iterator for StreamingResponse
           - Returns queued events or ": keep-alive\n\n" every 30s
   ```

**Global Singletons**:
```python
event_manager = EventManager()
device_event_manager = DeviceEventManager(event_manager)
```

### 4.2 SSE Endpoint

**File**: [`backend/app/routers/events.py`](backend/app/routers/events.py)

**Endpoint**: `GET /api/events/stream`

**Flow**:
```python
async def event_generator():
    sse_response = SSEResponse()
    await event_manager.subscribe(sse_response.send_event)  # Register callback
    
    # Send connection event + recent history
    await sse_response.send_event({"type": "connection", ...})
    for event in event_manager.get_recent_events(5):
        await sse_response.send_event(event)
    
    # Stream loop
    async for data in sse_response:
        if await request.is_disconnected(): break
        yield data  # SSE-formatted string
    
    await event_manager.unsubscribe(sse_response.send_event)  # Cleanup
```

**Response Headers**:
```python
"Content-Type": "text/event-stream",
"Cache-Control": "no-cache",
"Connection": "keep-alive",
"X-Accel-Buffering": "no"  # Nginx compatibility
```

### 4.3 Event Types

| Event Type | Source | Payload | Subscribers |
|------------|--------|---------|-------------|
| `connection` | SSE endpoint | `{status: "connected"}` | Individual SSE client |
| `device_status` | DeviceMonitor | `{device_id, ip, old_status, new_status, response_time}` | All SSE clients, Telegram bot |
| `device_recovery` | DeviceMonitor | Same as above (offline→online) | SSE + bot |
| `device_failure` | DeviceMonitor | Same as above (online→offline) | SSE + bot |
| `ping_completed` | MonitoringService | `{total_devices, online_count, offline_count, results[]}` | SSE clients |
| `monitoring_started` | MonitoringService | `{devices_count, ping_interval}` | SSE clients |
| `monitoring_stopped` | MonitoringService | `{}` | SSE clients |
| `category_created` | EventCategoryService | `{category_id, name, description}` | SSE clients |
| `category_devices_updated` | EventCategoryService | `{category_id, devices_count}` | SSE clients |

### 4.4 Buffer & History

**Recent Events Buffer**:
- Size: 100 events (configurable via `_max_history`)
- Used for: 
  - New SSE clients receive last 5 events immediately
  - `/api/events/recent?limit=10` endpoint
- Pruning: FIFO when buffer exceeds limit

---

## 5. Database Architecture

### 5.1 ORM Layer: SQLModel

**File**: [`backend/app/core/db.py`](backend/app/core/db.py)

**Engine Configuration**:
```python
engine = create_engine(
    f"sqlite:///{settings['DB_PATH']}",  # Default: shaplych_monitoring.db
    echo=settings.get('DB_ECHO', False)
)
```

**Session Management**:
```python
def get_session():
    with Session(engine) as session:
        yield session
# Used via FastAPI Depends(get_session)
```

**Table Creation**:
```python
def create_db_and_tables():
    from ..models.device import Device
    from ..models.theme import ThemePreset
    from ..models.scenario import Scenario
    from ..models.event import EventCategory, EventDevice
    
    SQLModel.metadata.create_all(engine)
```

### 5.2 Data Models

#### Device Model

**File**: [`backend/app/models/device.py`](backend/app/models/device.py)

```python
class Device(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    device_id: str = Field(index=True, unique=True)  # e.g., "H1-2"
    ip: str = Field(index=True)                      # e.g., "10.2.98.112"
    description: Optional[str]                       # e.g., "выход H1"
    category: str = Field(default="Турникет", index=True)
    status: str = Field(default="unknown", index=True)  # online/offline/error
    response_ms: Optional[int]                       # Ping latency
    last_check: Optional[datetime]                   # Last ping timestamp
    created_at: datetime
    updated_at: datetime
```

**Indexes**: `device_id`, `ip`, `category`, `status` for fast queries.

#### Event Models

**File**: [`backend/app/models/event.py`](backend/app/models/event.py)

```python
class EventCategory(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    name: str = Field(index=True)           # e.g., "Concert - Main Entrance"
    description: Optional[str]
    is_active: bool = Field(default=True)   # Monitoring enabled/disabled
    created_at: datetime
    updated_at: datetime

class EventDevice(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    event_category_id: int = Field(foreign_key="eventcategory.id")
    device_id: str                          # References Device.device_id
    is_enabled: bool = Field(default=True)  # Per-device toggle
    created_at: datetime
```

**Relationship**: Many-to-many between `EventCategory` and `Device` via `EventDevice` join table.

### 5.3 Database Files

**Current State**:
- **Primary**: `backend/shaplych_monitoring.db` (53 KB) - active database
- **Legacy**: `backend/data.db` (20 KB) - older version, possibly from migrations

**Schema Inspection** (via `setup_database.py --check`):
```
📱 Устройств в базе: 36
📋 Категорий в базе: 3
🔗 Связей устройств с категориями: 12
```

### 5.4 Initialization Script

**File**: [`backend/setup_database.py`](backend/setup_database.py)

**Usage**:
```bash
python backend/setup_database.py --init      # Create tables + seed from IP_list.json
python backend/setup_database.py --check     # Validate schema
python backend/setup_database.py --sample    # Create sample event category
```

**Key Function** (`init_devices_from_config`):
```python
def init_devices_from_config():
    # Reads IP_list.json
    # Creates Device records if not exists
    # Used for initial setup / migrations
```

**Note**: Monitoring service auto-creates missing devices during runtime, so manual DB init is optional.

---

## 6. Configuration Management

### 6.1 Configuration Files

#### IP_list.json

**Locations**: 
- **Primary**: `/IP_list.json` (root)
- **Backend Copy**: `/backend/IP_list.json`

**Format**:
```json
{
  "H1-2": ["10.2.98.112", "выход H1", "1"],
  "H2-1": ["10.2.98.113", "вход H2", "1"],
  "F1-1": ["10.2.98.134", "вход в зал E11", "0"]
}
```

**Schema**:
- Key: `device_id` (string)
- Value: `[ip_address, description, enabled_flag]`
  - `enabled_flag`: `"1"` = enabled, `"0"` = disabled

**Usage**:
- `MonitoringService._load_devices_from_config()` reads from **parent directory** (`../../IP_list.json` relative to `monitoring.py`)
- `pingApi.pingAll()` reads from backend's copy
- **Issue**: Duplication can cause inconsistencies if only one file is updated

#### config.json

**Location**: `/config.json` (root) and `/backend/config.json`

**Format**:
```json
{
  "TOKEN": "8340257712:AAGx7r2uOYe2FgkmzC1YiSpQ2z_Nrsjepf8",
  "time_connect": "50",
  "chat_id": [519434051, 329051835, 812582329]
}
```

**Fields**:
- `TOKEN`: Telegram Bot API token
- `time_connect`: Ping interval in seconds (string or int, clamped 10-300)
- `chat_id`: Authorized Telegram user/group IDs (array or single int)

**Usage**:
- `MonitoringService._load_ping_interval()`
- `TelegramBotService._load_config()`
- `Read_config.py` (legacy standalone bot)

### 6.2 Config API Endpoints

**File**: [`backend/app/routers/config.py`](backend/app/routers/config.py)

**Endpoints**:

1. `GET /api/config` - Full config dump:
   ```json
   {
     "devices": [...],
     "bot": {"token": "...", "time_connect": 50, "chat_ids": [...]},
     "total_devices": 36,
     "enabled_devices": 24
   }
   ```

2. `GET /api/config/devices` - IP_list.json as structured array:
   ```json
   {
     "devices": [
       {"device_id": "H1-2", "ip": "10.2.98.112", "description": "выход H1", "category": "Турникет", "enabled": true}
     ],
     "total": 36
   }
   ```

3. `GET /api/config/bot` - Bot config:
   ```json
   {
     "exists": true,
     "token": "...",
     "time_connect": 50,
     "chat_ids": [519434051]
   }
   ```

4. `PUT /api/config/bot` - Update bot config (writes to config.json)

**Frontend Integration**: Settings screens call these endpoints to display/edit configs without file system access.

### 6.3 Runtime Config Reload

**Monitoring Service**:
```python
# Every 5 minutes in _monitoring_loop()
if now - last_config_check > 300s:
    await _reload_configuration()
    # Re-reads IP_list.json and config.json
    # Adds/removes DeviceMonitor instances
    # Updates ping_interval
```

**Telegram Bot**:
- No auto-reload; requires restart via `/api/bot/restart` to pick up config changes

---

## 7. Legacy & Auxiliary Tooling

### 7.1 System Orchestration Script

**File**: [`start_system.py`](start_system.py)

**Purpose**: Launch all components from single command.

**Components**:
```
SystemManager.start_system()
    ├─ start_backend()    → uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ├─ start_frontend()   → npm run dev (cwd: frontend/)
    └─ start_telegram_bot() → python advanced_bot.py (optional, if TOKEN configured)
```

**Usage**:
```bash
python start_system.py                # Start all (backend + frontend + bot)
python start_system.py --no-bot       # Skip bot
python start_system.py --check-deps   # Validate dependencies only
```

**Capabilities**:
- Dependency checks (fastapi, uvicorn, npm, node_modules, config files)
- Process monitoring and auto-restart on crash
- Graceful shutdown via Ctrl+C (SIGINT/SIGTERM handlers)
- Logs to `system.log` and stdout

**Production Note**: Not intended for production; use systemd/Docker/PM2 instead.

### 7.2 Standalone Telegram Bot

**File**: [`advanced_bot.py`](advanced_bot.py) (1188 lines)

**Architecture**:
```
TurboShpalych Pro Bot
    ├─ DeviceInfo, CategoryInfo data models
    ├─ UIComponents (keyboard builders, formatters)
    ├─ MonitoringManager (wraps Ping.py)
    ├─ Handlers: /start, /status, /devices, /categories, /ping
    └─ Inline keyboards for device/category navigation
```

**Key Difference vs Backend Bot**:
- **Standalone**: Runs independently, does NOT integrate with backend's monitoring service
- **Data Source**: Reads `IP_list.json` and `config.json` directly
- **Ping Logic**: Uses `Ping.py` module (not icmplib via backend)
- **Use Case**: For environments without FastAPI backend (legacy deployment)

**Dependencies**:
```python
from Read_config import TOKEN, time_connect, chat_id
from Ping import Ping_IP
```

**Note**: When backend bot is enabled via `/api/bot/start`, running `advanced_bot.py` simultaneously causes conflicts (same TOKEN, competing pollers).

### 7.3 Legacy Ping Module

**File**: [`Ping.py`](Ping.py)

**Function**:
```python
def Ping_IP(ip: str) -> Dict:
    # Returns {"Status": "online"/"offline", "IP": ip, "Responds": response_time}
```

**Implementation**: Likely uses `icmplib` or `subprocess` ping.

**Usage**: Only used by `advanced_bot.py`, not by backend.

### 7.4 Config Reader

**File**: `Read_config.py`

**Exports**:
```python
TOKEN: str           # From config.json
time_connect: int    # Ping interval
chat_id: List[int]   # Authorized users

def read_config():   # Reloads config.json
```

**Usage**: Imported by `advanced_bot.py` for bot credentials.

---

## 8. Frontend Stack

### 8.1 Technology Stack

**Core**:
- **Framework**: Vue 3 (Composition API)
- **UI Library**: Vuetify 3
- **Build Tool**: Vite
- **State Management**: Pinia
- **HTTP Client**: ofetch (fetch wrapper)
- **Real-time**: EventSource (SSE native API)

**Key Files**:
- `frontend/src/main.ts` - App bootstrap
- `frontend/src/App.vue` - Root component
- `frontend/src/router/` - Vue Router config
- `frontend/src/plugins/vuetify.ts` - Vuetify setup

### 8.2 Pinia Store: The Central Hub

**File**: [`frontend/src/stores/pingStore.ts`](frontend/src/stores/pingStore.ts) (849 lines)

**State Domains**:

1. **Devices**:
   ```typescript
   devices: ref<Device[]>([])
   devicesLoading: ref(false)
   devicesError: ref<string | null>(null)
   ```

2. **Ping Results**:
   ```typescript
   pingLoading: ref(false)
   pingResults: ref<Map<string, any>>(new Map())
   ```

3. **Telegram Bot**:
   ```typescript
   telegramStatus: ref<TelegramStatus>({
       isRunning: false,
       botUsername: '@PingMonitorBot',
       connectedUsers: 0,
       messagesCount: 0,
       uptime: '0m'
   })
   ```

4. **Events**:
   ```typescript
   recentEvents: ref<any[]>([])
   isConnectedToEvents: ref(false)
   ```

5. **Configuration**:
   ```typescript
   configDevices: ref<DeviceConfig[]>([])
   botConfig: ref<BotConfig>({token: '', time_connect: 50, chat_ids: []})
   ```

6. **Event Categories**:
   ```typescript
   eventCategories: ref<EventCategoryWithDevices[]>([])
   availableDevices: ref<DeviceConfig[]>([])
   ```

7. **Monitoring**:
   ```typescript
   monitoringStatus: ref<any>({})
   isMonitoringActive: ref(false)
   ```

**Key Actions** (subset):

| Action | API Call | Purpose |
|--------|----------|---------|
| `loadDevices()` | `configApi.getDevicesConfig()` | Load from IP_list.json |
| `pingAllDevices()` | `pingApi.pingAll()` | Trigger batch ping |
| `connectToEventStream()` | `eventStream.connect()` | Start SSE subscription |
| `startTelegramBot()` | `telegramApi.startBot()` | Launch bot |
| `loadMonitoringStatus()` | `monitoringApi.getStatus()` | Get monitoring state |
| `loadEventCategories()` | `eventsApi.getCategories()` | Fetch event categories |

**Computed Properties**:
```typescript
deviceStats: computed(() => {
    total: devices.value.length,
    online: devices.filter(d => d.status === 'online').length,
    offline: devices.filter(d => d.status === 'offline').length,
    warning: devices.filter(d => d.status === 'warning').length
})

availabilityPercentage: computed(() => 
    Math.round((online / total) * 100)
)

averageResponseTime: computed(() => 
    Math.round(sum(response_ms) / count)
)
```

### 8.3 API Client

**File**: [`frontend/src/api/pingApi.ts`](frontend/src/api/pingApi.ts) (711 lines)

**Base Configuration**:
```typescript
const API_BASE_URL = appConfig.apiUrl  // http://127.0.0.1:8000
const apiClient = ofetch.create({
    baseURL: `${API_BASE_URL}/api`,
    headers: {'Content-Type': 'application/json'}
})
```

**API Modules**:

1. **deviceApi**: CRUD for devices
2. **pingApi**: Ping operations (`pingAll()`, `pingDevice()`, `pingIp()`)
3. **monitoringApi**: Monitoring control (`start()`, `stop()`, `pingNow()`, `reloadConfig()`)
4. **telegramApi**: Bot lifecycle (`getStatus()`, `startBot()`, `stopBot()`, `restartBot()`, `getLogs()`)
5. **configApi**: Config management (`getFullConfig()`, `getBotConfig()`, `updateBotConfig()`)
6. **eventsApi**: Event categories (`getCategories()`, `createCategory()`, `updateCategory()`, `deleteCategory()`, `updateDevices()`)

**TypeScript Interfaces**:
```typescript
interface Device {
    id?: number
    device_id: string
    ip: string
    description: string
    category: string
    status?: 'online' | 'offline' | 'warning' | 'unknown'
    response_ms?: number
    last_check?: string
}

interface EventCategoryWithDevices extends EventCategory {
    devices: EventDevice[]
    enabled_devices_count: number
    total_devices_count: number
}
```

### 8.4 SSE Client Integration

**Class**: `EventStreamClient` (lines 382-463 in `pingApi.ts`)

**Architecture**:
```typescript
class EventStreamClient {
    private eventSource: EventSource | null = null
    private listeners: Map<string, Set<(data: any) => void>>
    
    connect(): void {
        this.eventSource = new EventSource('/api/events/stream')
        this.eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data)
            this.emit(data.type, data)  // Fan-out to listeners
        }
        this.eventSource.onerror = () => {
            setTimeout(() => this.connect(), 5000)  // Auto-reconnect
        }
    }
    
    on(eventType: string, callback: (data: any) => void)
    off(eventType: string, callback: (data: any) => void)
}
```

**Usage in Store**:
```typescript
connectToEventStream() {
    eventStream.connect()
    
    eventStream.on('device_status', (event) => {
        const device = devices.value.find(d => d.device_id === event.data.device_id)
        if (device) {
            device.status = event.data.status
            device.response_ms = event.data.response_time
        }
        recentEvents.value.unshift({...event, timestamp: new Date()})
    })
    
    eventStream.on('ping_completed', (event) => {
        // Update aggregate stats
    })
}
```

**Auto-Reconnect**: 5-second backoff on connection loss.

### 8.5 View Layer Organization

**Structure**: `frontend/src/views/ping/`

| Directory | Views | Purpose |
|-----------|-------|---------|
| `dashboard/` | `PingDashboard.vue` | Main overview with device stats, charts, recent events |
| `devices/` | `DeviceList.vue`, `DeviceDetail.vue` | Device management UI |
| `events/` | `EventList.vue`, `EventCategoryManager.vue` | Event category CRUD |
| `telegram/` | `TelegramManager.vue`, `BotLogs.vue` | Bot control panel |
| `settings/` | `MonitoringSettings.vue`, `ConfigEditor.vue` | System configuration |
| `analytics/` | `AnalyticsView.vue` | Historical data & reports |

**Common Pattern**:
```vue
<script setup lang="ts">
import { usePingStore } from '@/stores/pingStore'
import { onMounted } from 'vue'

const store = usePingStore()

onMounted(async () => {
    await store.loadDevices()
    store.connectToEventStream()
})
</script>

<template>
    <v-container>
        <v-card>
            <v-card-title>Devices ({{ store.deviceStats.total }})</v-card-title>
            <v-list>
                <v-list-item v-for="device in store.devices" :key="device.id">
                    <v-chip :color="device.status === 'online' ? 'success' : 'error'">
                        {{ device.status }}
                    </v-chip>
                    {{ device.device_id }} - {{ device.ip }}
                </v-list-item>
            </v-list>
        </v-card>
    </v-container>
</template>
```

### 8.6 Composables

**Location**: `frontend/src/composables/`

**Example**: `useNotifications.ts`
```typescript
export function useNotifications() {
    function success(title: string, message: string) {
        // Vuetify snackbar/toast
    }
    
    function error(title: string, message: string) { }
    
    function deviceOnline(deviceId: string, ip: string) {
        success('Device Online', `${deviceId} (${ip}) is back online`)
    }
    
    function deviceOffline(deviceId: string, ip: string) {
        error('Device Offline', `${deviceId} (${ip}) is unreachable`)
    }
    
    return { success, error, deviceOnline, deviceOffline }
}
```

**Used by**: `pingStore.ts` for user feedback on state changes.

---

## 9. Telegram Bot Integration

### 9.1 Dual Bot Architecture

**Two Implementations**:

1. **Backend-Integrated Bot** (`backend/app/services/telegram_bot.py`):
   - **Pros**: Access to backend services, event bus, monitoring state
   - **Lifecycle**: Managed via `/api/bot/*` endpoints, controlled from frontend
   - **Data**: Direct access to SQLite DB and monitoring service

2. **Standalone Bot** (`advanced_bot.py`):
   - **Pros**: Independent deployment, no backend dependency
   - **Lifecycle**: Run as separate process (`python advanced_bot.py`)
   - **Data**: Reads IP_list.json and Ping.py directly

**Conflict Warning**: Both use same `TOKEN` from `config.json`. Running simultaneously causes:
- Telegram API errors (409 Conflict)
- Duplicate notifications
- Command interference

### 9.2 Bot Management Flow (Backend-Integrated)

**Frontend → Backend → Bot**:

```
User clicks "Start Bot" in UI
    ↓
frontend/src/stores/pingStore.ts → startTelegramBot()
    ↓
POST /api/bot/start
    ↓
backend/app/routers/bot.py → start_bot()
    ↓
services/telegram_bot.py → telegram_bot_service.start()
    ↓
    ├─ Initialize aiogram Bot with TOKEN
    ├─ Setup handlers (commands, callbacks)
    ├─ Subscribe to event_manager
    └─ Start dp.start_polling() in asyncio.Task
    ↓
Bot starts receiving Telegram updates
```

**Status Polling**:
```
Frontend Dashboard (auto-refresh every 30s)
    ↓
GET /api/bot/status
    ↓
Returns: {is_running, uptime, messages_sent, commands_processed, authorized_users}
```

### 9.3 Notification Flow

**Device Failure → Telegram Alert**:

```
MonitoringService detects device offline
    ↓
device_event_manager.device_status_changed()
    ↓
event_manager.publish({"type": "device_failure", ...})
    ↓
telegram_bot_service._event_listener() (subscribed)
    ↓
Filters: only "device_failure" or "device_recovery"
    ↓
Sends message to authorized chat_ids:
    "🔴 Устройство H1-2 (10.2.98.112) недоступно"
```

**Authorization Check**:
```python
if chat_id in self._get_authorized_chat_ids():
    await bot.send_message(chat_id, text)
```

### 9.4 Bot Commands (Backend-Integrated)

**Registered Handlers**:

| Command | Handler | Response |
|---------|---------|----------|
| `/start` | `cmd_start()` | Welcome message + main menu keyboard |
| `/status` | `cmd_status()` | Monitoring service stats (online/offline counts) |
| `/devices` | `cmd_devices()` | List all devices with status |
| `/ping` | `cmd_ping()` | Trigger immediate ping of all devices |
| `/categories` | `cmd_categories()` | List event categories |

**Example** (`/status` handler):
```python
@router.message(Command("status"))
async def cmd_status(message: types.Message):
    status = monitoring_service.get_status()
    online = sum(1 for m in status["monitors"].values() if m["current_status"] == "online")
    offline = sum(1 for m in status["monitors"].values() if m["current_status"] == "offline")
    
    await message.answer(
        f"📊 Статус системы:\n"
        f"✅ Онлайн: {online}\n"
        f"❌ Офлайн: {offline}\n"
        f"🔄 Интервал пинга: {status['ping_interval']}s"
    )
```

### 9.5 Logs Management

**Log File**: `bot.log` (root directory)

**Endpoints**:
- `GET /api/bot/logs` → Returns last 100 lines
- `DELETE /api/bot/logs` → Truncates log file

**Frontend Integration**:
```vue
<template>
    <v-btn @click="viewLogs">View Logs</v-btn>
    <v-dialog v-model="showLogs">
        <v-card>
            <v-card-text>
                <pre>{{ logs.join('\n') }}</pre>
            </v-card-text>
        </v-card>
    </v-dialog>
</template>

<script setup>
const viewLogs = async () => {
    const result = await store.getBotLogs()
    logs.value = result.logs
    showLogs.value = true
}
</script>
```

---

## 10. Data Flow Analysis

### 10.1 Device Discovery Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ Configuration Files (Root & Backend)                             │
│   IP_list.json: {"H1-2": ["10.2.98.112", "выход H1", "1"], ...} │
│   config.json: {"time_connect": "50", "chat_id": [...]}         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ (startup / every 5 min)
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ MonitoringService._load_devices_from_config()                    │
│   - Reads IP_list.json                                           │
│   - Filters enabled devices (3rd element == "1")                 │
│   - Creates/updates DeviceMonitor instances                      │
│   - Loads ping_interval from config.json                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ DeviceMonitor[] (per-device state machines)                      │
│   monitors = {"H1-2": DeviceMonitor(ip="10.2.98.112"), ...}     │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     │ (every ping_interval seconds)
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Parallel ICMP Ping (asyncio.gather)                              │
│   tasks = [monitor.ping() for monitor in monitors.values()]     │
│   results = await asyncio.gather(*tasks)                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Result Processing                                                │
│   ├─ Update Device table (status, response_ms, last_check)      │
│   ├─ Detect status changes (online ↔ offline)                   │
│   └─ Emit events to event_manager                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ EventManager.publish()                                           │
│   ├─ Fan-out to all SSE subscribers                             │
│   ├─ Fan-out to Telegram bot                                    │
│   └─ Store in event_history (ring buffer, max 100)              │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴───────────────┐
        ↓                            ↓
┌──────────────────┐      ┌──────────────────────┐
│ SSE Stream       │      │ Telegram Bot         │
│ (text/event-     │      │ (device_failure      │
│  stream)         │      │  notifications)      │
└────────┬─────────┘      └──────────────────────┘
         │
         ↓
┌─────────────────────────────────────────────────────────────────┐
│ Frontend EventStreamClient                                       │
│   eventSource.onmessage → emit(type, data)                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Pinia Store (pingStore)                                          │
│   eventStream.on('device_status', (event) => {                  │
│       devices.value[i].status = event.data.status               │
│       recentEvents.value.unshift(event)                         │
│   })                                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────────┐
│ Vue Components (Reactive Re-render)                              │
│   <DeviceCard :status="device.status" />                        │
│   <StatusChip :color="statusColor" />                           │
│   <EventFeed :events="recentEvents" />                          │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 User-Triggered Ping Flow

```
User clicks "Ping All" button in UI
    ↓
pingStore.pingAllDevices()
    ↓
POST /api/ping/all
    ↓
routers/ping.py → ping_all_devices()
    ↓
    ├─ Load IP_list.json
    ├─ Parallel ping all devices (asyncio.gather)
    ├─ Update Device table
    ├─ Publish events to event_manager
    └─ Return results: [{device_id, ip, status, response_time}, ...]
    ↓
Frontend receives response
    ↓
pingStore updates devices.value array
    ↓
UI reactively updates device cards
```

### 10.3 Event Category Monitoring Flow

```
User creates "Concert - Main Entrance" category
    ↓
Frontend: POST /api/events/categories
    ↓
EventCategoryService.create_category()
    ↓
Insert EventCategory record (is_active=True)
    ↓
User assigns devices: H1-1, H1-2, H1-3
    ↓
Frontend: PUT /api/events/categories/{id}/devices
    ↓
EventCategoryService.update_category_devices()
    ↓
    ├─ Delete old EventDevice records
    ├─ Insert new EventDevice records
    └─ Call restart_category_monitoring()
    ↓
EventCategoryService.start_category_monitoring()
    ↓
    ├─ Load enabled devices from EventDevice table
    ├─ Store in active_categories dict
    ├─ Store device_ids in category_monitors dict
    └─ Publish "category_monitoring_started" event
    ↓
MonitoringService continues pinging all devices
(EventCategoryService doesn't change ping behavior,
 just tracks which devices belong to which categories)
    ↓
User requests category stats
    ↓
GET /api/events/categories/{id}/statistics
    ↓
EventCategoryService.get_category_statistics()
    ↓
    ├─ Fetch EventDevice records for category
    ├─ Cross-reference with MonitoringService.get_status()
    ├─ Aggregate: online_count, offline_count, availability_%
    └─ Return enriched statistics
```

---

## 11. Architecture Diagrams

### 11.1 System Context Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Shaplych Monitoring System                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────┐         ┌────────────────┐         ┌─────────────┐ │
│  │   Frontend     │  HTTP   │    Backend     │  ICMP   │  Turnstile  │ │
│  │   (Vue 3 +     │◄───────►│   (FastAPI +   │◄───────►│   Devices   │ │
│  │   Vuetify)     │  SSE    │   SQLModel)    │  Ping   │  (Network)  │ │
│  │                │         │                │         │             │ │
│  │  - Dashboard   │         │  - Monitoring  │         │  10.2.98.*  │ │
│  │  - Devices     │         │  - Events      │         │             │ │
│  │  - Events      │         │  - Categories  │         │             │ │
│  │  - Telegram    │         │  - Telegram    │         │             │ │
│  │  - Settings    │         │  - Config API  │         │             │ │
│  └────────────────┘         └────────┬───────┘         └─────────────┘ │
│         ▲                             │                                 │
│         │ WebSocket/SSE               │                                 │
│         │ (Real-time events)          │                                 │
│         │                             ↓                                 │
│         │                    ┌────────────────┐                         │
│         │                    │  SQLite DB     │                         │
│         │                    │  - devices     │                         │
│         │                    │  - categories  │                         │
│         │                    │  - events      │                         │
│         │                    └────────────────┘                         │
│         │                                                                │
│         └──────────────────────────────────┐                            │
│                                            │                            │
│  ┌─────────────────────────────────────┐  │                            │
│  │      Telegram Bot (aiogram)         │  │                            │
│  │  - Commands: /start, /status, /ping │  │                            │
│  │  - Notifications: device failures   │  │                            │
│  │  - Authorization: chat_id list      │◄─┘                            │
│  └─────────────────────────────────────┘                                │
│                 ▲                                                        │
│                 │ Telegram Bot API                                      │
│                 │                                                        │
└─────────────────┼────────────────────────────────────────────────────────┘
                  │
            ┌─────┴─────┐
            │  Telegram │
            │  Platform │
            └───────────┘
```

### 11.2 Backend Component Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         backend/app/main.py                            │
│                         FastAPI Application                            │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                         Routers Layer                            │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  devices  ping  config  monitoring  events  events_api  bot      │ │
│  │     │      │      │         │         │         │         │      │ │
│  └─────┼──────┼──────┼─────────┼─────────┼─────────┼─────────┼──────┘ │
│        │      │      │         │         │         │         │        │
│        ↓      ↓      ↓         ↓         │         ↓         ↓        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                       Services Layer                             │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │ │
│  │  │ MonitoringService│  │EventCategoryServ │  │TelegramBotServ │ │ │
│  │  │                  │  │                  │  │                │ │ │
│  │  │ - DeviceMonitor[]│  │ - active_categs  │  │ - Bot (aiogram)│ │ │
│  │  │ - _monitoring_   │  │ - start/stop     │  │ - Handlers     │ │ │
│  │  │   loop()         │  │ - statistics     │  │ - Notifications│ │ │
│  │  └────────┬─────────┘  └────────┬─────────┘  └───────┬────────┘ │ │
│  │           │                     │                     │          │ │
│  └───────────┼─────────────────────┼─────────────────────┼──────────┘ │
│              │                     │                     │            │
│              └──────────┬──────────┴─────────────────────┘            │
│                         ↓                                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                  utils/events_bus.py                             │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  EventManager (pub/sub)                                          │ │
│  │    - _subscribers: List[Callable]                                │ │
│  │    - _event_history: List[Event]  (max 100)                      │ │
│  │    - publish(event) → fan-out to subscribers                     │ │
│  │                                                                   │ │
│  │  DeviceEventManager                                              │ │
│  │    - device_status_changed()                                     │ │
│  │    - ping_completed()                                            │ │
│  │                                                                   │ │
│  │  SSEResponse (per-client queue)                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                         ↓                     ↓                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                    core/db.py + models/*                         │ │
│  ├──────────────────────────────────────────────────────────────────┤ │
│  │  SQLModel ORM                                                     │ │
│  │    - Device (device_id, ip, status, response_ms, last_check)    │ │
│  │    - EventCategory (name, description, is_active)               │ │
│  │    - EventDevice (category_id, device_id, is_enabled)           │ │
│  │    - ThemePreset, Scenario                                      │ │
│  │                                                                   │ │
│  │  SQLite: shaplych_monitoring.db                                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

### 11.3 Frontend State Management Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    frontend/src/stores/pingStore.ts                 │
│                    (Pinia Store - 849 lines)                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  State                   Actions                   Computed         │
│  ─────                   ───────                   ────────         │
│  devices[]               loadDevices()             deviceStats      │
│  pingResults             pingAllDevices()          onlineDevices    │
│  telegramStatus          startTelegramBot()        offlineDevices   │
│  recentEvents            loadTelegramStatus()      availability%    │
│  configDevices           connectToEventStream()    avgResponseTime  │
│  botConfig               loadEventCategories()                      │
│  eventCategories         createCategory()                           │
│  monitoringStatus        updateCategory()                           │
│  isMonitoringActive      startMonitoring()                          │
│                          stopMonitoring()                           │
│                                                                     │
└──────┬────────────────────┬────────────────────────────────────────┘
       │                    │
       │ API Calls          │ SSE Events
       ↓                    ↓
┌─────────────────┐   ┌─────────────────────────────────────────────┐
│  api/pingApi.ts │   │   EventStreamClient (SSE)                   │
│                 │   │                                             │
│  - deviceApi    │   │   eventSource = new EventSource(           │
│  - pingApi      │   │       '/api/events/stream'                 │
│  - monitoringApi│   │   )                                         │
│  - telegramApi  │   │                                             │
│  - configApi    │   │   on('device_status', callback)            │
│  - eventsApi    │   │   on('ping_completed', callback)           │
│                 │   │   on('telegram_status', callback)          │
│                 │   │                                             │
│  (uses ofetch)  │   │   Auto-reconnect on error (5s backoff)     │
└─────────────────┘   └─────────────────────────────────────────────┘
       │                    │
       │ HTTP               │ EventSource
       ↓                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Backend FastAPI Server                           │
│                    http://127.0.0.1:8000/api                        │
└─────────────────────────────────────────────────────────────────────┘
```

### 11.4 SSE Event Flow Sequence

```
MonitoringService           EventManager          SSEResponse (Client 1)     Frontend
      │                          │                          │                    │
      │ ping_completed()         │                          │                    │
      ├─────────────────────────►│                          │                    │
      │                          │ publish(event)           │                    │
      │                          ├─────────────────────────►│                    │
      │                          │                          │ queue.put(data)    │
      │                          │                          │                    │
      │                          │ Fan-out to all SSE       │                    │
      │                          │ subscribers...           ├───────────────────►│
      │                          │                          │ "data: {json}\n\n" │
      │                          │                          │                    │
      │                          │                          │                    │ 
      │ device_status_changed()  │                          │                    │
      ├─────────────────────────►│                          │                    │
      │                          │ publish(event)           │                    │
      │                          ├─────────────────────────►│                    │
      │                          │                          ├───────────────────►│
      │                          │                          │                    │
      │                          │                          │                    │ Vue Reactive
      │                          │                          │                    │ Update
      │                          │                          │                    ├──► device.status
      │                          │                          │                    │    updated
      │                          │                          │                    │
      │                          │ (keep-alive after 30s)   │                    │
      │                          │                          ├───────────────────►│
      │                          │                          │ ": keep-alive\n\n" │
      │                          │                          │                    │
```

---

## 12. Known Issues & Technical Debt

### 12.1 Configuration Duplication

**Problem**: `IP_list.json` and `config.json` exist in both root and `backend/` directories.

**Impact**:
- Monitoring service reads from root (`../../IP_list.json`)
- Some routers may read from backend copy
- Manual syncing required for consistency

**Solution**: 
- Centralize config in one location (prefer root)
- Add symlinks or config path resolution in code
- Implement config validation API endpoint

### 12.2 Dual Database Files

**Files**:
- `backend/shaplych_monitoring.db` (active)
- `backend/data.db` (legacy)

**Issue**: Unclear which is authoritative; potential for stale data.

**Solution**: 
- Remove/archive `data.db` if obsolete
- Document migration path if both are needed

### 12.3 Telegram Bot Conflict

**Problem**: Two bot implementations (`backend/services/telegram_bot.py` and `advanced_bot.py`) use same TOKEN.

**Conflict**:
- Running both simultaneously causes Telegram API 409 errors
- Duplicate notifications to users

**Recommendations**:
- Use only one implementation per deployment
- Document when to use standalone vs backend-integrated bot
- Add startup check to prevent dual launches

### 12.4 Missing Error Recovery

**Areas**:
- SSE reconnection works, but no UI feedback during connection loss
- Monitoring service doesn't handle IP_list.json parse errors gracefully
- Bot doesn't retry failed Telegram API calls (send_message)

**Enhancements**:
- Add connection status indicator in frontend
- Implement exponential backoff for Telegram API
- Add config validation on reload

### 12.5 Hardcoded Values

**Examples**:
- Ping timeout: 3 seconds (hardcoded in `monitoring.py`)
- SSE keep-alive: 30 seconds (hardcoded in `events_bus.py`)
- Event history buffer: 100 events (hardcoded)
- Config reload interval: 300 seconds (hardcoded)

**Solution**: Move to `config.json` or environment variables.

### 12.6 Limited Test Coverage

**Current State**: No automated tests found in repository.

**Risks**:
- Regressions during refactoring
- Unclear behavior for edge cases (e.g., malformed config, network timeouts)

**Recommendations**:
- Add pytest tests for services (monitoring, event_categories)
- Add frontend unit tests (Vitest) for stores and composables
- Add integration tests for API endpoints

### 12.7 Database Schema Evolution

**Issue**: No migration strategy for schema changes.

**Current Approach**:
- `SQLModel.metadata.create_all()` creates tables if missing
- Existing tables are NOT altered

**Risk**: Adding new columns requires manual DB editing or recreating DB (data loss).

**Solution**: Integrate Alembic for migrations.

### 12.8 Security Considerations

**Concerns**:
1. **Bot Token Exposure**: `config.json` contains plaintext TOKEN (exposed in GET /api/config/bot)
2. **CORS**: Wide-open in development (all origins for `localhost:*`)
3. **No Authentication**: API endpoints have no auth (anyone on network can control bot)
4. **Telegram Chat ID**: Stored in config (static whitelist, no dynamic user management)

**Production Hardening**:
- Use environment variables for secrets
- Implement API key/JWT authentication
- Restrict CORS to specific domains
- Add user management UI for Telegram authorizations

### 12.9 Performance Bottlenecks

**Potential Issues**:
- **Large Device Count**: `asyncio.gather()` on 100+ devices may hit system limits (file descriptors, asyncio task overhead)
- **SSE Fan-out**: Every event is sent to ALL SSE clients (no filtering by subscription)
- **Database Writes**: Every ping cycle updates Device table (36 devices × 30s = 72 writes/min per monitoring service)

**Optimizations**:
- Batch database writes (1 transaction per ping cycle instead of per-device)
- Add SSE topic filtering (e.g., subscribe only to specific device events)
- Implement device pagination or chunked ping groups for large deployments

### 12.10 Frontend State Bloat

**Issue**: `pingStore.ts` is 849 lines (monolithic store handling devices, ping, telegram, events, categories, monitoring).

**Maintainability**: Hard to reason about dependencies and side effects.

**Refactor**:
- Split into domain-specific stores:
  - `useDeviceStore()` (devices, ping results)
  - `useTelegramStore()` (bot status, commands)
  - `useEventStore()` (SSE, recent events)
  - `useCategoryStore()` (event categories)
  - `useMonitoringStore()` (monitoring status, control)

---

## Conclusion

The **Shaplych Monitoring System** demonstrates a well-architected full-stack solution for real-time device monitoring with several key strengths:

✅ **Modern Tech Stack**: FastAPI + Vue 3 + SSE for performant, reactive UIs  
✅ **Asynchronous Design**: Background monitoring with asyncio, non-blocking API  
✅ **Event-Driven Architecture**: Decoupled services via pub/sub (events_bus)  
✅ **Flexible Deployment**: Standalone scripts, backend-integrated bot, config surfacing  
✅ **Rich Feature Set**: Device CRUD, categories, Telegram integration, analytics  

**Key Technical Achievements**:
- Live dashboard updates via Server-Sent Events with auto-reconnect
- Configurable monitoring intervals with hot-reload
- Event category system for context-aware device grouping
- Dual bot architecture (standalone + integrated) for deployment flexibility

**Areas for Improvement**:
- Configuration management (duplication, hardcoded values)
- Security hardening (auth, secret management)
- Test coverage (unit + integration tests)
- Database migrations (Alembic integration)
- State management refactoring (split monolithic store)

This document provides a comprehensive foundation for:
- **Onboarding new engineers** to understand system behavior
- **Planning feature additions** (understand integration points)
- **Troubleshooting production issues** (trace data flows)
- **Refactoring initiatives** (identify technical debt)

**Next Steps**:
1. Address critical issues (config duplication, bot conflicts)
2. Implement authentication/authorization for production
3. Add automated testing suite
4. Document deployment procedures (Docker, systemd, nginx)
5. Create monitoring/alerting for the monitoring system itself (meta-monitoring)

---

*For questions or clarifications, refer to source code references throughout this document or consult repository maintainers.*
