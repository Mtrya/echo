<template>
  <div class="quick-response">
    <!-- Question Playback Phase -->
    <div v-if="phase === 'playback'" class="playback-phase">
      <div class="playback-icon">🎧</div>
      <div class="playback-text">
        {{ translate('questions.quickResponse.listening') }}
      </div>
      <div class="status-text">
        {{ audioStatus }}
      </div>
    </div>

    <!-- Get Ready Phase -->
    <div v-else-if="phase === 'ready'" class="ready-phase">
      <div class="ready-icon">⏱️</div>
      <div class="ready-text">
        {{ translate('questions.quickResponse.getReady') }}
      </div>
      <div class="countdown-text">
        {{ countdownText }}
      </div>
    </div>

    <!-- Recording Phase -->
    <div v-else-if="phase === 'recording'" class="recording-phase">
      <div class="recording-instruction">
        {{ translate('questions.quickResponse.speakNow') }}
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
        {{ translate('questions.quickResponse.stopRecording') }}
      </button>
    </div>

    <!-- Auto-submit Phase -->
    <div v-else-if="phase === 'auto-submit'" class="auto-submit-phase">
      <div class="auto-submit-text">
        {{ translate('questions.quickResponse.timeUp') }}
      </div>
    </div>

    <!-- Hidden audio player for question audio -->
    <audio ref="audioPlayer" hidden></audio>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useTranslations } from '../composables/useTranslations.js'
import Mp3Recorder, { blobToBase64 } from '../utils/mp3Recorder.js'

export default {
  name: 'QuickResponse',
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
    const phase = ref('playback') // 'playback', 'ready', 'recording', 'auto-submit'

    // Timer and audio
    const timeRemaining = ref(0)
    const audioPlayer = ref(null)
    const audioStatus = ref('Preparing...')
    const countdownText = ref('3')

    // Countdown timer
    let readyTimer = null
    let recordingTimer = null

    // MP3 recorder
    let mp3Recorder = null

    // Initialize on component mount
    onMounted(async () => {
      await initializeQuestion()
    })

    // Watch for question changes and reset state
    watch(() => props.currentQuestion, async (newQuestion, oldQuestion) => {
      if (newQuestion && newQuestion.id !== oldQuestion?.id) {
        console.log('QuickResponse: Question changed from', oldQuestion?.id, 'to', newQuestion.id)
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
      console.log('QuickResponse: Resetting component state')

      // Clean up any existing resources
      cleanup()

      // Reset all reactive state
      phase.value = 'playback'
      timeRemaining.value = 0
      audioStatus.value = 'Preparing...'
      countdownText.value = '3'

      console.log('QuickResponse: State reset complete')
    }

    // Initialize the question flow
    const initializeQuestion = async () => {
      try {
        // Initialize audio recording permissions
        await initializeAudio()

        // Start playback phase
        await startPlaybackPhase()

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

    // Start playback phase
    const startPlaybackPhase = async () => {
      phase.value = 'playback'

      if (props.currentQuestion.audio_file_path) {
        // Play question audio
        audioStatus.value = 'Playing question...'
        await playQuestionAudio()
      } else {
        // No audio file, this shouldn't happen for quick_response
        console.error('QuickResponse question missing audio file')
        throw new Error('No audio file available for quick response question')
      }

      // Start ready phase
      startReadyPhase()
    }

    // Play question audio
    const playQuestionAudio = async () => {
      try {
        if (audioPlayer.value) {
          audioPlayer.value.src = props.currentQuestion.audio_file_path

          return new Promise((resolve, reject) => {
            audioPlayer.value.onended = resolve
            audioPlayer.value.onerror = reject
            audioPlayer.value.play().catch(reject)
          })
        }
      } catch (error) {
        console.error('Failed to play question audio:', error)
        throw error
      }
    }

    // Start ready phase
    const startReadyPhase = () => {
      phase.value = 'ready'
      let countdown = 3

      // Start countdown timer
      readyTimer = setInterval(() => {
        countdown--
        countdownText.value = countdown.toString()

        if (countdown <= 0) {
          clearInterval(readyTimer)
          readyTimer = null
          startRecordingPhase()
        }
      }, 1000)
    }

    // Start recording phase
    const startRecordingPhase = async () => {
      phase.value = 'recording'
      timeRemaining.value = props.currentQuestion.time_limit || 15

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
      if (readyTimer) {
        clearInterval(readyTimer)
        readyTimer = null
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
      audioPlayer,
      audioStatus,
      countdownText,
      stopRecording,
      translate
    }
  }
}
</script>

<style scoped>
.quick-response {
  text-align: center;
  max-width: 600px;
  margin: 0 auto;
  padding: 2rem;
}

/* Playback Phase */
.playback-phase {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.playback-icon {
  font-size: 4rem;
  margin-bottom: 2rem;
  animation: pulse 2s infinite;
}

.playback-text {
  font-size: 1.8rem;
  color: #374151;
  margin-bottom: 2rem;
  font-weight: 600;
}

.status-text {
  font-size: 1.2rem;
  color: #16a34a;
  font-weight: 600;
}

/* Ready Phase */
.ready-phase {
  min-height: 400px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.ready-icon {
  font-size: 3rem;
  margin-bottom: 2rem;
}

.ready-text {
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
  min-height: 400px;
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
  min-height: 300px;
  display: flex;
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