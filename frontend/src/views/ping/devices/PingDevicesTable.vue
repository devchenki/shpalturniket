<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { apiUtils } from '@/api/pingApi'
import type { Device } from '@/api/pingApi'

const pingStore = usePingStore()

const search = ref('')
const selectedDevices = ref<Device[]>([])

// Диалоги
const addDialog = ref(false)
const editDialog = ref(false)
const deleteDialog = ref(false)
const editingDevice = ref<Device | null>(null)

// Форма для добавления/редактирования
const deviceForm = ref<Partial<Device>>({
  device_id: '',
  ip: '',
  description: '',
  category: 'Турникет',
})

// Получаем данные из store
const devices = computed(() => pingStore.devices)
const loading = computed(() => pingStore.devicesLoading || pingStore.pingLoading)

const categories = [
  { title: 'Турникет', value: 'Турникет' },
]

const headers = [
  { title: 'ID', key: 'device_id', sortable: true },
  { title: 'IP адрес', key: 'ip', sortable: true },
  { title: 'Описание', key: 'description', sortable: true },
  { title: 'Категория', key: 'category', sortable: true },
  { title: 'Статус', key: 'status', sortable: true },
  { title: 'Отклик', key: 'response_ms', sortable: true },
  { title: 'Действия', key: 'actions', sortable: false },
]

