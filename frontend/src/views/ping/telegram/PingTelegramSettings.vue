<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'

const pingStore = usePingStore()
const notifications = useNotifications()

const settings = ref({
  token: '',
  whitelist: ['123456789', '987654321'],
  notifications: {
    deviceDown: true,
    deviceUp: true,
    highLatency: true,
    dailyReport: true,
  },
  thresholds: {
    latencyWarning: 500,
    latencyError: 1000,
  },
})

const newUserId = ref('')
const saving = ref(false)

// Загружаем текущие настройки при монтировании
onMounted(async () => {
  try {
    await pingStore.loadBotConfig()
    if (pingStore.botConfig) {
      settings.value.token = pingStore.botConfig.token || ''
      // Преобразуем chat_ids в whitelist
      settings.value.whitelist = pingStore.botConfig.chat_ids?.map(String) || []
    }
  } catch (error) {
    console.error('Ошибка загрузки настроек бота:', error)
  }
})

const addUser = () => {
  if (newUserId.value && !settings.value.whitelist.includes(newUserId.value)) {
    settings.value.whitelist.push(newUserId.value)
    newUserId.value = ''
  }
}

const removeUser = (userId: string) => {
  const index = settings.value.whitelist.indexOf(userId)
  if (index > -1) {
    settings.value.whitelist.splice(index, 1)
  }
}

const saveSettings = async () => {
  saving.value = true
  try {
    // Преобразуем whitelist в chat_ids (числа)
    const chatIds = settings.value.whitelist.map(id => parseInt(id)).filter(id => !isNaN(id))
    
    const botConfig = {
      token: settings.value.token,
      time_connect: 50, // Значение по умолчанию
      chat_ids: chatIds
    }
    
    await pingStore.updateBotConfig(botConfig)
    notifications.success('Настройки сохранены', 'Конфигурация Telegram бота обновлена')
  } catch (error) {
    console.error('Ошибка сохранения настроек:', error)
    notifications.error('Ошибка сохранения', 'Не удалось сохранить настройки бота')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <VCard>
    <VCardItem>
      <VCardTitle class="d-flex align-center gap-2">
        <VIcon
          icon="tabler-settings"
          size="24"
        />
        Настройки бота
      </VCardTitle>
    </VCardItem>

    <VCardText>
      <VForm @submit.prevent="saveSettings">
        <!-- Токен -->
        <VTextField
          v-model="settings.token"
          label="Токен бота"
          type="password"
          prepend-inner-icon="tabler-key"
          placeholder="1234567890:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPQQRRs"
          class="mb-4"
        />

        <!-- Белый список -->
        <div class="mb-4">
          <h6 class="text-h6 mb-3">
            Разрешенные пользователи
          </h6>
          
          <div class="d-flex gap-2 mb-3">
            <VTextField
              v-model="newUserId"
              label="User ID"
              placeholder="123456789"
              density="compact"
              hide-details
            />
            <VBtn
              color="primary"
              @click="addUser"
            >
              Добавить
            </VBtn>
          </div>

          <VChipGroup class="mb-4">
            <VChip
              v-for="userId in settings.whitelist"
              :key="userId"
              closable
              color="primary"
              variant="tonal"
              @click:close="removeUser(userId)"
            >
              {{ userId }}
            </VChip>
          </VChipGroup>
        </div>

        <!-- Уведомления -->
        <div class="mb-4">
          <h6 class="text-h6 mb-3">
            Типы уведомлений
          </h6>
          
          <VCheckbox
            v-model="settings.notifications.deviceDown"
            label="Устройство недоступно"
            color="primary"
          />
          <VCheckbox
            v-model="settings.notifications.deviceUp"
            label="Устройство восстановлено"
            color="primary"
          />
          <VCheckbox
            v-model="settings.notifications.highLatency"
            label="Высокое время отклика"
            color="primary"
          />
          <VCheckbox
            v-model="settings.notifications.dailyReport"
            label="Ежедневный отчет"
            color="primary"
          />
        </div>

        <!-- Пороговые значения -->
        <div class="mb-4">
          <h6 class="text-h6 mb-3">
            Пороговые значения
          </h6>
          
          <VTextField
            v-model.number="settings.thresholds.latencyWarning"
            label="Предупреждение (мс)"
            type="number"
            suffix="мс"
            class="mb-2"
          />
          <VTextField
            v-model.number="settings.thresholds.latencyError"
            label="Ошибка (мс)"
            type="number"
            suffix="мс"
          />
        </div>

        <!-- Кнопки -->
        <div class="d-flex gap-2">
          <VBtn
            type="submit"
            color="primary"
            prepend-icon="tabler-device-floppy"
            :loading="saving"
            :disabled="saving"
          >
            {{ saving ? 'Сохранение...' : 'Сохранить' }}
          </VBtn>
          <VBtn
            color="secondary"
            variant="outlined"
            prepend-icon="tabler-refresh"
          >
            Сбросить
          </VBtn>
        </div>
      </VForm>
    </VCardText>
  </VCard>
</template>
