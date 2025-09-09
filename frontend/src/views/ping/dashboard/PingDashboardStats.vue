<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'

// Используем наш Pinia store
const pingStore = usePingStore()

// Получаем реактивные данные из store
const stats = computed(() => pingStore.deviceStats)
const loading = computed(() => pingStore.devicesLoading)
const availabilityPercentage = computed(() => pingStore.availabilityPercentage)

// Инициализируем store при монтировании
onMounted(async () => {
  await pingStore.initialize()
})

// Отключаемся от событий при размонтировании
onUnmounted(() => {
  pingStore.disconnectFromEventStream()
})

const statCards = computed(() => [
  {
    title: 'Всего устройств',
    value: stats.value.total,
    icon: 'tabler-devices',
    color: 'primary',
    trend: '+12%',
  },
  {
    title: 'Онлайн',
    value: stats.value.online,
    icon: 'tabler-circle-check',
    color: 'success',
    trend: '+8%',
  },
  {
    title: 'Офлайн',
    value: stats.value.offline,
    icon: 'tabler-circle-x',
    color: 'error',
    trend: '-15%',
  },
  {
    title: 'Предупреждения',
    value: stats.value.warning,
    icon: 'tabler-alert-triangle',
    color: 'warning',
    trend: '+5%',
  },
])
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon
          icon="tabler-activity"
          size="24"
        />
        Статистика устройств
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <VRow>
        <VCol
          v-for="card in statCards"
          :key="card.title"
          cols="12"
          sm="6"
          md="3"
        >
          <VCard
            :color="card.color"
            variant="tonal"
            class="text-center"
          >
            <VCardText>
              <VIcon
                :icon="card.icon"
                size="40"
                class="mb-4"
              />
              <h3 class="text-h3 mb-2">
                {{ loading ? '...' : card.value }}
              </h3>
              <p class="text-body-2 mb-2">
                {{ card.title }}
              </p>
              <VChip
                :color="card.color"
                size="small"
                variant="outlined"
              >
                {{ card.trend }}
              </VChip>
            </VCardText>
          </VCard>
        </VCol>
      </VRow>

      <!-- Доступность -->
      <VDivider class="my-6" />
      
      <div class="d-flex align-center justify-space-between">
        <div>
          <h4 class="text-h4 mb-1">
            Общая доступность
          </h4>
          <p class="text-body-2 text-medium-emphasis">
            Процент устройств онлайн
          </p>
        </div>
        <div class="text-center">
          <VProgressCircular
            :model-value="availabilityPercentage"
            :size="80"
            :width="8"
            color="success"
          >
            <span class="text-h5 font-weight-bold">{{ availabilityPercentage }}%</span>
          </VProgressCircular>
        </div>
      </div>
    </VCardText>
  </VCard>
</template>
