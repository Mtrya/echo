<template>
  <div class="results">
    <div class="results-container">
      <div class="results-header">
        <h1>{{ translate('results.examCompleted') }}</h1>
        <p>{{ translate('results.congratulations') }}</p>
      </div>

      <div class="score-section">
        <div class="score-circle">
          <div class="score-number">{{ score || '?' }}</div>
          <div class="score-label">{{ translate('results.outOf') }} {{ totalQuestions || '?' }}</div>
        </div>
        <div class="processing-info" v-if="!allProcessed">
          <p v-if="!timeoutOccurred">{{ translate('results.processing', [formatCount(processedCount), totalQuestionCount ?? '?']) }}</p>
          <p v-else class="timeout-warning">{{ translate('results.timeoutWarning', [Math.floor(POLLING_TIMEOUT / 1000)]) }}</p>
        </div>
      </div>

      <div class="results-details">
        <!-- Show processing status -->
        <div v-if="!allProcessed" class="processing-message">
          <h3>{{ translate('results.processingAnswers') }}</h3>
          <p>{{ translate('results.analyzingResponses') }}</p>
          <div class="loading-indicator">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
          </div>
        </div>

        <!-- Show processed questions results -->
        <div v-else-if="resultsData" class="question-results">
          <h3>{{ translate('results.yourResults') }}</h3>
          <div class="results-summary">
            <p><strong>{{ translate('results.finalScore') }}:</strong> {{ formatScore(score) }}/{{ totalQuestions }} ({{ percentage }}%)</p>
            <p><strong>{{ translate('results.timeTaken') }}:</strong> {{ formatDuration(resultsData.duration_seconds) }}</p>
          </div>

          <!-- Timeout Warning -->
          <div v-if="timeoutOccurred" class="timeout-warning-box">
            <p>⚠️ <strong>{{ translate('results.timeoutOccurred') }}</strong> {{ translate('results.timeoutOccurredMessage') }}</p>
          </div>

          <!-- AI Disclaimer -->
          <div class="ai-disclaimer">
            <p>⚠️ <strong>{{ translate('results.aiDisclaimer') }}</strong> {{ translate('results.aiDisclaimerText') }}</p>
          </div>

          <div class="question-list">
            <div v-for="question in resultsData.question_results" :key="question.question_index" class="question-item">
              <div class="question-header">
                <span class="question-type">{{ formatQuestionType(question.question_type) }}</span>
                <span class="question-score">{{ formatScore(question.score) }}/5</span>
              </div>
              <div class="question-text">{{ question.question_text }}</div>

              <!-- Audio playback for student answers (ReadAloud, QuickResponse, Translation) -->
              <div v-if="['read_aloud', 'quick_response', 'translation'].includes(question.question_type) && question.student_audio_path" class="audio-playback">
                <button @click="playStudentAudio(question.student_audio_path, question.question_index)" class="btn btn-audio" :disabled="isPlayingAudio === question.question_index">
                  {{ isPlayingAudio === question.question_index ? '🔊 ' + translate('results.playing') : '🔊 ' + translate('results.playStudentAnswer') }}
                </button>
              </div>

              <!-- Student answer and reference answer for MultipleChoice -->
              <div v-if="question.question_type === 'multiple_choice'" class="answer-display">
                <p><strong>{{ translate('results.yourAnswer') }}</strong> {{ question.student_answer || translate('results.notAnswered') }}</p>
                <p><strong>{{ translate('results.correctAnswer') }}</strong> {{ question.reference_answer }}</p>
              </div>

              <div class="question-feedback">
                <p><strong>{{ translate('results.feedback') }}</strong> {{ question.feedback }}</p>
                <p v-if="question.explanation"><strong>{{ translate('results.explanation') }}</strong> {{ question.explanation }}</p>
                <p v-if="question.suggested_answer"><strong>{{ translate('results.suggestedAnswer') }}</strong> {{ question.suggested_answer }}</p>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="placeholder-message">
          <h3>📊 {{ translate('results.loadingResults') }}</h3>
          <p>{{ translate('results.finalizingResults') }}</p>
        </div>
      </div>

      <div class="results-actions">
        <button @click="startNewExam" class="btn btn-primary">
          📝 {{ translate('results.startNewExam') }}
        </button>
        <button @click="goHome" class="btn btn-secondary">
          🏠 {{ translate('results.backToHome') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTranslations } from '@/composables/useTranslations'
import { apiUrl } from '@/utils/api'
import type { ExamResultsResponse, QuestionResult } from '@/types'

// Props
const props = defineProps<{
  sessionId: string
}>()

// Emits
const emit = defineEmits<{
  'new-exam': []
  'go-home': []
}>()

// Translation support
const { translate } = useTranslations()

// Reactive state with proper types
const score = ref<number | null>(null)
const totalQuestions = ref<number | null>(null)
const totalQuestionCount = ref<number | null>(null)
const percentage = ref<number | null>(null)
const resultsData = ref<ExamResultsResponse | null>(null)
const allProcessed = ref<boolean>(false)
const processedCount = ref<number>(0)
const isCheckingStatus = ref<boolean>(false)
const isPlayingAudio = ref<number | null>(null) // Track which question's audio is playing
const timeoutOccurred = ref<boolean>(false) // Track if timeout has occurred
const pollingStartTime = ref<number | null>(null) // Track when polling started

// Audio player element
const audioPlayer = ref<HTMLAudioElement | null>(null)

// Timeout configuration (60 seconds)
const POLLING_TIMEOUT: number = 60000

// Start checking status when component mounts
onMounted(async () => {
  await loadResults()
})

// Cleanup audio player when component unmounts
onUnmounted(() => {
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.onended = null
    audioPlayer.value.onerror = null
    audioPlayer.value = null
  }
})

