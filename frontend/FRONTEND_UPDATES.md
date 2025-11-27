# Frontend Updates - Device Enable/Disable Feature

## Обзор изменений

Добавлена поддержка включения/выключения устройств на фронтенде в соответствии с бэкенд миграцией.

---

## Изменённые файлы

### 1. `src/api/pingApi.ts`

**Обновлён интерфейс Device:**
```typescript
export interface Device {
  id?: number
  device_id: string
  ip: string
  description: string
  category: string
  status?: 'online' | 'offline' | 'warning' | 'unknown'
  response_ms?: number
  last_check?: string
  enabled?: boolean        // ✅ NEW
  created_at?: string      // ✅ NEW
  updated_at?: string      // ✅ NEW
}
```

### 2. `src/stores/pingStore.ts`

**Добавлены computed свойства:**
```typescript
const enabledDevices = computed(() => 
  devices.value.filter(d => d.enabled !== false)
)

const disabledDevices = computed(() => 
  devices.value.filter(d => d.enabled === false)
)
```

**Добавлен метод переключения:**
```typescript
async function toggleDeviceEnabled(id: number, enabled: boolean) {
  const updatedDevice = await updateDevice(id, { enabled })
  notifications.success(
    enabled ? 'Устройство включено' : 'Устройство выключено',
    `${updatedDevice.device_id} ${enabled ? 'включено в мониторинг' : 'исключено из мониторинга'}`
  )
  return updatedDevice
}
```

### 3. `src/components/DeviceToggle.vue` (Новый)

Компонент для переключения enabled:
```vue
<DeviceToggle
  :enabled="device.enabled ?? true"
  @toggle="(value) => store.toggleDeviceEnabled(device.id, value)"
/>
```

**Props:**
- `enabled: boolean` - текущее состояние
- `disabled?: boolean` - заблокировать переключение

**Events:**
- `@toggle="(value: boolean) => void"` - срабатывает при клике

**Features:**
- Визуальное отображение состояния (Вкл/Выкл)
- Loading state при переключении
- Tooltip с подсказкой
- Компактный дизайн для таблиц

---

## Как использовать

### В компонентах списков устройств

```vue
<template>
  <v-data-table :items="store.devices" :headers="headers">
    <!-- ... другие колонки ... -->
    
    <template #item.enabled="{ item }">
      <DeviceToggle
        :enabled="item.enabled ?? true"
        @toggle="(value) => handleToggle(item, value)"
      />
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
import { usePingStore } from '@/stores/pingStore'
import DeviceToggle from '@/components/DeviceToggle.vue'

const store = usePingStore()

async function handleToggle(device: Device, enabled: boolean) {
  await store.toggleDeviceEnabled(device.id!, enabled)
}
</script>
```

### Фильтрация по enabled

```vue
<template>
  <v-tabs v-model="tab">
    <v-tab value="all">Все ({{ store.devices.length }})</v-tab>
    <v-tab value="enabled">Включенные ({{ store.enabledDevices.length }})</v-tab>
    <v-tab value="disabled">Выключенные ({{ store.disabledDevices.length }})</v-tab>
  </v-tabs>

  <v-window v-model="tab">
    <v-window-item value="all">
      <DeviceList :devices="store.devices" />
    </v-window-item>
    <v-window-item value="enabled">
      <DeviceList :devices="store.enabledDevices" />
    </v-window-item>
    <v-window-item value="disabled">
      <DeviceList :devices="store.disabledDevices" />
    </v-window-item>
  </v-window>
</template>
```

### Bulk операции

```vue
<template>
  <v-btn @click="enableAll">Включить все</v-btn>
  <v-btn @click="disableSelected">Выключить выбранные</v-btn>
</template>

<script setup lang="ts">
const store = usePingStore()
const selected = ref<Device[]>([])

async function enableAll() {
  for (const device of store.disabledDevices) {
    await store.toggleDeviceEnabled(device.id!, true)
  }
}

async function disableSelected() {
  for (const device of selected.value) {
    await store.toggleDeviceEnabled(device.id!, false)
  }
}
</script>
```

---

## Визуальные индикаторы

### Бейджи статуса

```vue
<v-chip
  v-if="!device.enabled"
  color="grey"
  size="small"
  variant="flat"
>
  Отключено
</v-chip>
```

### Иконки

```vue
<v-icon
  :icon="device.enabled ? 'mdi-power' : 'mdi-power-off'"
  :color="device.enabled ? 'success' : 'grey'"
/>
```

### Затемнение отключённых устройств

```vue
<v-list-item
  :class="{ 'opacity-50': !device.enabled }"
  :disabled="!device.enabled"
>
  <template #prepend>
    <v-icon 
      :icon="device.enabled ? 'mdi-check-circle' : 'mdi-minus-circle'"
      :color="device.enabled ? 'success' : 'grey'"
    />
  </template>
  
  <v-list-item-title>{{ device.device_id }}</v-list-item-title>
  <v-list-item-subtitle>
    {{ device.ip }} - {{ device.enabled ? 'Включено' : 'Выключено' }}
  </v-list-item-subtitle>
</v-list-item>
```

---

## Интеграция в существующие views

### `/src/views/ping/devices/DeviceList.vue`

Добавить колонку "Enabled" в таблицу:

```typescript
const headers = [
  { title: 'Device ID', key: 'device_id' },
  { title: 'IP', key: 'ip' },
  { title: 'Description', key: 'description' },
  { title: 'Status', key: 'status' },
  { title: 'Enabled', key: 'enabled', sortable: true },  // ✅ ADD THIS
  { title: 'Actions', key: 'actions', sortable: false },
]
```

