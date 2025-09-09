<script setup lang="ts">
import { ref } from 'vue'
import PingTelegramControl from './PingTelegramControl.vue'
import PingTelegramSettings from './PingTelegramSettings.vue'
import PingTelegramLogs from './PingTelegramLogs.vue'

const activeTab = ref('control')
</script>

<template>
  <div>
    <VRow>
      <VCol cols="12">
        <VCard>
          <VTabs
            v-model="activeTab"
            color="primary"
            align-tabs="start"
          >
            <VTab value="control">
              <VIcon
                icon="tabler-robot"
                class="me-2"
              />
              Управление
            </VTab>
            
            <VTab value="settings">
              <VIcon
                icon="tabler-settings"
                class="me-2"
              />
              Настройки
            </VTab>
            
            <VTab value="logs">
              <VIcon
                icon="tabler-file-text"
                class="me-2"
              />
              Логи бота
            </VTab>
          </VTabs>

          <VTabsWindow v-model="activeTab">
            <VTabsWindowItem value="control">
              <PingTelegramControl />
            </VTabsWindowItem>
            
            <VTabsWindowItem value="settings">
              <PingTelegramSettings />
            </VTabsWindowItem>
            
            <VTabsWindowItem value="logs">
              <PingTelegramLogs />
            </VTabsWindowItem>
          </VTabsWindow>
        </VCard>
      </VCol>
    </VRow>
  </div>
</template>
