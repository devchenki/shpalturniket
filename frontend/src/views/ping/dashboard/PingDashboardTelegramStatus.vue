<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'

const pingStore = usePingStore()

// Геттеры для данных из стора
const telegramStatus = computed(() => pingStore.telegramStatus)
const isLoading = computed(() => pingStore.telegramLoading)

// Управление запуском / остановкой бота
const toggleBot = async () => {
  if (isLoading.value) return // защита от двойного клика

  try {
    if (telegramStatus.value?.isRunning) {
      await pingStore.stopTelegramBot()
    } else {
      await pingStore.startTelegramBot()
    }
  } catch (error) {
    console.error('Ошибка переключения бота:', error)
  }
}

// Первичная загрузка статуса
onMounted(async () => {
  try {
    await pingStore.loadTelegramStatus()
  } catch (error) {
    console.error('Ошибка загрузки статуса Telegram:', error)
  }
})
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon icon="tabler-brand-telegram" size="24" />
        Telegram Бот
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <!-- Статус бота -->
      <div class="d-flex align-center justify-space-between mb-4">
        <div>
          <h6 class="text-h6 mb-1">Статус</h6>
          <p class="text-body-2 text-medium-emphasis mb-0">
            {{ isLoading ? 'Загрузка...' : telegramStatus?.botUsername || '—' }}
          </p>
        </div>
        <VChip
          :color="telegramStatus?.isRunning ? 'success' : 'error'"
          :prepend-icon="telegramStatus?.isRunning ? 'tabler-circle-check' : 'tabler-circle-x'"
          size="small"
        >
          {{ telegramStatus?.isRunning ? 'Активен' : 'Остановлен' }}
        </VChip>
      </div>

      <VDivider class="mb-4" />

      <!-- Статистика -->
      <VRow class="mb-4">
        <VCol cols="6" class="text-center">
          <div class="text-h4 text-primary mb-1">
            {{ isLoading ? '...' : telegramStatus?.connectedUsers ?? 0 }}
          </div>
          <div class="text-body-2 text-medium-emphasis">Пользователей</div>
        </VCol>
        <VCol cols="6" class="text-center">
          <div class="text-h4 text-success mb-1">
            {{ isLoading ? '...' : telegramStatus?.messagesCount ?? 0 }}
          </div>
          <div class="text-body-2 text-medium-emphasis">Сообщений</div>
        </VCol>
      </VRow>

      <!-- Последнее обновление -->
      <div class="d-flex align-center gap-2 mb-4">
        <VIcon icon="tabler-clock" size="16" class="text-medium-emphasis" />
        <span class="text-body-2 text-medium-emphasis">
          Обновлено: {{ isLoading ? '...' : telegramStatus?.lastUpdate || '—' }}
        </span>
      </div>

      <!-- Управление -->
      <div class="d-flex gap-2">
        <VBtn
          :color="telegramStatus?.isRunning ? 'error' : 'success'"
          :prepend-icon="telegramStatus?.isRunning ? 'tabler-player-stop' : 'tabler-player-play'"
          variant="tonal"
          size="small"
          block
          :loading="isLoading"
          :disabled="isLoading"
          @click="toggleBot"
        >
          {{ telegramStatus?.isRunning ? 'Остановить' : 'Запустить' }}
        </VBtn>

        <VBtn
          color="primary"
          prepend-icon="tabler-settings"
          variant="outlined"
          size="small"
          :disabled="isLoading"
          to="/ping-telegram"
        >
          Настройки
        </VBtn>
      </div>
    </VCardText>
  </VCard>
</template>
