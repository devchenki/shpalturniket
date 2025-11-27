# Migration Guide: IP_list.json → Database

This guide documents the migration from file-based device configuration (`IP_list.json`) to database-backed configuration management.

## Overview

**What Changed:**
- Device configuration moved from `IP_list.json` to `device` table in SQLite database
- Added `enabled` field to Device model for granular control
- MonitoringService now reads from DB instead of JSON files
- Config API now returns data from DB, not filesystem
- Device CRUD operations trigger automatic monitoring config reload

**Benefits:**
- ✅ Single source of truth (no more file duplication)
- ✅ Proper CRUD API for device management
- ✅ Real-time monitoring updates when devices change
- ✅ Better scalability and concurrent access
- ✅ Alembic migrations for safe schema evolution

---

## Migration Steps

### 1. Install Alembic (Already Done)

```bash
cd backend
uv pip install alembic
```

### 2. Run Database Migration

Apply the schema migration to add `enabled` field:

```bash
cd backend
/home/engine/project/backend/.venv/bin/alembic upgrade head
```

Expected output:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 257010976e6d, add_enabled_field_to_device
```

### 3. Migrate Data from JSON to DB

**Dry-run first (recommended):**
```bash
cd backend
python migrate_config_to_db.py --dry-run
```

**Apply migration:**
```bash
python migrate_config_to_db.py
```

Expected output:
```
📈 Результаты миграции:
   Создано новых: 36
   Обновлено: 0
   Пропущено: 0

🎉 Миграция завершена успешно!
```

**Verify migration:**
```bash
python migrate_config_to_db.py --verify
```

### 4. Test the System

Start the backend and verify devices are loaded from DB:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Check logs for:
```
✅ Устройства загружены из БД: 23 активных
```

### 5. Update Frontend (Optional)

The frontend already uses `/api/devices/` endpoints, so no changes needed. However, you may want to update the UI to show the `enabled` field.

---

## API Changes

### New Device Fields

**Device Model:**
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
    enabled: boolean  // NEW FIELD
    created_at?: string
    updated_at?: string
}
```

### CRUD Endpoints

All endpoints now support the `enabled` field:

**Create Device:**
```bash
POST /api/devices/
{
    "device_id": "NEW-1",
    "ip": "10.2.98.200",
    "description": "New turnstile",
    "category": "Турникет",
    "enabled": true
}
```

**Update Device (enable/disable):**
```bash
PUT /api/devices/1
{
    "enabled": false  // Disable device
}
```

**List Devices:**
```bash
GET /api/devices/
```
Returns all devices including `enabled` field.

---

## Monitoring Service Changes

### Before (JSON-based)

```python
def _load_devices_from_config(self):
    # Read IP_list.json
    with open(ip_list_path, 'r') as f:
        ip_data = json.load(f)
    # Filter enabled devices based on 3rd element
    ...
```

### After (Database-based)

```python
def _load_devices_from_config(self):
    # Read from database
    with next(get_session()) as session:
        db_devices = session.exec(
            select(Device).where(Device.enabled == True)
        ).all()
    # Fallback to JSON if DB fails
    ...
```

**Automatic Reload:**
- When device is created/updated/deleted via API, monitoring config reloads automatically
- Config still reloads every 5 minutes (configurable)
- Fallback to `IP_list.json` if database is unavailable

---

## Backward Compatibility

### Fallback Mechanism

If the database is unavailable, the system automatically falls back to reading `IP_list.json`:

```python
try:
    devices = load_from_database()
except Exception:
    logger.warning("DB unavailable, using IP_list.json fallback")
    devices = load_from_json()
```

### Config API

`GET /api/config/devices` now reads from DB, but the response format is unchanged:

```json
{
    "devices": [
        {
            "device_id": "H1-2",
            "ip": "10.2.98.112",
            "description": "выход H1",
            "category": "Турникет",
            "enabled": true
        }
    ],
    "total": 36
}
```

---

## Rollback Plan

If you need to rollback to JSON-based configuration:

### 1. Revert MonitoringService

```bash
git revert <commit_hash>
```

### 2. Downgrade Database

```bash
cd backend
alembic downgrade -1
```

This removes the `enabled` field from the `device` table.

### 3. Restore JSON Config

If you deleted `IP_list.json`, restore it from backup or export from DB:

```python
# Export current DB to JSON
import json
from app.core.db import get_session
from app.models.device import Device
from sqlmodel import select

with next(get_session()) as session:
    devices = session.exec(select(Device)).all()
    ip_list = {}
    for device in devices:
        ip_list[device.device_id] = [
            device.ip,
            device.description or "",
            "1" if device.enabled else "0"
        ]
    
    with open("IP_list.json", "w") as f:
        json.dump(ip_list, f, ensure_ascii=False, indent=2)
```

---

## Future Enhancements

### 1. Remove JSON Files

Once confident in the migration, remove duplicate config files:

```bash
# Backup first
cp IP_list.json IP_list.json.backup
cp backend/IP_list.json backend/IP_list.json.backup

# Remove duplicates
rm IP_list.json backend/IP_list.json
```

### 2. Add Device Management UI

Create frontend screens for:
- Adding new devices
- Bulk enable/disable
- Device history/audit log
- Import/export CSV

### 3. Advanced Features

- Device grouping by location
- Scheduled enable/disable (time-based)
- Device templates for quick setup
- Batch operations

---

## Troubleshooting

### Issue: Monitoring not picking up new devices

**Solution:** Trigger manual config reload:

```bash
curl -X POST http://localhost:8000/api/monitoring/reload-config
```

### Issue: Migration script fails

**Check:**
1. Database file exists: `ls -l backend/shaplych_monitoring.db`
2. Alembic migration applied: `alembic current`
3. Models imported correctly: Check logs for import errors

**Re-run migration:**
```bash
cd backend
alembic downgrade base
alembic upgrade head
python migrate_config_to_db.py
```

### Issue: Frontend not showing enabled field

**Update TypeScript interface:**
```typescript
// src/api/pingApi.ts
export interface Device {
    // ... existing fields
    enabled: boolean  // Add this
}
```

### Issue: Device stuck in old state

**Force reload:**
```bash
# Restart backend
systemctl restart shaplych-backend

# Or via API
curl -X POST http://localhost:8000/api/monitoring/stop
curl -X POST http://localhost:8000/api/monitoring/start
```

---

## Verification Checklist

After migration, verify:

- [ ] All 36 devices loaded from DB
- [ ] 23 devices enabled, 13 disabled (matches IP_list.json)
- [ ] Monitoring service running and pinging enabled devices
- [ ] Device create/update/delete triggers config reload
- [ ] Frontend displays devices correctly
- [ ] SSE events streaming device status updates
- [ ] Telegram bot receives device failure notifications
- [ ] Alembic migrations tracked in `alembic_version` table

---

## Reference

- **Migration Script:** `backend/migrate_config_to_db.py`
- **Alembic Config:** `backend/alembic.ini`
- **Migration File:** `backend/alembic/versions/257010976e6d_add_enabled_field_to_device.py`
- **Updated Models:** `backend/app/models/device.py`
- **Updated Service:** `backend/app/services/monitoring.py`
- **Updated Router:** `backend/app/routers/devices.py`

---

## Questions?

If you encounter issues or have questions:

1. Check logs: `tail -f backend/system.log`
2. Verify DB state: `python migrate_config_to_db.py --verify`
3. Review ANALYSIS.md for architecture details
4. Open an issue on GitHub with logs and error messages