// Load results from backend (polling until all processed or timeout)
const loadResults = async (): Promise<void> => {
  if (isCheckingStatus.value) return

  // Initialize polling start time if not set
  if (!pollingStartTime.value) {
    pollingStartTime.value = Date.now()
  }

  // Check for timeout
  const elapsedTime = Date.now() - (pollingStartTime.value || 0)
  if (elapsedTime > POLLING_TIMEOUT && !timeoutOccurred.value) {
    console.log('Polling timeout reached, forcing results display')
    timeoutOccurred.value = true
    await handleTimeout()
    return
  }

  try {
    isCheckingStatus.value = true
    console.log('Loading results for session:', props.sessionId)
    const response = await fetch(apiUrl(`/session/${props.sessionId}/results`))
    console.log('Response status:', response.status)

    // Check if timeout occurred while waiting for response
    if (timeoutOccurred.value) {
      console.log('Timeout occurred during request, stopping polling')
      return
    }

    if (response.ok) {
      const data: ExamResultsResponse = await response.json()
      console.log('Results loaded:', data)
      resultsData.value = data
      score.value = data.total_score
      totalQuestions.value = data.max_score
      percentage.value = Math.round(data.percentage)
      allProcessed.value = data.all_processed
      processedCount.value = data.processed_count
      // Store total question count separately for display
      totalQuestionCount.value = data.total_questions

      // If not all processed and no timeout, continue polling
      if (!data.all_processed && !timeoutOccurred.value) {
        setTimeout(loadResults, 2000)
      }
    } else {
      console.error('Failed to load results:', response.status)
      // Continue polling on error if no timeout
      if (!timeoutOccurred.value) {
        setTimeout(loadResults, 2000)
      }
    }
  } catch (error) {
    console.error('Error loading results:', error)
    // Continue polling on error if no timeout
    if (!timeoutOccurred.value) {
      setTimeout(loadResults, 2000)
    }
  } finally {
    isCheckingStatus.value = false
  }
}

// Handle timeout by generating failed results for unprocessed questions
const handleTimeout = async (): Promise<void> => {
  if (!resultsData.value) return

  console.log('Handling timeout, generating failed question results')

  // Create a copy of the results data
  const modifiedResults: ExamResultsResponse = { ...resultsData.value }

  // Get indices of questions that haven't been processed
  const processedIndices = new Set(modifiedResults.question_results.map((q: QuestionResult) => q.question_index))
  const totalQuestionsCount = modifiedResults.total_questions

  // Generate failed results for unprocessed questions
  for (let i = 0; i < totalQuestionsCount; i++) {
    if (!processedIndices.has(i)) {
      const failedResult = generateFailedQuestionResult(i)
      modifiedResults.question_results.push(failedResult)
    }
  }

  // Sort questions by index
  modifiedResults.question_results.sort((a: QuestionResult, b: QuestionResult) => a.question_index - b.question_index)

  // Update the results data
  modifiedResults.all_processed = true
  modifiedResults.processed_count = totalQuestionsCount
  resultsData.value = modifiedResults
  allProcessed.value = true
}