### `/src/views/ping/dashboard/PingDashboard.vue`

Добавить статистику по enabled/disabled:

```vue
<v-row>
  <v-col cols="12" md="3">
    <v-card>
      <v-card-text>
        <div class="text-h4">{{ store.enabledDevices.length }}</div>
        <div class="text-caption">Устройств включено</div>
      </v-card-text>
    </v-card>
  </v-col>
  <v-col cols="12" md="3">
    <v-card>
      <v-card-text>
        <div class="text-h4">{{ store.disabledDevices.length }}</div>
        <div class="text-caption">Устройств выключено</div>
      </v-card-text>
    </v-card>
  </v-col>
</v-row>
```

---

## Обратная совместимость

Все изменения обратно совместимы:
- `enabled` помечен как `optional` (может быть `undefined`)
- По умолчанию считается `true` если не указано
- Старые устройства без поля `enabled` работают как раньше

---

## Testing Checklist

- [ ] Загрузка устройств отображает `enabled` корректно
- [ ] Toggle переключает устройство и обновляет UI
- [ ] Отключённое устройство исчезает из мониторинга
- [ ] Включённое устройство появляется в мониторинге
- [ ] Фильтры enabled/disabled работают
- [ ] Bulk операции работают корректно
- [ ] Notifications отображаются при toggle
- [ ] Loading state отображается правильно

---

## Next Steps

### Рекомендуемые улучшения:

1. **Bulk Enable/Disable UI**
   - Чекбоксы для выбора нескольких устройств
   - Кнопки "Включить выбранные" / "Выключить выбранные"

2. **Advanced Filters**
   ```vue
   <v-select
     v-model="filter"
     :items="['all', 'enabled', 'disabled', 'online', 'offline']"
     label="Фильтр"
   />
   ```

3. **Device Groups**
   - Группировка устройств по enabled/disabled
   - Expandable sections

4. **History Log**
   - История включений/выключений устройств
   - Кто и когда изменил статус

5. **Schedule Enable/Disable**
   - Планирование включения/выключения по расписанию
   - Временные окна мониторинга

---

## API Endpoints Used

```typescript
// Create device with enabled
POST /api/devices/
{
  "device_id": "NEW-1",
  "ip": "10.2.98.200",
  "description": "New device",
  "category": "Турникет",
  "enabled": true
}

// Update enabled status
PUT /api/devices/1
{
  "enabled": false
}

// Get devices (includes enabled field)
GET /api/devices/
```

---

## Примеры использования

### Пример 1: Простой список с toggle

```vue
<template>
  <v-list>
    <v-list-item
      v-for="device in store.devices"
      :key="device.id"
    >
      <v-list-item-title>{{ device.device_id }}</v-list-item-title>
      
      <template #append>
        <DeviceToggle
          :enabled="device.enabled ?? true"
          @toggle="(val) => store.toggleDeviceEnabled(device.id!, val)"
        />
      </template>
    </v-list-item>
  </v-list>
</template>
```

### Пример 2: Карточки устройств с индикатором

```vue
<template>
  <v-row>
    <v-col
      v-for="device in store.devices"
      :key="device.id"
      cols="12"
      md="4"
    >
      <v-card :class="{ 'opacity-50': !device.enabled }">
        <v-card-title>
          {{ device.device_id }}
          <v-chip
            v-if="!device.enabled"
            color="grey"
            size="small"
            class="ml-2"
          >
            Выкл
          </v-chip>
        </v-card-title>
        
        <v-card-text>
          <div>IP: {{ device.ip }}</div>
          <div>Status: {{ device.status }}</div>
        </v-card-text>
        
        <v-card-actions>
          <DeviceToggle
            :enabled="device.enabled ?? true"
            @toggle="(val) => store.toggleDeviceEnabled(device.id!, val)"
          />
        </v-card-actions>
      </v-card>
    </v-col>
  </v-row>
</template>
```

### Пример 3: Таблица с сортировкой

```vue
<template>
  <v-data-table
    :items="store.devices"
    :headers="headers"
    :sort-by="[{ key: 'enabled', order: 'desc' }]"
  >
    <template #item.enabled="{ item }">
      <DeviceToggle
        :enabled="item.enabled ?? true"
        @toggle="(val) => store.toggleDeviceEnabled(item.id!, val)"
      />
    </template>
    
    <template #item.device_id="{ item }">
      <div class="d-flex align-center">
        <v-icon
          :icon="item.enabled ? 'mdi-check-circle' : 'mdi-minus-circle'"
          :color="item.enabled ? 'success' : 'grey'"
          size="small"
          class="mr-2"
        />
        {{ item.device_id }}
      </div>
    </template>
  </v-data-table>
</template>

<script setup lang="ts">
const headers = [
  { title: 'Device', key: 'device_id' },
  { title: 'IP', key: 'ip' },
  { title: 'Status', key: 'status' },
  { title: 'Response', key: 'response_ms' },
  { title: 'Enabled', key: 'enabled', align: 'center' },
]
</script>
```

---

## Troubleshooting

### Issue: Toggle не работает

**Solution:** Проверьте что `device.id` не undefined:
```typescript
if (!device.id) {
  console.error('Device ID is missing')
  return
}
```

### Issue: Устройство не исчезает из мониторинга

**Solution:** Мониторинг автоматически перезагружается, но может занять до 5 минут. Для немедленного обновления:
```typescript
await store.reloadMonitoringConfig()
```

### Issue: Notifications не отображаются

**Solution:** Убедитесь что `useNotifications` composable правильно настроен:
```typescript
import { useNotifications } from '@/composables/useNotifications'
const notifications = useNotifications()
```
