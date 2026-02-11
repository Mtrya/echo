<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <h1>{{ translate('header.title') }}</h1>
    </header>

    <!-- Loading screen while waiting for backend in Tauri mode -->
    <main v-if="!backendReady" class="main-content">
      <div class="loading-screen">
        <div class="loading-spinner"></div>
        <p>{{ translate('common.loading') || 'Starting up...' }}</p>
      </div>
    </main>

    <!-- Main Content Area -->
    <main v-else class="main-content">
      <!-- Home Page -->
      <div v-if="currentPage === 'home'">
        <HomePage ref="homePage" @start-exam="handleStartExam" @file-converter="currentPage = 'file-converter'" @open-settings="showSettings = true" />
      </div>

      <!-- File Converter Page -->
      <div v-else-if="currentPage === 'file-converter'">
        <FileConverter
          :key="'file-converter'"
          @go-home="currentPage = 'home'"
        />
      </div>

      <!-- Audio Test Page -->
      <div v-else-if="currentPage === 'audio-test'">
        <AudioTest
          :session-id="sessionId"
          @complete="handleAudioTestComplete"
        />
      </div>

      <!-- Instruction Page -->
      <div v-else-if="currentPage === 'instruction'">
        <InstructionPage
          :key="currentQuestionType + '-' + (currentInstruction?.text || '')"
          :instruction="currentInstruction"
          :audio-file="currentInstructionAudio"
          :question-type="currentQuestionType"
          @start-section="handleInstructionComplete"
        />
      </div>

      <!-- Read Aloud Question -->
      <div v-else-if="currentPage === 'read-aloud'">
        <ReadAloud
          :key="currentQuestion?.id || 'read-aloud'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Multiple Choice Question -->
      <div v-else-if="currentPage === 'multiple-choice'">
        <MultipleChoice
          :key="currentQuestion?.id || 'multiple-choice'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Quick Response Question -->
      <div v-else-if="currentPage === 'quick-response'">
        <QuickResponse
          :key="currentQuestion?.id || 'quick-response'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Translation Question -->
      <div v-else-if="currentPage === 'translation'">
        <Translation
          :key="currentQuestion?.id || 'translation'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Results Page -->
      <div v-else-if="currentPage === 'results'">
        <Results
          :session-id="sessionId"
          @new-exam="handleNewExam"
          @go-home="handleGoHome"
        />
      </div>

      <!-- Other pages will be added later -->
      <div v-else class="placeholder-page">
        <h2>{{ currentPage }} - Coming Soon</h2>
        <button @click="currentPage = 'home'" class="btn btn-secondary">{{ translate('common.back') }}</button>
      </div>
    </main>

    <!-- Settings Modal -->
    <div v-if="showSettings" class="settings-modal">
      <div class="settings-modal-content">
        <Settings
          @close-settings="showSettings = false"
          @settings-updated="handleSettingsUpdated"
        />
      </div>
    </div>

    <!-- Update Modal -->
    <div v-if="updateState.status === 'available'" class="settings-modal">
      <div class="update-modal-content">
        <h2>{{ translate('update.available') }}</h2>
        <p>{{ translate('update.newVersion', [updateState.version ?? '', updateState.currentVersion ?? '']) }}</p>
        <div v-if="updateState.notes" class="update-notes">
          <strong>{{ translate('update.releaseNotes') }}</strong>
          <p>{{ updateState.notes }}</p>
        </div>
        <div class="update-actions">
          <button @click="updateState.status = 'idle'" class="btn btn-secondary">{{ translate('update.later') }}</button>
          <button @click="updateState.install?.()" class="btn btn-primary">{{ translate('update.updateNow') }}</button>
        </div>
      </div>
    </div>

    <!-- Update downloading overlay -->
    <div v-if="updateState.status === 'downloading' || updateState.status === 'installing'" class="settings-modal">
      <div class="update-modal-content">
        <div class="loading-spinner"></div>
        <p>{{ updateState.status === 'downloading' ? translate('update.downloading') : translate('update.installing') }}</p>
      </div>
    </div>

    <!-- Update error -->
    <div v-if="updateState.status === 'error'" class="settings-modal">
      <div class="update-modal-content">
        <p class="update-error">{{ translate('update.failed') }}</p>
        <button @click="updateState.status = 'idle'" class="btn btn-secondary">{{ translate('common.close') }}</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useTranslations } from '@/composables/useTranslations'
