<script setup lang="ts">
import PingTelegramControl from '@/views/ping/telegram/PingTelegramControl.vue'
import PingTelegramSettings from '@/views/ping/telegram/PingTelegramSettings.vue'
import PingTelegramLogs from '@/views/ping/telegram/PingTelegramLogs.vue'

definePage({
  meta: {
    title: 'Telegram - Ping мониторинг',
  },
})
</script>

<template>
  <VRow class="match-height">
    <!-- 👉 Управление ботом -->
    <VCol
      cols="12"
      md="6"
    >
      <PingTelegramControl />
    </VCol>

    <!-- 👉 Настройки -->
    <VCol
      cols="12"
      md="6"
    >
      <PingTelegramSettings />
    </VCol>

    <!-- 👉 Логи -->
    <VCol cols="12">
      <PingTelegramLogs />
    </VCol>
  </VRow>
</template>
