<template>
  <v-tooltip location="top">
    <template #activator="{ props }">
      <v-switch
        v-bind="props"
        :model-value="enabled"
        :loading="loading"
        :disabled="disabled || loading"
        color="success"
        density="compact"
        hide-details
        @update:model-value="handleToggle"
      >
        <template #label>
          <span class="text-caption">
            {{ enabled ? 'Вкл' : 'Выкл' }}
          </span>
        </template>
      </v-switch>
    </template>
    <span>{{ enabled ? 'Устройство включено в мониторинг' : 'Устройство отключено' }}</span>
  </v-tooltip>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  enabled: boolean
  disabled?: boolean
}

interface Emits {
  (e: 'toggle', value: boolean): void
}

const props = withDefaults(defineProps<Props>(), {
  disabled: false,
})

const emit = defineEmits<Emits>()

const loading = ref(false)

async function handleToggle(value: boolean) {
  loading.value = true
  try {
    emit('toggle', value)
  } finally {
    // Keep loading state until parent updates
    setTimeout(() => {
      loading.value = false
    }, 500)
  }
}
</script>

<style scoped>
.v-switch {
  flex: 0 0 auto;
}
</style>