import { apiUrl, setApiBaseUrl } from '@/utils/api'
import HomePage from '@/components/HomePage.vue'
import AudioTest from '@/components/AudioTest.vue'
import InstructionPage from '@/components/InstructionPage.vue'
import ReadAloud from '@/components/ReadAloud.vue'
import MultipleChoice from '@/components/MultipleChoice.vue'
import QuickResponse from '@/components/QuickResponse.vue'
import Translation from '@/components/Translation.vue'
import Results from '@/components/Results.vue'
import FileConverter from '@/components/FileConverter.vue'
import Settings from '@/components/Settings.vue'
import type { Question, Instruction, GetQuestionResponse, StartSessionResponse, AppConfig } from '@/types'
import { checkForUpdates, type UpdateState } from '@/utils/updater'

type PageType = 'home' | 'file-converter' | 'audio-test' | 'instruction' | 'read-aloud' | 'multiple-choice' | 'quick-response' | 'translation' | 'results'
type QuestionType = 'read_aloud' | 'multiple_choice' | 'quick_response' | 'translation'

// Extend Window interface for Tauri
declare global {
  interface Window {
    __TAURI__?: boolean
  }
}

// Translation support
const { translate } = useTranslations()

// Navigation state
const currentPage = ref<PageType>('home')
const sessionId = ref<string>('')
const currentQuestion = ref<Question | null>(null)
const showSettings = ref<boolean>(false)
const currentInstruction = ref<Instruction | null>(null)
const currentInstructionAudio = ref<string | null>(null)
const currentQuestionType = ref<QuestionType | null>(null)
const homePage = ref<InstanceType<typeof HomePage> | null>(null)
// In Tauri mode, wait for backend-ready event before rendering content
const backendReady = ref<boolean>(!window.__TAURI__)
// Update state
const updateState = ref<UpdateState>({ status: 'idle' })

// Set up Tauri backend-ready listener
onMounted(async () => {
  if (window.__TAURI__) {
    const { listen } = await import('@tauri-apps/api/event')
    listen('backend-ready', (event: { payload: number }) => {
      const port = event.payload
      console.log('Backend ready on port:', port)
      setApiBaseUrl(`http://127.0.0.1:${port}`)
      backendReady.value = true
    })
    // Check for updates in background
    checkForUpdates(updateState)
  }
})

interface ExamStartData {
  sessionId?: string
  examFile?: string
}

// Handle exam start event from components
const handleStartExam = async (examData: ExamStartData) => {
  console.log('Exam start request:', examData)

  // Check if we have a session ID (from existing exam) or exam file (from file converter)
  if (examData.sessionId) {
    // Existing exam with session ID
    sessionId.value = examData.sessionId
    currentPage.value = 'audio-test'
  } else if (examData.examFile) {
    // New exam from file converter - start session first
    try {
      const response = await fetch(apiUrl('/session/start'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          exam_file_path: examData.examFile
        })
      })

      const data: StartSessionResponse = await response.json()

      if (data.session_id) {
        sessionId.value = data.session_id
        currentPage.value = 'audio-test'
      } else {
        console.error('Failed to start exam session')
        currentPage.value = 'home'
      }
    } catch (error) {
      console.error('Failed to start exam:', error)
      currentPage.value = 'home'
    }
  } else {
    console.error('Invalid exam data:', examData)
    currentPage.value = 'home'
  }
}

// Start the first question
const startFirstQuestion = async () => {
  console.log('Starting first question for session:', sessionId.value)
  await getNextQuestion()
}

interface AudioTestData {
  sessionId: string
  audioTestPassed: boolean
}

// Handle audio test completion
const handleAudioTestComplete = async (testData: AudioTestData) => {
  console.log('Audio test completed:', testData)

  // Start the first question
  await startFirstQuestion()
}

