<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'

const pingStore = usePingStore()

const logs = ref<string[]>([])
const loading = ref(false)
const autoRefresh = ref(true)
const refreshInterval = ref<NodeJS.Timeout | null>(null)

// Загрузить логи
const loadLogs = async (showLoading = false) => {
  if (showLoading) {
    loading.value = true
  }
  try {
    const result = await pingStore.getBotLogs()
    if (result.success && result.logs) {
      // Плавное обновление - добавляем только новые логи
      const newLogs = result.logs
      if (newLogs.length > logs.value.length) {
        logs.value = newLogs
      } else if (JSON.stringify(newLogs) !== JSON.stringify(logs.value)) {
        logs.value = newLogs
      }
    }
  } catch (error) {
    console.error('Ошибка загрузки логов:', error)
  } finally {
    if (showLoading) {
      loading.value = false
    }
  }
}

// Автообновление логов
const startAutoRefresh = () => {
  if (refreshInterval.value) return
  
  refreshInterval.value = setInterval(async () => {
    if (autoRefresh.value) {
      await loadLogs(false) // Не показываем загрузку при автообновлении
    }
  }, 3000) // Обновляем каждые 3 секунды
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// Очистить логи
const clearLogs = async () => {
  try {
    await pingStore.clearBotLogs()
    logs.value = []
  } catch (e) {
    // Ошибку уже показали в notifications
  }
}

// Инициализация
onMounted(async () => {
  await loadLogs(true) // Показываем загрузку при первой загрузке
  startAutoRefresh()
})

onUnmounted(() => {
  stopAutoRefresh()
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon
          icon="tabler-file-text"
          size="24"
        />
        Логи бота
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <!-- Управление -->
      <div class="d-flex gap-2 mb-4">
        <VBtn
          color="primary"
          prepend-icon="tabler-refresh"
          variant="outlined"
          size="small"
          :loading="loading"
          @click="() => loadLogs(true)"
        >
          Обновить
        </VBtn>
        
        <VBtn
          color="warning"
          prepend-icon="tabler-trash"
          variant="outlined"
          size="small"
          @click="clearLogs"
        >
          Очистить
        </VBtn>
        
        <VSpacer />
        
        <VSwitch
          v-model="autoRefresh"
          label="Автообновление"
          color="primary"
          hide-details
        />
      </div>

      <!-- Логи -->
      <VCard
        variant="outlined"
        class="logs-container"
        style="height: 400px; overflow-y: auto;"
      >
        <VCardText class="pa-2">
          <div v-if="logs.length === 0 && !loading" class="text-center text-medium-emphasis py-8">
            <VIcon
              icon="tabler-file-text"
              size="48"
              class="mb-2"
            />
            <div>Логи отсутствуют</div>
          </div>
          
          <div v-else-if="loading" class="text-center py-8">
            <VProgressCircular
              indeterminate
              color="primary"
              size="32"
            />
            <div class="mt-2">Загрузка логов...</div>
          </div>
          
          <div v-else class="logs-content">
            <div
              v-for="(log, index) in logs"
              :key="index"
              class="log-line"
              :class="{
                'log-error': log.includes('ERROR') || log.includes('❌'),
                'log-warning': log.includes('WARNING') || log.includes('⚠️'),
                'log-info': log.includes('INFO') || log.includes('✅') || log.includes('🚀'),
                'log-success': log.includes('SUCCESS') || log.includes('✅')
              }"
            >
              {{ log }}
            </div>
          </div>
        </VCardText>
      </VCard>
    </VCardText>
  </VCard>
</template>

<style scoped>
.logs-container {
  background-color: rgb(var(--v-theme-surface));
  border: 1px solid rgb(var(--v-theme-outline-variant));
}

.logs-content {
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
}

.log-line {
  padding: 2px 0;
  border-bottom: 1px solid rgba(var(--v-theme-outline), 0.1);
  word-wrap: break-word;
  white-space: pre-wrap;
}

.log-line:last-child {
  border-bottom: none;
}

.log-error {
  color: rgb(var(--v-theme-error));
  background-color: rgba(var(--v-theme-error), 0.05);
  padding: 2px 4px;
  border-radius: 2px;
}

.log-warning {
  color: rgb(var(--v-theme-warning));
  background-color: rgba(var(--v-theme-warning), 0.05);
  padding: 2px 4px;
  border-radius: 2px;
}

.log-info {
  color: rgb(var(--v-theme-info));
  background-color: rgba(var(--v-theme-info), 0.05);
  padding: 2px 4px;
  border-radius: 2px;
}

.log-success {
  color: rgb(v