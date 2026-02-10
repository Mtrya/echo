<template>
  <div class="home-page">
    <div class="button-column">
      <!-- Settings Button -->
      <button @click="$emit('open-settings')" class="btn btn-secondary" :class="{ 'btn-warning': !hasApiKey }">⚙️ {{ translate('home.settings') }}</button>

      <!-- File Converter Button -->
      <button @click="openFileConverter" class="btn btn-secondary" :disabled="!hasApiKey" :title="!hasApiKey ? translate('home.apiRequired') : ''">
        📁 {{ translate('home.createExam') }}
      </button>

      <!-- Exam Selection -->
      <button @click="handleExamListClick" class="btn btn-primary" :disabled="!hasApiKey" :title="!hasApiKey ? translate('home.apiRequired') : ''">
        📋 {{ translate('home.selectExam') }}
      </button>

      <!-- Start Exam -->
      <button @click="startExam" class="btn btn-primary" :disabled="!hasApiKey || !selectedExam" :title="!hasApiKey ? translate('home.apiRequired') : !selectedExam ? translate('home.selectExamFirst') : ''">
        <span v-if="selectedExam">
          🚀 {{ translate('home.startExam') }}: <span class="exam-name-text">{{ selectedExam }}</span>
        </span>
        <span v-else>
          🚀 {{ translate('home.startExam') }}
        </span>
      </button>
    </div>

    <!-- Exam Selection Modal -->
    <div v-if="showExamList" class="modal-overlay" @click="showExamList = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ translate('home.selectExamTitle') }}</h3>
          <label class="toggle-container">
            <input type="checkbox" v-model="showCompletedExams" @change="handleToggleChange">
            <span class="toggle-slider"></span>
            <span class="toggle-label">{{ translate('home.showCompleted') }}</span>
          </label>
        </div>
        <div class="exam-list">
          <div
            v-for="exam in availableExams"
            :key="exam"
            class="exam-item"
            :class="{
              selected: selectedExam === exam,
              completed: completedExams.includes(exam)
            }"
            @click="selectExam(exam)"
          >
            <span class="exam-name">{{ exam }}</span>
            <span v-if="completedExams.includes(exam)" class="completed-badge">✓</span>
          </div>
        </div>
        <button @click="showExamList = false" class="btn btn-secondary">{{ translate('home.close') }}</button>
      </div>
    </div>

    <!-- Alert Modal -->
    <div v-if="showAlert" class="modal-overlay" @click="showAlert = false">
      <div class="modal-content alert-content" @click.stop>
        <p>{{ alertMessage }}</p>
        <button @click="showAlert = false" class="btn btn-primary">{{ translate('common.ok') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTranslations } from '@/composables/useTranslations'
import { apiUrl } from '@/utils/api'

// Emits definition
const emit = defineEmits<{
  'start-exam': [data: { sessionId: string; examName: string }]
  'file-converter': []
  'open-settings': []
}>()

// Translation support
const { translate } = useTranslations()

// State management with proper types
const showExamList = ref<boolean>(false)
const showAlert = ref<boolean>(false)
const alertMessage = ref<string>('')
const selectedExam = ref<string | null>(null)
const availableExams = ref<string[]>([])
const completedExams = ref<string[]>([])
const showCompletedExams = ref<boolean>(false)
const hasApiKey = ref<boolean>(false)

// Load available exams and check API key when component mounts
onMounted(async () => {
  await checkApiKeyStatus()
  await loadCompletedExams()
  await loadExams()
})

// Check API key status
const checkApiKeyStatus = async (): Promise<void> => {
  try {
    const response = await fetch(apiUrl('/api-key-status'))
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    const data = await response.json()
    hasApiKey.value = data.has_api_key
  } catch (error) {
    console.error('Failed to check API key status:', error)
    hasApiKey.value = false
    // Don't show alert for this error - it's expected when backend isn't running
  }
}

// Refresh API key status (exposed to parent)
const refreshApiKeyStatus = async (): Promise<void> => {
  await checkApiKeyStatus()
}

// Handle toggle change event
const handleToggleChange = async (): Promise<void> => {
  await loadExams()
}

// Load completed exams
const loadCompletedExams = async (): Promise<void> => {
  try {
    const response = await fetch(apiUrl('/exams/completed'))
    const data = await response.json()
    completedExams.value = data.completed_exams || []
  } catch (error) {
    console.error('Failed to load completed exams:', error)
    completedExams.value = []
  }
}

// API call to get exam list
const loadExams = async (): Promise<void> => {
  try {
    const includeCompleted = showCompletedExams.value
    const response = await fetch(apiUrl(`/exams/list?include_completed=${includeCompleted}`))
    const data = await response.json()
    availableExams.value = data.exams || []
  } catch (error) {
    console.error('Failed to load exams:', error)
    showAlert.value = true
    alertMessage.value = 'Failed to load exam list'
  }
}

// Select an exam from the list
const selectExam = (exam: string): void => {
  selectedExam.value = exam
  showExamList.value = false
}

// Open file converter
const openFileConverter = (): void => {
  if (!hasApiKey.value) {
    showAlert.value = true
    alertMessage.value = 'Please configure API key in settings first!'
    return
  }
  emit('file-converter')
}

// Handle exam list button click
const handleExamListClick = (): void => {
  if (!hasApiKey.value) {
    showAlert.value = true
    alertMessage.value = 'Please configure API key in settings first!'
    return
  }
  showExamList.value = true
}

// Start the exam
const startExam = async (): Promise<void> => {
  if (!selectedExam.value) {
    showAlert.value = true
    alertMessage.value = 'Please select an exam first!'
    return
  }

  if (!hasApiKey.value) {
    showAlert.value = true
    alertMessage.value = 'Please configure API key in settings first!'
    return
  }

  try {
    const response = await fetch(apiUrl('/session/start'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        exam_file_path: selectedExam.value
      })
    })

    const data = await response.json()

    if (data.session_id) {
      // Emit event to parent component with session data
      emit('start-exam', {
        sessionId: data.session_id,
        examName: selectedExam.value
      })
    } else {
      showAlert.value = true
      alertMessage.value = 'Failed to start exam session'
    }
  } catch (error) {
    console.error('Failed to start exam:', error)
    showAlert.value = true
    alertMessage.value = 'Failed to start exam session'
  }
}

