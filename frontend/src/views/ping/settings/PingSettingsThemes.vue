<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTheme } from 'vuetify'
import { useConfigStore } from '@core/stores/config'
import { cookieRef } from '@layouts/stores/config'
import { useNotifications } from '@/composables/useNotifications'

const theme = useTheme()
const configStore = useConfigStore()
const notifications = useNotifications()

// Состояния
const primaryColor = ref('#7367F0')
const themeMode = ref<'light' | 'dark' | 'system'>('system')
const customColors = ref({
  success: '#28C76F',
  error: '#FF4C51',
  warning: '#FF9F43',
  info: '#00BAD1',
})

// Пресеты Vuexy + кастомные
const colorPresets = [
  { name: 'Деловая', primary: '#2563eb', success: '#059669', error: '#dc2626', warning: '#d97706', info: '#0891b2' },
  { name: 'Классическая', primary: '#1976d2', success: '#4caf50', error: '#f44336', warning: '#ff9800', info: '#2196f3' },
  { name: 'Современная', primary: '#6366f1', success: '#10b981', error: '#ef4444', warning: '#f59e0b', info: '#06b6d4' },
  { name: 'Монохромная', primary: '#374151', success: '#374151', error: '#374151', warning: '#374151', info: '#374151' },
  { name: 'Vuexy Default', primary: '#7367F0', success: '#28C76F', error: '#FF4C51', warning: '#FF9F43', info: '#00BAD1' },
]

// Инициализация
onMounted(() => {
  themeMode.value = configStore.theme
  const currentTheme = theme.current.value
  primaryColor.value = currentTheme.colors.primary
  customColors.value = {
    success: currentTheme.colors.success,
    error: currentTheme.colors.error,
    warning: currentTheme.colors.warning,
    info: currentTheme.colors.info,
  }
})

// Применение пресета
const applyColorScheme = (preset: typeof colorPresets[0]) => {
  primaryColor.value = preset.primary
  customColors.value = {
    success: preset.success,
    error: preset.error,
    warning: preset.warning,
    info: preset.info,
  }
  updateTheme()
  notifications.info('Цветовая схема', `Применена схема "${preset.name}"`)
}

// Переключение темы
const setThemeMode = (mode: 'light' | 'dark' | 'system') => {
  themeMode.value = mode
  configStore.theme = mode

  if (mode !== 'system') {
    theme.global.name.value = mode
  }

  const labels: Record<typeof mode, string> = {
    light: 'Светлая',
    dark: 'Тёмная',
    system: 'Системная',
  }

  notifications.success('Тема изменена', `Выбрана ${labels[mode]} тема`)
}

// Обновление темы
const updateTheme = () => {
  const currentTheme = theme.global.name.value
  const colors = theme.themes.value[currentTheme].colors

  colors.primary = primaryColor.value
  colors['primary-darken-1'] = getDarkenColor(primaryColor.value)

  colors.success = customColors.value.success
  colors.error = customColors.value.error
  colors.warning = customColors.value.warning
  colors.info = customColors.value.info

  cookieRef(`${currentTheme}ThemePrimaryColor`, null).value = primaryColor.value
  cookieRef(`${currentTheme}ThemePrimaryDarkenColor`, null).value = getDarkenColor(primaryColor.value)

  notifications.info('Цвета обновлены', 'Новая палитра применена')
}

// Генерация затемнённого оттенка
const getDarkenColor = (color: string): string => {
  const hex = color.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  const darken = (val: number) => Math.max(0, Math.floor(val * 0.8))

  return `#${darken(r).toString(16).padStart(2, '0')}${darken(g).toString(16).padStart(2, '0')}${darken(b).toString(16).padStart(2, '0')}`
}

// Сброс
const resetToDefaults = () => {
  primaryColor.value = '#7367F0'
  themeMode.value = 'system'
  customColors.value = {
    success: '#28C76F',
    error: '#FF4C51',
    warning: '#FF9F43',
    info: '#00BAD1',
  }
  setThemeMode('system')
  updateTheme()
  notifications.info('Сброс настроек', 'Значения восстановлены по умолчанию')
}

