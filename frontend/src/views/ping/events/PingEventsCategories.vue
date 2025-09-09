<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { usePingStore } from '@/stores/pingStore'
import { useNotifications } from '@/composables/useNotifications'
import type { EventCategoryCreate } from '@/api/pingApi'

const pingStore = usePingStore()
const notifications = useNotifications()

const loading = ref(false)
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const selectedCategory = ref<any>(null)

const newCategory = ref<EventCategoryCreate>({
  name: '',
  description: ''
})

const editCategory = ref<EventCategoryCreate>({
  name: '',
  description: ''
})

// Создать категорию
const createCategory = async () => {
  if (!newCategory.value.name.trim()) {
    notifications.error('Ошибка', 'Название категории обязательно')
    return
  }

  loading.value = true
  try {
    await pingStore.createEventCategory(newCategory.value)
    notifications.success('Категория создана', `Категория "${newCategory.value.name}" создана успешно`)
    showCreateDialog.value = false
    newCategory.value = { name: '', description: '' }
  } catch (error) {
    notifications.error('Ошибка создания', 'Не удалось создать категорию')
  } finally {
    loading.value = false
  }
}

// Редактировать категорию
const editCategoryStart = (category: any) => {
  selectedCategory.value = category
  editCategory.value = {
    name: category.name,
    description: category.description || ''
  }
  showEditDialog.value = true
}

const updateCategory = async () => {
  if (!editCategory.value.name.trim()) {
    notifications.error('Ошибка', 'Название категории обязательно')
    return
  }

  loading.value = true
  try {
    await pingStore.updateEventCategory(selectedCategory.value.id, editCategory.value)
    notifications.success('Категория обновлена', `Категория "${editCategory.value.name}" обновлена успешно`)
    showEditDialog.value = false
    selectedCategory.value = null
  } catch (error) {
    notifications.error('Ошибка обновления', 'Не удалось обновить категорию')
  } finally {
    loading.value = false
  }
}

// Удалить категорию
const deleteCategory = async (category: any) => {
  if (!confirm(`Вы уверены, что хотите удалить категорию "${category.name}"?`)) {
    return
  }

  loading.value = true
  try {
    await pingStore.deleteEventCategory(category.id)
    notifications.success('Категория удалена', `Категория "${category.name}" удалена успешно`)
  } catch (error) {
    notifications.error('Ошибка удаления', 'Не удалось удалить категорию')
  } finally {
    loading.value = false
  }
}

// Инициализация
onMounted(async () => {
  await pingStore.loadEventCategories()
})
</script>

<template>
  <VCardText>
    <!-- Заголовок и кнопка создания -->
    <div class="d-flex justify-space-between align-center mb-6">
      <div>
        <h6 class="text-h6 mb-1">
          Категории мероприятий
        </h6>
        <p class="text-body-2 text-medium-emphasis">
          Создавайте категории для разных мероприятий и настраивайте устройства
        </p>
      </div>
      
      <VBtn
        color="primary"
        prepend-icon="tabler-plus"
        @click="showCreateDialog = true"
      >
        Создать категорию
      </VBtn>
    </div>

    <!-- Список категорий -->
    <VRow v-if="pingStore.eventCategories.length > 0">
      <VCol
        v-for="category in pingStore.eventCategories"
        :key="category.id"
        cols="12"
        md="6"
        lg="4"
      >
        <VCard
          variant="outlined"
          class="h-100"
        >
          <VCardItem>
            <VCardTitle class="d-flex align-center justify-space-between">
              <span>{{ category.name }}</span>
              <VChip
                :color="category.is_active ? 'success' : 'error'"
                size="small"
              >
                {{ category.is_active ? 'Активна' : 'Неактивна' }}
              </VChip>
            </VCardTitle>
            
            <VCardSubtitle v-if="category.description">
              {{ category.description }}
            </VCardSubtitle>
          </VCardItem>

          <VCardText>
            <div class="d-flex justify-space-between align-center mb-3">
              <div class="text-center">
                <div class="text-h6 text-primary">
                  {{ category.enabled_devices_count }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  Включено
                </div>
              </div>
              
              <div class="text-center">
                <div class="text-h6 text-medium-emphasis">
                  {{ category.total_devices_count }}
                </div>
                <div class="text-caption text-medium-emphasis">
                  Всего
                </div>
              </div>
            </div>

            <div class="d-flex gap-2">
              <VBtn
                color="primary"
                variant="outlined"
                size="small"
                prepend-icon="tabler-edit"
                @click="editCategoryStart(category)"
              >
                Редактировать
              </VBtn>
              
              <VBtn
                color="error"
                variant="outlined"
                size="small"
                prepend-icon="tabler-trash"
                @click="deleteCategory(category)"
              >
                Удалить
              </VBtn>
            </div>
          </VCardText>
        </VCard>
      </VCol>
    </VRow>

    <!-- Пустое состояние -->
    <VCard
      v-else
      variant="outlined"
      class="text-center py-8"
    >
      <VCardText>
        <VIcon
          icon="tabler-calendar-event"
          size="64"
          class="text-medium-emphasis mb-4"
        />
        <h6 class="text-h6 mb-2">
          Нет категорий мероприятий
        </h6>
        <p class="text-body-2 text-medium-emphasis mb-4">
          Создайте первую категорию для настройки устройств под мероприятие
        </p>
        <VBtn
          color="primary"
          prepend-icon="tabler-plus"
          @click="showCreateDialog = true"
        >
          Создать категорию
        </VBtn>
      </VCardText>
    </VCard>

    <!-- Диалог создания категории -->
    <VDialog
      v-model="showCreateDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle>
          Создать категорию мероприятия
        </VCardTitle>
        
        <VCardText>
          <VTextField
            v-model="newCategory.name"
            label="Название категории"
            placeholder="Например: Конференция 2025"
            required
            class="mb-4"
          />
          
          <VTextarea
            v-model="newCategory.description"
            label="Описание"
            placeholder="Описание мероприятия..."
            rows="3"
          />
        </VCardText>
        
        <VCardActions>
          <VSpacer />
          <VBtn
            variant="outlined"
            @click="showCreateDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="primary"
            :loading="loading"
            @click="createCategory"
          >
            Создать
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>

    <!-- Диалог редактирования категории -->
    <VDialog
      v-model="showEditDialog"
      max-width="500"
    >
      <VCard>
        <VCardTitle>
          Редактировать категорию
        </VCardTitle>
        
        <VCardText>
          <VTextField
            v-model="editCategory.name"
            label="Название категории"
            required
            class="mb-4"
          />
          
          <VTextarea
            v-model="editCategory.description"
            label="Описание"
            rows="3"
          />
        </VCardText>
        
        <VCardActions>
          <VSpacer />
          <VBtn
            variant="outlined"
            @click="showEditDialog = false"
          >
            Отмена
          </VBtn>
          <VBtn
            color="primary"
            :loading="loading"
            @click="updateCategory"
          >
            Сохранить
          </VBtn>
        </VCardActions>
      </VCard>
    </VDialog>
  </VCardText>
</template>