// Get the next question
const getNextQuestion = async () => {
  try {
    console.log('Fetching next question for session:', sessionId.value)
    const response = await fetch(apiUrl(`/session/${sessionId.value}/question`))
    const data: GetQuestionResponse = await response.json()

    console.log('Question response:', data)

    if (data.question) {
      currentQuestion.value = {
        ...data.question,
        question_index: data.question_index,
        is_last: data.is_last,
        audio_file_path: data.audio_file_path,
        time_limit: data.time_limit
      }

      console.log('Setting up question:', data.question.type, 'has instruction:', !!data.instruction)

      // Check if this is the first question in a section (has instruction)
      if (data.instruction) {
        // Show instruction page first
        currentQuestionType.value = data.question.type as QuestionType
        currentInstruction.value = data.instruction
        currentInstructionAudio.value = data.instruct_audio_file_path ? apiUrl(data.instruct_audio_file_path) : null
        currentPage.value = 'instruction'
        console.log('Navigating to instruction page for section:', data.question.type)
      } else {
        // Go directly to question
        navigateToQuestion(data.question.type as QuestionType)
      }
    } else {
      console.error('No question in response:', data)
      currentPage.value = 'home'
    }
  } catch (error) {
    console.error('Failed to get next question:', error)
    currentPage.value = 'home'
  }
}

// Navigate to the appropriate question page
const navigateToQuestion = (questionType: QuestionType) => {
  console.log('Navigating to question type:', questionType)
  if (questionType === 'read_aloud') {
    currentPage.value = 'read-aloud'
  } else if (questionType === 'multiple_choice') {
    currentPage.value = 'multiple-choice'
  } else if (questionType === 'quick_response') {
    currentPage.value = 'quick-response'
  } else if (questionType === 'translation') {
    currentPage.value = 'translation'
  } else {
    console.log('Unknown question type:', questionType)
    currentPage.value = 'home'
  }
}

// Handle instruction page completion
const handleInstructionComplete = async () => {
  console.log('Instruction completed, starting question section:', currentQuestionType.value)
  if (currentQuestionType.value) {
    navigateToQuestion(currentQuestionType.value)
  }
}

interface QuestionResult {
  success: boolean
  error?: string
}

// Handle question completion
const handleQuestionComplete = async (result: QuestionResult) => {
  console.log('Question completed:', result)

  if (result.success) {
    if (currentQuestion.value?.is_last) {
      // Go to results page
      console.log('Exam completed! Navigating to results...')
      currentPage.value = 'results'
    } else {
      // Get next question
      await getNextQuestion()
    }
  } else {
    // Handle error
    console.error('Question failed:', result.error)
    currentPage.value = 'home'
  }
}

// Handle new exam request from results page
const handleNewExam = () => {
  // Reset state for new exam
  currentPage.value = 'home'
  sessionId.value = ''
  currentQuestion.value = null
}

// Handle go home request from results page
const handleGoHome = () => {
  currentPage.value = 'home'
}

const handleSettingsUpdated = async (newSettings: AppConfig) => {
  console.log('Settings updated:', newSettings)
  // Theme feature has been removed
  // currentTheme.value = `theme-${newSettings.ui.theme}`
  // document.body.className = `theme-${newSettings.ui.theme}`

  // Refresh API key status to update button states
  if (homePage.value) {
    await homePage.value.refreshApiKeyStatus()
  }
}
</script>

<style scoped>
/* App Layout */
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #4ade80 0%, #ffffff 100%);
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.9);
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header h1 {
  color: #16a34a;
  margin: 0;
  font-size: 2rem;
}

.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
}

/* Button Styles */
.btn {
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
}

.btn-primary {
  background: #16a34a;
  color: white;
}

.btn-primary:hover {
  background: #15803d;
  transform: translateY(-2px);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #16a34a;
  border: 2px solid #16a34a;
}

.btn-secondary:hover {
  background: white;
  transform: translateY(-2px);
}

/* Loading Screen */
.loading-screen {
  text-align: center;
  color: #16a34a;
}

.loading-screen p {
  margin-top: 1rem;
  font-size: 1.2rem;
  font-weight: 600;
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(22, 163, 74, 0.2);
  border-top-color: #16a34a;
  border-radius: 50%;
  margin: 0 auto;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* Placeholder Page */
.placeholder-page {
  text-align: center;
}

.placeholder-page h2 {
  color: #16a34a;
  margin-bottom: 1rem;
}

/* Settings Modal */
.settings-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.settings-modal-content {
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  background: white;
  border-radius: 10px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

/* Update Modal */
.update-modal-content {
  background: white;
  border-radius: 10px;
  padding: 2rem;
  max-width: 450px;
  text-align: center;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.update-modal-content h2 {
  color: #16a34a;
  margin: 0 0 1rem;
}

.update-notes {
  text-align: left;
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  margin: 1rem 0;
  max-height: 200px;
  overflow-y: auto;
}

.update-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 1.5rem;
}

.update-error {
  color: #dc3545;
  font-weight: 600;
  margin-bottom: 1rem;
}
</style>
