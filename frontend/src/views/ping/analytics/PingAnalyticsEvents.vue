<script setup lang="ts">
import { ref } from 'vue'

const events = ref([
  {
    id: '1',
    timestamp: '2024-01-15 14:30:22',
    device: 'Сервер 1 (192.168.1.100)',
    event: 'Устройство недоступно',
    type: 'error',
    duration: '5м 23с',
  },
  {
    id: '2',
    timestamp: '2024-01-15 14:25:15',
    device: 'Роутер офис (192.168.1.1)',
    event: 'Устройство восстановлено',
    type: 'success',
    duration: '—',
  },
  {
    id: '3',
    timestamp: '2024-01-15 14:20:45',
    device: 'Принтер HP (192.168.1.50)',
    event: 'Высокое время отклика (1200ms)',
    type: 'warning',
    duration: '2м 15с',
  },
])

const headers = [
  { title: 'Время', key: 'timestamp', sortable: true },
  { title: 'Устройство', key: 'device', sortable: true },
  { title: 'Событие', key: 'event', sortable: true },
  { title: 'Тип', key: 'type', sortable: true },
  { title: 'Длительность', key: 'duration', sortable: true },
]

const getEventColor = (type: string) => {
  switch (type) {
    case 'success': return 'success'
    case 'error': return 'error'
    case 'warning': return 'warning'
    default: return 'primary'
  }
}

const getEventText = (type: string) => {
  switch (type) {
    case 'success': return 'Восстановление'
    case 'error': return 'Ошибка'
    case 'warning': return 'Предупреждение'
    default: return 'Информация'
  }
}
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle>История событий</VCardTitle>
    </VCardItem>

    <VCardText>
      <VDataTable
        :headers="headers"
        :items="events"
        items-per-page-text="Событий на странице:"
        no-data-text="События не найдены"
        class="elevation-1"
      >
        <!-- Тип события -->
        <template #item.type="{ item }">
          <VChip
            :color="getEventColor(item.type)"
            size="small"
            variant="tonal"
          >
            {{ getEventText(item.type) }}
          </VChip>
        </template>
      </VDataTable>
    </VCardText>
  </VCard>
</template>
