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
          <p>{{ translate('results.processing', [formatCount(processedCount), totalQuestionCount]) }}</p>
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

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useTranslations } from '../composables/useTranslations.js'

export default {
  name: 'Results',
  props: {
    sessionId: {
      type: String,
      required: true
    }
  },
  setup(props, { emit }) {
    // Translation support
    const { translate } = useTranslations()

    const score = ref(null)
    const totalQuestions = ref(null)
    const totalQuestionCount = ref(null)
    const percentage = ref(null)
    const resultsData = ref(null)
    const allProcessed = ref(false)
    const processedCount = ref(0)
    const isCheckingStatus = ref(false)
    const isPlayingAudio = ref(null) // Track which question's audio is playing

    // Audio player element
    const audioPlayer = ref(null)

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

    // Load results from backend (polling until all processed)
    const loadResults = async () => {
      if (isCheckingStatus.value) return

      try {
        isCheckingStatus.value = true
        console.log('Loading results for session:', props.sessionId)
        const response = await fetch(`/session/${props.sessionId}/results`)
        console.log('Response status:', response.status)

        if (response.ok) {
          const data = await response.json()
          console.log('Results loaded:', data)
          resultsData.value = data
          const maxPossibleScore = data.total_questions * 5
          score.value = data.total_score
          totalQuestions.value = maxPossibleScore
          percentage.value = Math.round((data.total_score / maxPossibleScore) * 100)
          allProcessed.value = data.all_processed
          processedCount.value = data.processed_count
          // Store total question count separately for display
          totalQuestionCount.value = data.total_questions

          // If not all processed, continue polling
          if (!data.all_processed) {
            setTimeout(loadResults, 2000)
          }
        } else {
          console.error('Failed to load results:', response.status)
          // Continue polling on error
          setTimeout(loadResults, 2000)
        }
      } catch (error) {
        console.error('Error loading results:', error)
        // Continue polling on error
        setTimeout(loadResults, 2000)
      } finally {
        isCheckingStatus.value = false
      }
    }

  
    // Start a new exam
    const startNewExam = () => {
      emit('new-exam')
    }

    // Go back to home
    const goHome = () => {
      emit('go-home')
    }

    // Format duration in seconds to readable format
    const formatDuration = (seconds) => {
      const minutes = Math.floor(seconds / 60)
      const remainingSeconds = seconds % 60
      return `${minutes}m ${remainingSeconds}s`
    }

    // Format score to show one decimal place
    const formatScore = (score) => {
      if (score === null || score === undefined) return '?'
      return parseFloat(score).toFixed(1)
    }

    // Format count to start at 1 instead of 0
    const formatCount = (count) => {
      if (count === null || count === undefined) return '?'
      return Math.max(1, count)
    }

    // Format question type for display
    const formatQuestionType = (type) => {
      const typeMap = {
        'read_aloud': 'Read Aloud',
        'multiple_choice': 'Multiple Choice',
        'quick_response': 'Quick Response',
        'translation': 'Translation'
      }
      return typeMap[type] || type
    }

    // Play student audio recording
    const playStudentAudio = (audioPath, questionIndex) => {
      if (isPlayingAudio.value === questionIndex) return // Already playing

      try {
        isPlayingAudio.value = questionIndex

        // Initialize audio player if needed
        if (!audioPlayer.value) {
          audioPlayer.value = new Audio()
        }

        // Construct the full URL for the audio file
        const audioUrl = `/audio-cache/${audioPath}`

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

    return {
      score,
      totalQuestions,
      totalQuestionCount,
      percentage,
      resultsData,
      allProcessed,
      processedCount,
      isPlayingAudio,
      startNewExam,
      goHome,
      formatDuration,
      formatQuestionType,
      formatScore,
      formatCount,
      playStudentAudio,
      translate
    }
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