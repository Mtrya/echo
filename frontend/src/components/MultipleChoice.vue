<template>
  <div class="multiple-choice">
    <!-- Question Phase -->
    <div class="question-phase">
      <div class="question-text">
        {{ currentQuestion.text }}
      </div>

      <div class="options-grid">
        <div
          v-for="option in currentQuestion.options"
          :key="option"
          class="option-item"
          :class="{ selected: selectedOption === option }"
          @click="selectOption(option)"
        >
          {{ option }}
        </div>
      </div>

      <div class="timer-section">
        <div class="timer-indicator" :class="{ 'timer-danger': timeRemaining <= 10 }">
          <div class="timer-dot"></div>
          <div class="timer-text">
            TIME: {{ timeRemaining }}s
          </div>
        </div>
      </div>

      <button
        @click="submitAnswer"
        class="btn btn-submit"
        :disabled="!selectedOption"
      >
        {{ translate('questions.multipleChoice.submitAnswer') }}
      </button>
    </div>

    <!-- Auto-submit Phase -->
    <div v-if="phase === 'auto-submit'" class="auto-submit-phase">
      <div class="question-text">
        {{ currentQuestion.text }}
      </div>

      <div class="options-grid">
        <div
          v-for="option in currentQuestion.options"
          :key="option"
          class="option-item"
          :class="{ selected: selectedOption === option }"
        >
          {{ option }}
        </div>
      </div>

      <div class="auto-submit-text">
        {{ translate('questions.multipleChoice.timeUp') }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'
import { useTranslations } from '../composables/useTranslations.js'
import { apiUrl } from '../utils/api.js'

export default {
  name: 'MultipleChoice',
  props: {
    sessionId: {
      type: String,
      required: true
    },
    currentQuestion: {
      type: Object,
      required: true
    }
  },
  emits: ['complete'],
  setup(props, { emit }) {
    // Translation support
    const { translate } = useTranslations()

    // Phase management
    const phase = ref('question') // 'question', 'auto-submit'

    // Timer and selection
    const timeRemaining = ref(0)
    const selectedOption = ref(null)

    // Timer reference
    let questionTimer = null

    // Initialize on component mount
    onMounted(async () => {
      await initializeQuestion()
    })

    // Cleanup on component unmount
    onUnmounted(() => {
      cleanup()
    })

    // Initialize the question flow
    const initializeQuestion = async () => {
      try {
        // Start question phase directly
        startQuestionPhase()
      } catch (error) {
        console.error('Failed to initialize question:', error)
        startQuestionPhase()
      }
    }

    
    // Start question phase
    const startQuestionPhase = () => {
      phase.value = 'question'
      timeRemaining.value = props.currentQuestion.time_limit || 30
      selectedOption.value = null

      // Start countdown timer
      questionTimer = setInterval(() => {
        timeRemaining.value--

        if (timeRemaining.value <= 0) {
          autoSubmit()
        }
      }, 1000)
    }

    // Select an option
    const selectOption = (option) => {
      selectedOption.value = option
    }

    // Submit answer manually
    const submitAnswer = () => {
      if (!selectedOption.value) return

      cleanup()
      submitToBackend(selectedOption.value)
    }

    // Auto-submit when time runs out
    const autoSubmit = () => {
      phase.value = 'auto-submit'
      cleanup()

      // Submit with empty string if no selection
      const answer = selectedOption.value || ''

      // Brief delay to show auto-submit message
      setTimeout(() => {
        submitToBackend(answer)
      }, 1000)
    }

    // Submit answer to backend
    const submitToBackend = async (answerText) => {
      try {
        const response = await fetch(apiUrl(`/session/${props.sessionId}/answer`), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            answer_text: answerText
          })
        })

        if (response.ok) {
          console.log('Answer submitted successfully:', answerText)

          // Immediately emit completion event
          emit('complete', {
            sessionId: props.sessionId,
            questionIndex: props.currentQuestion.question_index,
            success: true
          })
        } else {
          throw new Error('Failed to submit answer')
        }

      } catch (error) {
        console.error('Failed to submit answer:', error)
        emit('complete', {
          sessionId: props.sessionId,
          questionIndex: props.currentQuestion.question_index,
          success: false,
          error: error.message
        })
      }
    }

    // Cleanup resources
    const cleanup = () => {
      if (questionTimer) {
        clearInterval(questionTimer)
        questionTimer = null
      }
    }

    return {
      phase,
      timeRemaining,
      selectedOption,
      selectOption,
      submitAnswer,
      translate
    }
  }
}
</script>

<style scoped>
.multiple-choice {
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
}


/* Question Phase */
.question-phase {
  min-height: 500px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.question-text {
  font-size: 2rem;
  color: #374151;
  margin-bottom: 2rem;
  line-height: 1.6;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin: 2rem 0;
}

.option-item {
  padding: 1.5rem;
  border: 3px solid #e5e7eb;
  border-radius: 12px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.8);
}

.option-item:hover {
  border-color: #16a34a;
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-2px);
}

.option-item.selected {
  border-color: #16a34a;
  background: #dcfce7;
  color: #16a34a;
}

.timer-section {
  margin: 1rem 0;
}

.timer-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 2rem;
  border-radius: 50px;
  background: rgba(34, 197, 94, 0.1);
  border: 3px solid #22c55e;
  transition: all 0.3s ease;
  justify-content: center;
  margin-bottom: 1rem;
}

.timer-indicator.timer-danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  animation: pulse 1s infinite;
}

.timer-dot {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #22c55e;
  animation: timer-pulse 2s infinite;
}

.timer-indicator.timer-danger .timer-dot {
  background: #ef4444;
  animation: timer-pulse-danger 1s infinite;
}

.timer-text {
  font-size: 1.3rem;
  font-weight: 700;
  color: #22c55e;
}

.timer-indicator.timer-danger .timer-text {
  color: #ef4444;
}

/* Auto-submit Phase */
.auto-submit-phase {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.auto-submit-text {
  font-size: 1.5rem;
  color: #ef4444;
  font-weight: 600;
  margin-top: 2rem;
  animation: pulse 1s infinite;
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
  margin: 0.5rem;
}

.btn-submit {
  background: #16a34a;
  color: white;
  min-width: 200px;
}

.btn-submit:hover:not(:disabled) {
  background: #15803d;
  transform: translateY(-2px);
}

.btn-submit:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  transform: none;
}

/* Animations */
@keyframes timer-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes timer-pulse-danger {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}
</style>