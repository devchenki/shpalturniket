<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'

const pingStore = usePingStore()
const notifications = useNotifications()

const loading = ref(false)
const lastUpdate = ref<Date>(new Date())

// Типизация статуса
interface BotStatus {
  botUsername?: string
  isRunning: boolean
  uptime?: string
  connectedUsers?: number
  messagesCount?: number
}
const botStatus = computed<BotStatus>(() => pingStore.telegramStatus ?? { isRunning: false })

// Универсальный обработчик ошибок
const handleError = (title: string, error: unknown, fallback = 'Произошла ошибка') => {
  console.error(title, error)
  notifications.error(title, fallback)
}

const toggleBot = async () => {
  loading.value = true
  try {
    const result = botStatus.value.isRunning
      ? await pingStore.stopTelegramBot()
      : await pingStore.startTelegramBot()

    if (result.success) {
      notifications.success(
        botStatus.value.isRunning ? 'Бот остановлен' : 'Бот запущен',
        result.message
      )
    } else {
      notifications.error('Ошибка', result.message)
    }

    await refreshStatus()
  } catch (error) {
    handleError('Ошибка управления ботом', error)
  } finally {
    loading.value = false
  }
}

const restartBot = async () => {
  loading.value = true
  try {
    const result = await pingStore.restartTelegramBot()
    result.success
      ? notifications.success('Бот перезапущен', result.message)
      : notifications.error('Ошибка перезапуска', result.message)

    await refreshStatus()
  } catch (error) {
    handleError('Ошибка перезапуска бота', error)
  } finally {
    loading.value = false
  }
}

const testMessage = () => {
  // TODO: заменить на вызов pingStore.sendTestMessage()
  notifications.info('Тест сообщения', 'Функция в разработке')
}

const refreshStatus = async () => {
  try {
    await pingStore.loadTelegramStatus()
    lastUpdate.value = new Date()
  } catch (error) {
    handleError('Ошибка обновления статуса', error)
  }
}

// Инициализация
onMounted(refreshStatus)
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon icon="tabler-robot" size="24" />
        Управление ботом
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <!-- Статус -->
      <div class="d-flex align-center justify-space-between mb-6">
        <div>
          <h6 class="text-h6 mb-1">
            {{ botStatus.botUsername ?? '@ShaplychBot' }}
          </h6>
          <p class="text-body-2 text-medium-emphasis">
            Telegram бот для уведомлений
          </p>
          <p class="text-caption text-medium-emphasis">
            Последнее обновление: {{ lastUpdate.toLocaleTimeString('ru-RU') }}
          </p>
        </div>
        <VChip
          :color="botStatus.isRunning ? 'success' : 'error'"
          :prepend-icon="botStatus.isRunning ? 'tabler-circle-check' : 'tabler-circle-x'"
          size="large"
        >
          {{ botStatus.isRunning ? 'Активен' : 'Остановлен' }}
        </VChip>
      </div>

      <!-- Статистика -->
      <VRow class="mb-6">
        <VCol cols="4" class="text-center">
          <div class="text-h4 text-primary mb-1">
            {{ botStatus.uptime ?? '—' }}
          </div>
          <div class="text-body-2 text-medium-emphasis">Статус</div>
        </VCol>
        <VCol cols="4" class="text-center">
          <div class="text-h4 text-success mb-1">
            {{ botStatus.connectedUsers ?? 0 }}
          </div>
          <div class="text-body-2 text-medium-emphasis">Пользователей</div>
        </VCol>
        <VCol cols="4" class="text-center">
          <div class="text-h4 text-info mb-1">
            {{ botStatus.messagesCount ?? 0 }}
          </div>
          <div class="text-body-2 text-medium-emphasis">Сообщений</div>
        </VCol>
      </VRow>

      <!-- Управление -->
      <div class="d-flex gap-2">
        <VBtn
          :color="botStatus.isRunning ? 'error' : 'success'"
          :prepend-icon="botStatus.isRunning ? 'tabler-player-stop' : 'tabler-player-play'"
          :loading="loading"
          :disabled="loading"
          variant="flat"
          block
          @click="toggleBot"
        >
          {{ botStatus.isRunning ? 'Остановить бота' : 'Запустить бота' }}
        </VBtn>
      </div>

      <div class="d-flex gap-2 mt-2 flex-wrap">
        <VBtn
          color="primary"
          prepend-icon="tabler-refresh"
          variant="outlined"
          size="small"
          class="flex-grow-1"
          :loading="loading"
          :disabled="loading"
          @click="restartBot"
        >
          Перезапуск
        </VBtn>
        <VBtn
          color="info"
          prepend-icon="tabler-send"
          variant="outlined"
          size="small"
          class="flex-grow-1"
          @click="testMessage"
        >
          Тест сообщения
        </VBtn>
      </div>
    </VCardText>
  </VCard>
</template>
