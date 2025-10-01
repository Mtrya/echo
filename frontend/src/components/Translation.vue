<template>
  <div class="translation">
    <!-- Display Phase -->
    <div v-if="phase === 'display'" class="display-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="status-text">
        {{ translate('questions.translation.getReady') }}
      </div>
    </div>

    <!-- Thinking Phase -->
    <div v-else-if="phase === 'thinking'" class="thinking-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="thinking-text">
        {{ translate('questions.translation.getReady') }}
      </div>
      <div class="countdown-text">
        {{ countdownText }}
      </div>
    </div>

    <!-- Recording Phase -->
    <div v-else-if="phase === 'recording'" class="recording-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="recording-instruction">
        {{ translate('questions.translation.speakNow') }}
      </div>
      <div class="recording-indicator" :class="{ 'recording-danger': timeRemaining <= 5 }">
        <div class="recording-dot"></div>
        <div class="recording-text">
          RECORDING: {{ timeRemaining }}s
        </div>
      </div>
      <button
        v-if="timeRemaining > 0"
        @click="stopRecording"
        class="btn btn-stop"
      >
        {{ translate('questions.translation.stopRecording') }}
      </button>
    </div>

    <!-- Auto-submit Phase -->
    <div v-else-if="phase === 'auto-submit'" class="auto-submit-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="auto-submit-text">
        {{ translate('questions.translation.timeUp') }}
      </div>
    </div>

    </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useTranslations } from '../composables/useTranslations.js'
import Mp3Recorder, { blobToBase64 } from '../utils/mp3Recorder.js'

export default {
  name: 'Translation',
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
    const phase = ref('display') // 'display', 'thinking', 'recording', 'auto-submit'

    // Timer
    const timeRemaining = ref(0)
    const countdownText = ref('3')

    // MP3 recorder
    let mp3Recorder = null

    // Timer references
    let thinkingTimer = null
    let recordingTimer = null

    // Initialize on component mount
    onMounted(async () => {
      await initializeQuestion()
    })

    // Watch for question changes and reset state
    watch(() => props.currentQuestion, async (newQuestion, oldQuestion) => {
      if (newQuestion && newQuestion.id !== oldQuestion?.id) {
        console.log('Translation: Question changed from', oldQuestion?.id, 'to', newQuestion.id)
        // Reset component state for new question
        resetState()
        // Initialize new question
        await initializeQuestion()
      }
    }, { deep: true })

    // Cleanup on component unmount
    onUnmounted(() => {
      cleanup()
    })

    // Reset component state for new question
    const resetState = () => {
      console.log('Translation: Resetting component state')

      // Clean up any existing resources
      cleanup()

      // Reset all reactive state
      phase.value = 'display'
      timeRemaining.value = 0
      countdownText.value = '3'

      // Reset audio chunks
      // audioChunks = []  // No longer needed with MP3 recorder

      console.log('Translation: State reset complete')
    }

    // Initialize the question flow
    const initializeQuestion = async () => {
      try {
        // Initialize audio recording permissions
        await initializeAudio()

        // Start thinking phase directly
        startThinkingPhase()

      } catch (error) {
        console.error('Failed to initialize question:', error)
        submitEmptyAnswer()
      }
    }

    // Initialize MP3 recorder
    const initializeAudio = async () => {
      try {
        // Check browser support
        if (!Mp3Recorder.isSupported()) {
          throw new Error('MP3 recording is not supported in this browser')
        }

        // Create new MP3 recorder instance
        mp3Recorder = new Mp3Recorder()
        console.log('MP3 recorder initialized successfully')
      } catch (error) {
        console.error('Failed to initialize MP3 recorder:', error)
        throw error
      }
    }


    // Start thinking phase
    const startThinkingPhase = () => {
      phase.value = 'thinking'
      let countdown = 3

      // Start countdown timer
      thinkingTimer = setInterval(() => {
        countdown--
        countdownText.value = countdown.toString()

        if (countdown <= 0) {
          clearInterval(thinkingTimer)
          thinkingTimer = null
          startRecordingPhase()
        }
      }, 1000)
    }

    // Start recording phase
    const startRecordingPhase = async () => {
      phase.value = 'recording'

      // Calculate time: half of time_limit for thinking (already used), half for recording
      const totalTime = props.currentQuestion.time_limit || 30
      timeRemaining.value = Math.floor(totalTime / 2)

      // Start MP3 recording
      try {
        if (mp3Recorder) {
          await mp3Recorder.start()
        }
      } catch (error) {
        console.error('Failed to start MP3 recording:', error)
        submitEmptyAnswer()
        return
      }

      // Start countdown timer
      recordingTimer = setInterval(() => {
        timeRemaining.value--

        if (timeRemaining.value <= 0) {
          autoSubmit()
        }
      }, 1000)
    }

    // Stop recording manually
    const stopRecording = async () => {
      if (recordingTimer) {
        clearInterval(recordingTimer)
        recordingTimer = null
      }

      // Stop MP3 recording and submit answer
      if (mp3Recorder) {
        try {
          const mp3Blob = await mp3Recorder.stop()
          await submitAnswer(mp3Blob)
        } catch (error) {
          console.error('Failed to stop MP3 recording:', error)
          submitEmptyAnswer()
        }
      }
    }

    // Auto-submit when time runs out
    const autoSubmit = () => {
      phase.value = 'auto-submit'
      stopRecording()
    }

    // Submit the recorded answer
    const submitAnswer = async (mp3Blob) => {
      try {
        if (!mp3Blob) {
          throw new Error('No audio blob provided')
        }

        // Convert MP3 blob to base64
        const base64Audio = await blobToBase64(mp3Blob)

        // Submit as JSON with base64 encoded audio data
        const response = await fetch(`/session/${props.sessionId}/answer`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            audio_data: base64Audio
          })
        })

        if (response.ok) {
          console.log('MP3 answer submitted successfully')

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
        console.error('Failed to submit MP3 answer:', error)
        emit('complete', {
          sessionId: props.sessionId,
          questionIndex: props.currentQuestion.question_index,
          success: false,
          error: error.message
        })
      }
    }

    // Submit empty answer (when recording fails)
    const submitEmptyAnswer = () => {
      emit('complete', {
        sessionId: props.sessionId,
        questionIndex: props.currentQuestion.question_index,
        success: false,
        error: 'Recording failed'
      })
    }

    // Cleanup resources
    const cleanup = () => {
      if (thinkingTimer) {
        clearInterval(thinkingTimer)
        thinkingTimer = null
      }

      if (recordingTimer) {
        clearInterval(recordingTimer)
        recordingTimer = null
      }

      // Cleanup MP3 recorder if it exists
      if (mp3Recorder) {
        try {
          mp3Recorder._cleanup()
        } catch (error) {
          console.error('Error cleaning up MP3 recorder:', error)
        }
        mp3Recorder = null
      }
    }



    return {
      phase,
      timeRemaining,
      countdownText,
      stopRecording,
      translate
    }
  }
}
</script>