// Сохранение
const saveSettings = () => {
  updateTheme()
  notifications.success('Настройки сохранены', 'Тема и цвета успешно применены')
}
</script>

<template>
  <VCardText>
    <VRow>
      <!-- Пресеты -->
      <VCol cols="12">
        <h4 class="text-h5 mb-4">Цветовые схемы</h4>
        <VRow>
          <VCol
            v-for="preset in colorPresets"
            :key="preset.name"
            cols="12"
            sm="6"
            md="4"
            lg="2"
          >
            <VCard
              class="preset-card"
              :class="{ 'preset-active': primaryColor === preset.primary }"
              @click="applyColorScheme(preset)"
            >
              <VCardText class="text-center pa-3">
                <div class="d-flex justify-center gap-1 mb-2">
                  <div
                    v-for="(val, key) in [preset.primary, preset.success, preset.error, preset.warning]"
                    :key="key"
                    class="color-dot"
                    :style="{ backgroundColor: val }"
                  />
                </div>
                <h6 class="text-subtitle-2">{{ preset.name }}</h6>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VCol>

      <!-- Тема -->
      <VCol cols="12">
        <VDivider class="my-4" />
        <h4 class="text-h5 mb-4">Режим отображения</h4>
        <VRow>
          <VCol
            v-for="mode in [
              { value: 'light', label: 'Светлая', icon: 'tabler-sun', desc: 'Всегда светлая' },
              { value: 'dark', label: 'Тёмная', icon: 'tabler-moon-stars', desc: 'Всегда тёмная' },
              { value: 'system', label: 'Системная', icon: 'tabler-device-desktop-analytics', desc: 'Следует настройкам ОС' },
            ]"
            :key="mode.value"
            cols="12"
            sm="4"
          >
            <VCard
              class="theme-mode-card"
              :class="{ 'theme-mode-active': themeMode === mode.value }"
              @click="setThemeMode(mode.value)"
            >
              <VCardText class="text-center pa-4">
                <VIcon
                  :icon="mode.icon"
                  size="32"
                  class="mb-3"
                  :color="themeMode === mode.value ? 'primary' : undefined"
                />
                <h6 class="text-subtitle-1 mb-1">{{ mode.label }}</h6>
                <p class="text-body-2 text-medium-emphasis mb-0">{{ mode.desc }}</p>
              </VCardText>
            </VCard>
          </VCol>
        </VRow>
      </VCol>

      <!-- Кастомные цвета -->
      <VCol cols="12">
        <VDivider class="my-4" />
        <h4 class="text-h5 mb-4">Кастомные цвета</h4>
        <VRow>
          <VCol
            v-for="(val, key) in customColors"
            :key="key"
            cols="12"
            sm="6"
            md="3"
          >
            <VTextField
              v-model="customColors[key]"
              :label="`Цвет ${key}`"
              type="color"
              @update:model-value="updateTheme"
            />
          </VCol>
        </VRow>
      </VCol>

      <!-- Действия -->
      <VCol cols="12">
        <VDivider class="my-4" />
        <div class="d-flex gap-3">
          <VBtn color="primary" @click="saveSettings">
            <VIcon icon="tabler-device-floppy" class="me-2" /> Сохранить
          </VBtn>
          <VBtn variant="outlined" @click="resetToDefaults">
            <VIcon icon="tabler-refresh" class="me-2" /> Сбросить
          </VBtn>
        </div>
      </VCol>
    </VRow>
  </VCardText>
</template>

<style scoped>
.color-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
}

.preset-card,
.theme-mode-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border: 2px solid transparent;
}

.preset-card:hover,
.theme-mode-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.preset-active,
.theme-mode-active {
  border-color: rgb(var(--v-theme-primary));
  box-shadow: 0 0 0 1px rgb(var(--v-theme-primary));
  background: rgba(var(--v-theme-primary), 0.05);
}
</style>
