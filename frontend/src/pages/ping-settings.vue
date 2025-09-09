<script setup lang="ts">
import PingSettingsGeneral from '@/views/ping/settings/PingSettingsGeneral.vue'
import PingSettingsNotifications from '@/views/ping/settings/PingSettingsNotifications.vue'
import PingSettingsThemes from '@/views/ping/settings/PingSettingsThemes.vue'
import PingSettingsAdvanced from '@/views/ping/settings/PingSettingsAdvanced.vue'

definePage({
  meta: {
    title: 'Настройки - Ping мониторинг',
  },
})

const tab = ref('general')
</script>

<template>
  <VRow>
    <VCol cols="12">
      <VCard>
        <VTabs
          v-model="tab"
          color="primary"
        >
          <VTab value="general">
            <VIcon
              icon="tabler-settings"
              class="me-2"
            />
            Общие
          </VTab>
          <VTab value="notifications">
            <VIcon
              icon="tabler-bell"
              class="me-2"
            />
            Уведомления
          </VTab>
          <VTab value="themes">
            <VIcon
              icon="tabler-palette"
              class="me-2"
            />
            Темы
          </VTab>
          <VTab value="advanced">
            <VIcon
              icon="tabler-code"
              class="me-2"
            />
            Дополнительно
          </VTab>
        </VTabs>

        <VWindow v-model="tab">
          <VWindowItem value="general">
            <PingSettingsGeneral />
          </VWindowItem>
          
          <VWindowItem value="notifications">
            <PingSettingsNotifications />
          </VWindowItem>
          
          <VWindowItem value="themes">
            <PingSettingsThemes />
          </VWindowItem>
          
          <VWindowItem value="advanced">
            <PingSettingsAdvanced />
          </VWindowItem>
        </VWindow>
      </VCard>
    </VCol>
  </VRow>
</template>
