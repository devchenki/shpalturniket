<script setup lang="ts">
import { ref } from 'vue'

const settings = ref({
  pingInterval: 60,
  timeout: 5,
  retries: 3,
  autoStart: true,
  enableLogging: true,
  logLevel: 'INFO',
  maxLogSize: 100,
})

const logLevels = [
  { title: 'DEBUG', value: 'DEBUG' },
  { title: 'INFO', value: 'INFO' },
  { title: 'WARNING', value: 'WARNING' },
  { title: 'ERROR', value: 'ERROR' },
]

const saveSettings = () => {
  // TODO: Сохранение настроек
  console.log('Сохранение общих настроек:', settings.value)
}
</script>

<template>
  <VCardText>
    <VForm @submit.prevent="saveSettings">
      <VRow>
        <!-- Интервал пинга -->
        <VCol
          cols="12"
          md="6"
        >
          <VTextField
            v-model.number="settings.pingInterval"
            label="Интервал пинга"
            type="number"
            suffix="секунд"
            min="10"
            max="3600"
          />
        </VCol>

        <!-- Таймаут -->
        <VCol
          cols="12"
          md="6"
        >
          <VTextField
            v-model.number="settings.timeout"
            label="Таймаут"
            type="number"
            suffix="секунд"
            min="1"
            max="30"
          />
        </VCol>

        <!-- Количество попыток -->
        <VCol
          cols="12"
          md="6"
        >
          <VTextField
            v-model.number="settings.retries"
            label="Количество попыток"
            type="number"
            min="1"
            max="10"
          />
        </VCol>

        <!-- Максимальный размер лога -->
        <VCol
          cols="12"
          md="6"
        >
          <VTextField
            v-model.number="settings.maxLogSize"
            label="Максимальный размер лога"
            type="number"
            suffix="МБ"
            min="10"
            max="1000"
          />
        </VCol>

        <!-- Уровень логирования -->
        <VCol
          cols="12"
          md="6"
        >
          <VSelect
            v-model="settings.logLevel"
            :items="logLevels"
            label="Уровень логирования"
          />
        </VCol>

        <!-- Переключатели -->
        <VCol cols="12">
          <VCheckbox
            v-model="settings.autoStart"
            label="Автозапуск при старте системы"
            color="primary"
          />
          <VCheckbox
            v-model="settings.enableLogging"
            label="Включить логирование"
            color="primary"
          />
        </VCol>

        <!-- Кнопки -->
        <VCol cols="12">
          <div class="d-flex gap-2">
            <VBtn
              type="submit"
              color="primary"
              prepend-icon="tabler-device-floppy"
            >
              Сохранить настройки
            </VBtn>
            <VBtn
              color="secondary"
              variant="outlined"
              prepend-icon="tabler-refresh"
            >
              Сбросить по умолчанию
            </VBtn>
          </div>
        </VCol>
      </VRow>
    </VForm>
  </VCardText>
</template>