<style scoped>
.translation {
  text-align: center;
  max-width: 700px;
  margin: 0 auto;
  padding: 2rem;
}

/* Chinese Text Display */
.chinese-text {
  font-size: 2rem;
  color: #374151;
  margin-bottom: 2rem;
  line-height: 1.6;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

/* Display Phase */
.display-phase {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.status-text {
  font-size: 1.2rem;
  color: #16a34a;
  font-weight: 600;
}

/* Thinking Phase */
.thinking-phase {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.thinking-text {
  font-size: 1.6rem;
  color: #374151;
  margin-bottom: 1rem;
  font-weight: 600;
}

.countdown-text {
  font-size: 3rem;
  color: #16a34a;
  font-weight: 700;
  animation: countdown-pulse 1s infinite;
}

/* Recording Phase */
.recording-phase {
  min-height: 500px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.recording-instruction {
  font-size: 1.5rem;
  color: #374151;
  margin-bottom: 2rem;
  font-weight: 600;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.5rem 3rem;
  border-radius: 50px;
  background: rgba(34, 197, 94, 0.1);
  border: 3px solid #22c55e;
  margin: 2rem 0;
  transition: all 0.3s ease;
}

.recording-indicator.recording-danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  animation: pulse 1s infinite;
}

.recording-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #22c55e;
  animation: recording-pulse 1.5s infinite;
}

.recording-indicator.recording-danger .recording-dot {
  background: #ef4444;
  animation: recording-pulse-danger 0.8s infinite;
}

.recording-text {
  font-size: 1.4rem;
  font-weight: 700;
  color: #22c55e;
}

.recording-indicator.recording-danger .recording-text {
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

.btn-stop {
  background: #ef4444;
  color: white;
}

.btn-stop:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

/* Animations */
@keyframes recording-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes recording-pulse-danger {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.05); }
}

@keyframes countdown-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
</style>