// Expose refreshApiKeyStatus to parent component
defineExpose({
  refreshApiKeyStatus
})
</script>

<style scoped>
.home-page {
  width: 100%;
  max-width: 450px;
}

.button-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.selected-display {
  background: rgba(255, 255, 255, 0.9);
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  color: #16a34a;
  font-weight: 600;
  border: 2px solid #16a34a;
}

/* Button Styles */
.btn {
  padding: 1rem 1.5rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  text-align: left;
  white-space: normal;
  word-wrap: break-word;
  min-height: 60px;
  display: flex;
  align-items: center;
}

.exam-name-text {
  font-size: 0.9rem;
  opacity: 0.9;
  margin-left: 4px;
}

.btn-primary {
  background: #16a34a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #15803d;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  background: #9ca3af;
  color: #6b7280;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #16a34a;
  border: 2px solid #16a34a;
}

.btn-secondary:hover:not(:disabled) {
  background: white;
  transform: translateY(-2px);
}

.btn-secondary:disabled {
  background: #9ca3af;
  color: #6b7280;
  cursor: not-allowed;
  border-color: #9ca3af;
  transform: none;
}

.btn-warning {
  background: #f59e0b !important;
  color: white !important;
  border-color: #d97706 !important;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0.7);
  }
  70% {
    box-shadow: 0 0 0 10px rgba(245, 158, 11, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(245, 158, 11, 0);
  }
}

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  color: #16a34a;
  text-align: center;
}

/* Exam List Styles */
.exam-list {
  max-height: 300px;
  overflow-y: auto;
  margin: 1rem 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.exam-item {
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.exam-item:hover {
  background: #f3f4f6;
}

.exam-item.selected {
  background: #dcfce7;
  color: #16a34a;
  font-weight: 600;
}

.exam-item:last-child {
  border-bottom: none;
}

.exam-item.completed {
  opacity: 0.6;
  background: #f9fafb;
}

.exam-name {
  flex: 1;
}

.completed-badge {
  color: #16a34a;
  font-weight: bold;
  font-size: 1.2rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

/* Toggle Switch Styles */
.toggle-container {
  display: flex;
  align-items: center;
  cursor: pointer;
  user-select: none;
}

.toggle-container input[type="checkbox"] {
  display: none;
}

.toggle-slider {
  position: relative;
  width: 44px;
  height: 24px;
  background-color: #ccc;
  border-radius: 34px;
  transition: background-color 0.3s;
  margin-right: 8px;
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 16px;
  width: 16px;
  left: 4px;
  bottom: 4px;
  background-color: white;
  border-radius: 50%;
  transition: transform 0.3s;
}

.toggle-container input[type="checkbox"]:checked + .toggle-slider {
  background-color: #16a34a;
}

.toggle-container input[type="checkbox"]:checked + .toggle-slider:before {
  transform: translateX(20px);
}

.toggle-label {
  font-size: 0.9rem;
  color: #374151;
  font-weight: 500;
}

/* Alert Styles */
.alert-content {
  text-align: center;
}

.alert-content p {
  margin: 0 0 1rem 0;
  color: #374151;
}
</style>
