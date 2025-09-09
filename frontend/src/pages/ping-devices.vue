<script setup lang="ts">
import PingDevicesTable from '@/views/ping/devices/PingDevicesTable.vue'

definePage({
  meta: {
    title: 'Устройства - Ping мониторинг',
  },
})
</script>

<template>
  <VRow>
    <VCol cols="12">
      <PingDevicesTable />
    </VCol>
  </VRow>
</template>