const loadDevices = async () => {
  try {
    loading.value = true
    await pingStore.loadDevices()
  } catch (error) {
    console.error('Ошибка загрузки устройств:', error)
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status?: string) => {
  switch (status) {
    case 'online': return 'success'
    case 'offline': return 'error'
    case 'warning': return 'warning'
    default: return 'secondary'
  }
}

const getStatusText = (status?: string) => {
  switch (status) {
    case 'online': return 'Онлайн'
    case 'offline': return 'Офлайн'
    case 'warning': return 'Предупреждение'
    default: return 'Неизвестно'
  }
}

const getCategoryText = (category: string) => {
  const cat = categories.find(c => c.value === category)
  return cat?.title || category
}

const openAddDialog = () => {
  deviceForm.value = {
    device_id: '',
    ip: '',
    description: '',
    category: 'server',
  }
  addDialog.value = true
}

const openEditDialog = (device: Device) => {
  editingDevice.value = device
  deviceForm.value = { ...device }
  editDialog.value = true
}

const openDeleteDialog = (device: Device) => {
  editingDevice.value = device
  deleteDialog.value = true
}

const saveDevice = async () => {
  try {
    if (editingDevice.value) {
      await pingStore.updateDevice(editingDevice.value.id as number, deviceForm.value as any)
      editDialog.value = false
    } else {
      await pingStore.createDevice(deviceForm.value as any)
      addDialog.value = false
    }
  } catch (error) {
    console.error('Ошибка сохранения устройства:', error)
  }
}

const deleteDevice = async () => {
  try {
    if (editingDevice.value) {
      await pingStore.deleteDevice(editingDevice.value.id as number)
    }
    deleteDialog.value = false
  } catch (error) {
    console.error('Ошибка удаления устройства:', error)
  }
}

const pingDevice = async (device: Device) => {
  try {
    await pingStore.pingDevice(device.device_id)
  } catch (error) {
    console.error('Ошибка пинга:', error)
  }
}

const pingAll = async () => {
  try {
    await pingStore.pingAllDevices()
  } catch (error) {
    console.error('Ошибка пинга всех:', error)
  }
}

onMounted(loadDevices)
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon
          icon="tabler-devices"
          size="24"
        />
        Управление устройствами
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <!-- Панель действий -->
      <div class="d-flex flex-wrap gap-4 mb-6">
        <VBtn
          color="primary"
          prepend-icon="tabler-plus"
          @click="openAddDialog"
        >
          Добавить устройство
        </VBtn>
        
        <VBtn
          color="info"
          prepend-icon="tabler-activity"
          @click="pingAll"
        >
          Пинг всех
        </VBtn>
        
        <VBtn
          color="secondary"
          prepend-icon="tabler-refresh"
          @click="loadDevices"
        >
          Обновить
        </VBtn>

        <VSpacer />

        <VTextField
          v-model="search"
          prepend-inner-icon="tabler-search"
          label="Поиск устройств..."
          single-line
          hide-details
          density="compact"
          style="min-width: 250px;"
        />
      </div>

      <!-- Таблица устройств -->
      <VDataTable
        v-model="selectedDevices"
        :headers="headers"
        :items="devices"
        :search="search"
        :loading="loading"
        loading-text="Загрузка устройств..."
        no-data-text="Устройства не найдены"
        items-per-page-text="Устройств на странице:"
        show-select
        class="elevation-1"
      >
        <!-- Статус -->
        <template #item.status="{ item }">
          <VChip
            :color="getStatusColor(item.status)"
            size="small"
            variant="tonal"
          >
            {{ getStatusText(item.status) }}
          </VChip>
        </template>

        <!-- Категория -->
        <template #item.category="{ item }">
          {{ getCategoryText(item.category) }}
        </template>

        <!-- Отклик -->
        <template #item.response_ms="{ item }">
          <span v-if="item.response_ms">
            {{ item.response_ms }}ms
          </span>
          <span
            v-else
            class="text-medium-emphasis"
          >
            —
          </span>
        </template>

        <!-- Действия -->
        <template #item.actions="{ item }">
          <div class="d-flex gap-1">
            <VBtn
              icon="tabler-activity"
              size="small"
              variant="text"
              color="info"
              @click="pingDevice(item)"
            >
              <VIcon size="16" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Пинг
              </VTooltip>
            </VBtn>
            
            <VBtn
              icon="tabler-edit"
              size="small"
              variant="text"
              color="primary"
              @click="openEditDialog(item)"
            >
              <VIcon size="16" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Редактировать
              </VTooltip>
            </VBtn>
            
            <VBtn
              icon="tabler-trash"
              size="small"
              variant="text"
              color="error"
              @click="openDeleteDialog(item)"
            >
              <VIcon size="16" />
              <VTooltip
                activator="parent"
                location="top"
              >
                Удалить
              </VTooltip>
            </VBtn>
          </div>
        </template>
      </VDataTable>
    </VCardText>
  </VCard>

  <!-- Диалог добавления устройства -->
  <VDialog
    v-model="addDialog"
    max-width="500"
  >
    <VCard title="Добавить устройство">
      <VCardText>
        <VForm @submit.prevent="saveDevice">
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.device_id"
                label="ID устройства"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.ip"
                label="IP адрес"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.description"
                label="Описание"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VSelect
                v-model="deviceForm.category"
                :items="categories"
                label="Категория"
                required
              />
            </VCol>
          </VRow>
        </VForm>
      </VCardText>
      
      <VCardActions>
        <VSpacer />
        <VBtn
          color="secondary"
          @click="addDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          @click="saveDevice"
        >
          Добавить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Диалог редактирования устройства -->
  <VDialog
    v-model="editDialog"
    max-width="500"
  >
    <VCard title="Редактировать устройство">
      <VCardText>
        <VForm @submit.prevent="saveDevice">
          <VRow>
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.device_id"
                label="ID устройства"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.ip"
                label="IP адрес"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VTextField
                v-model="deviceForm.description"
                label="Описание"
                required
              />
            </VCol>
            
            <VCol cols="12">
              <VSelect
                v-model="deviceForm.category"
                :items="categories"
                label="Категория"
                required
              />
            </VCol>
          </VRow>
        </VForm>
      </VCardText>
      
      <VCardActions>
        <VSpacer />
        <VBtn
          color="secondary"
          @click="editDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="primary"
          @click="saveDevice"
        >
          Сохранить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>

  <!-- Диалог удаления устройства -->
  <VDialog
    v-model="deleteDialog"
    max-width="400"
  >
    <VCard>
      <VCardTitle>Удалить устройство?</VCardTitle>
      <VCardText>
        Вы уверены, что хотите удалить устройство 
        <strong>{{ editingDevice?.description }}</strong>?
        <br>
        Это действие нельзя отменить.
      </VCardText>
      
      <VCardActions>
        <VSpacer />
        <VBtn
          color="secondary"
          @click="deleteDialog = false"
        >
          Отмена
        </VBtn>
        <VBtn
          color="error"
          @click="deleteDevice"
        >
          Удалить
        </VBtn>
      </VCardActions>
    </VCard>
  </VDialog>
</template>