// Generate a failed question result
const generateFailedQuestionResult = (questionIndex: number): QuestionResult => {
  // Try to get question info from the original exam data
  // Since we don't have the full exam data, we'll create a generic failed result
  return {
    question_index: questionIndex,
    question_id: `question_${questionIndex}`,
    question_type: "unknown",
    question_text: translate('results.questionProcessingFailed'),
    score: 0,
    feedback: translate('results.processingTimeout'),
    explanation: translate('results.timeoutExplanation')
  }
}

// Start a new exam
const startNewExam = (): void => {
  emit('new-exam')
}

// Go back to home
const goHome = (): void => {
  emit('go-home')
}

// Format duration in seconds to readable format
const formatDuration = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}m ${remainingSeconds}s`
}

// Format score to show one decimal place
const formatScore = (score: number | null): string => {
  if (score === null || score === undefined) return '?'
  return parseFloat(score.toString()).toFixed(1)
}

// Format count to start at 1 instead of 0
const formatCount = (count: number | null): string => {
  if (count === null || count === undefined) return '?'
  return Math.max(1, count).toString()
}

// Format question type for display
const formatQuestionType = (type: string): string => {
  const typeMap: Record<string, string> = {
    'read_aloud': 'Read Aloud',
    'multiple_choice': 'Multiple Choice',
    'quick_response': 'Quick Response',
    'translation': 'Translation'
  }
  return typeMap[type] || type
}

// Play student audio recording
const playStudentAudio = (audioPath: string, questionIndex: number): void => {
  if (isPlayingAudio.value === questionIndex) return // Already playing

  try {
    isPlayingAudio.value = questionIndex

    // Initialize audio player if needed
    if (!audioPlayer.value) {
      audioPlayer.value = new Audio()
    }

    // Construct the full URL for the audio file
    const audioUrl = apiUrl(`/audio_cache/${audioPath}`)

    // Set up audio player
    audioPlayer.value.src = audioUrl
    audioPlayer.value.onended = () => {
      isPlayingAudio.value = null
    }
    audioPlayer.value.onerror = (error) => {
      console.error('Error playing audio:', error)
      isPlayingAudio.value = null
    }

    // Play the audio
    audioPlayer.value.play().catch(error => {
      console.error('Failed to play audio:', error)
      isPlayingAudio.value = null
    })

  } catch (error) {
    console.error('Error setting up audio playback:', error)
    isPlayingAudio.value = null
  }
}
</script>

<style scoped>
.results {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
  background: linear-gradient(135deg, #4ade80 0%, #ffffff 100%);
}

.results-container {
  max-width: 800px;
  width: 100%;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 20px;
  padding: 3rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  text-align: center;
}

.results-header h1 {
  color: #16a34a;
  font-size: 3rem;
  margin-bottom: 1rem;
}

.results-header p {
  color: #6b7280;
  font-size: 1.2rem;
  margin-bottom: 2rem;
}

.score-section {
  margin: 3rem 0;
}

.score-circle {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: linear-gradient(135deg, #16a34a, #22c55e);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  margin: 0 auto;
  box-shadow: 0 10px 30px rgba(34, 197, 94, 0.3);
}

.score-number {
  font-size: 3rem;
  font-weight: 700;
  color: white;
}

.score-label {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.9);
  margin-top: 0.5rem;
}

.results-details {
  margin: 3rem 0;
  padding: 2rem;
  background: rgba(34, 197, 94, 0.1);
  border-radius: 15px;
}

.placeholder-message h3 {
  color: #16a34a;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}

.placeholder-message p {
  color: #374151;
  margin-bottom: 1rem;
}

.placeholder-message ul {
  list-style: none;
  padding: 0;
  text-align: left;
  display: inline-block;
}

.placeholder-message li {
  color: #6b7280;
  margin: 0.5rem 0;
  padding-left: 1.5rem;
  position: relative;
}

.placeholder-message li::before {
  content: "✓";
  position: absolute;
  left: 0;
  color: #16a34a;
  font-weight: bold;
}

.processing-info {
  margin-top: 1rem;
  color: #6b7280;
  font-size: 1rem;
}

.results-actions {
  margin-top: 3rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.question-results {
  text-align: left;
  margin-top: 2rem;
}

.results-summary {
  background: #f9fafb;
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 2rem;
}

.results-summary p {
  margin: 0.5rem 0;
  color: #374151;
}

.question-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.question-item {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.question-type {
  background: #f3f4f6;
  color: #374151;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 600;
}

.question-score {
  font-weight: bold;
  color: #16a34a;
}

.question-text {
  color: #374151;
  margin-bottom: 1rem;
  line-height: 1.5;
}

.question-feedback {
  font-size: 0.875rem;
}

.question-feedback p {
  margin: 0.5rem 0;
  color: #6b7280;
}

.question-feedback strong {
  color: #374151;
}

.audio-playback {
  margin: 1rem 0;
}

.btn-audio {
  background: #3b82f6;
  color: white;
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
  min-width: auto;
}

.btn-audio:hover:not(:disabled) {
  background: #2563eb;
  transform: translateY(-1px);
}

.btn-audio:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

.answer-display {
  background: #f9fafb;
  padding: 1rem;
  border-radius: 8px;
  margin: 1rem 0;
}

.answer-display p {
  margin: 0.5rem 0;
  color: #374151;
}

.answer-display strong {
  color: #1f2937;
}

.ai-disclaimer {
  background: #fef3c7;
  border: 1px solid #f59e0b;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
}

.ai-disclaimer p {
  margin: 0;
  color: #92400e;
  font-size: 0.9rem;
  line-height: 1.5;
}

.ai-disclaimer strong {
  color: #78350f;
}

.timeout-warning {
  color: #dc2626;
  font-weight: 600;
}

.timeout-warning-box {
  background: #fef2f2;
  border: 1px solid #dc2626;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 2rem;
}

.timeout-warning-box p {
  margin: 0;
  color: #991b1b;
  font-size: 0.9rem;
  line-height: 1.5;
}

.timeout-warning-box strong {
  color: #7f1d1d;
}

.btn {
  padding: 1rem 2rem;
  border: none;
  border-radius: 12px;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  min-width: 180px;
}

.btn-primary {
  background: #16a34a;
  color: white;
}

.btn-primary:hover {
  background: #15803d;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(21, 128, 61, 0.3);
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #16a34a;
  border: 2px solid #16a34a;
}

.btn-secondary:hover {
  background: white;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.debug-results {
  text-align: left;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 1rem;
  margin: 1rem 0;
}

.debug-results h3 {
  color: #dc2626;
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
}

.debug-results pre {
  background: #1f2937;
  color: #f9fafb;
  padding: 1rem;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 0.9rem;
  line-height: 1.4;
}

.processing-message {
  text-align: center;
  padding: 2rem;
}

.processing-message h3 {
  color: #16a34a;
  margin-bottom: 1rem;
  font-size: 1.5rem;
}

.processing-message p {
  color: #6b7280;
  margin-bottom: 2rem;
  font-size: 1.1rem;
}

.loading-indicator {
  display: flex;
  justify-content: center;
  gap: 0.5rem;
}

.loading-dot {
  width: 12px;
  height: 12px;
  background: #16a34a;
  border-radius: 50%;
  animation: loading-pulse 1.4s ease-in-out infinite both;
}

.loading-dot:nth-child(1) {
  animation-delay: -0.32s;
}

.loading-dot:nth-child(2) {
  animation-delay: -0.16s;
}

.loading-dot:nth-child(3) {
  animation-delay: 0s;
}

@keyframes loading-pulse {
  0%, 80%, 100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@media (max-width: 768px) {
  .results-container {
    padding: 2rem;
    margin: 1rem;
  }

  .results-header h1 {
    font-size: 2rem;
  }

  .score-circle {
    width: 150px;
    height: 150px;
  }

  .score-number {
    font-size: 2.5rem;
  }

  .results-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>
