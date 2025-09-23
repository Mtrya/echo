<template>
  <div class="translation">
    <!-- Display Phase -->
    <div v-if="phase === 'display'" class="display-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="status-text">
        {{ audioStatus }}
      </div>
    </div>

    <!-- Thinking Phase -->
    <div v-else-if="phase === 'thinking'" class="thinking-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="thinking-text">
        Get ready to translate...
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
        🎤 Speak your English translation now
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
        Stop Recording
      </button>
    </div>

    <!-- Auto-submit Phase -->
    <div v-else-if="phase === 'auto-submit'" class="auto-submit-phase">
      <div class="chinese-text">
        {{ currentQuestion.text }}
      </div>
      <div class="auto-submit-text">
        Time's up! Submitting your answer...
      </div>
    </div>

    <!-- Hidden audio player for instruction audio -->
    <audio ref="audioPlayer" hidden></audio>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'

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
    // Phase management
    const phase = ref('display') // 'display', 'thinking', 'recording', 'auto-submit'

    // Timer and audio
    const timeRemaining = ref(0)
    const audioPlayer = ref(null)
    const audioStatus = ref('Preparing...')
    const countdownText = ref('3')

    // Media recorder and audio stream
    let mediaRecorder = null
    let audioChunks = []
    let audioStream = null

    // Timer references
    let thinkingTimer = null
    let recordingTimer = null
    let displayTimer = null

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
      audioStatus.value = 'Preparing...'
      countdownText.value = '3'

      // Reset audio chunks
      audioChunks = []

      console.log('Translation: State reset complete')
    }

    // Initialize the question flow
    const initializeQuestion = async () => {
      try {
        // Initialize audio recording permissions
        await initializeAudio()

        // Start display phase
        await startDisplayPhase()

      } catch (error) {
        console.error('Failed to initialize question:', error)
        submitEmptyAnswer()
      }
    }

    // Initialize audio recording permissions
    const initializeAudio = async () => {
      try {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true })

        mediaRecorder = new MediaRecorder(audioStream)

        mediaRecorder.ondataavailable = (event) => {
          audioChunks.push(event.data)
        }

        mediaRecorder.onstop = () => {
          // Recording stopped, submit the answer
          submitAnswer()
        }

        console.log('Audio initialized successfully')
      } catch (error) {
        console.error('Failed to initialize audio:', error)
        throw error
      }
    }

    // Start display phase
    const startDisplayPhase = async () => {
      phase.value = 'display'

      if (props.currentQuestion.audio_file_path) {
        // Play instruction audio
        audioStatus.value = 'Playing instructions...'
        await playInstructionAudio()
      } else {
        // No audio file, wait 5 seconds
        audioStatus.value = 'Get ready to translate...'
        await new Promise(resolve => {
          displayTimer = setTimeout(resolve, 5000)
        })
      }

      // Start thinking phase
      startThinkingPhase()
    }

    // Play instruction audio
    const playInstructionAudio = async () => {
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
        console.error('Failed to play instruction audio:', error)
        // Continue with 5-second fallback
        await new Promise(resolve => {
          displayTimer = setTimeout(resolve, 5000)
        })
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
    const startRecordingPhase = () => {
      phase.value = 'recording'

      // Calculate time: half of time_limit for thinking (already used), half for recording
      const totalTime = props.currentQuestion.time_limit || 30
      timeRemaining.value = Math.floor(totalTime / 2)

      // Start recording
      if (mediaRecorder && mediaRecorder.state === 'inactive') {
        audioChunks = []
        mediaRecorder.start()
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
    const stopRecording = () => {
      if (recordingTimer) {
        clearInterval(recordingTimer)
        recordingTimer = null
      }

      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }

      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop())
      }
    }

    // Auto-submit when time runs out
    const autoSubmit = () => {
      phase.value = 'auto-submit'
      stopRecording()

      // Brief delay to show auto-submit message
      setTimeout(() => {
        submitAnswer()
      }, 2000)
    }

    // Submit the recorded answer
    const submitAnswer = async () => {
      try {
        // Create audio blob from recorded chunks
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' })

        // Convert blob to base64
        const base64Audio = await blobToBase64(audioBlob)

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
          console.log('Answer submitted successfully')

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

    // Submit empty answer (when recording fails)
    const submitEmptyAnswer = () => {
      emit('complete', {
        sessionId: props.sessionId,
        questionIndex: props.currentQuestion.question_index,
        success: false,
        error: 'Recording failed'
      })
    }

    // Convert blob to base64
    const blobToBase64 = (blob) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onloadend = () => {
          // Extract base64 data from the result (remove data URL prefix)
          const base64 = reader.result.split(',')[1]
          resolve(base64)
        }
        reader.onerror = reject
        reader.readAsDataURL(blob)
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

      if (displayTimer) {
        clearTimeout(displayTimer)
        displayTimer = null
      }

      if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
      }

      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop())
      }
    }

    return {
      phase,
      timeRemaining,
      audioPlayer,
      audioStatus,
      countdownText,
      stopRecording
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