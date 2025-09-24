<template>
  <div class="audio-test">
    <h2>Audio Test</h2>
    <p>Please test your microphone before starting the exam.</p>
    
    <!-- Audio Playback Button -->
    <button @click="playTestAudio" class="btn btn-primary">
      {{ isPlaying ? 'Playing...' : 'Play Test Audio' }}
    </button>
    
    <!-- Recording Button -->
    <button @click="toggleRecording" class="btn" :class="isRecording ? 'btn-danger' : 'btn-secondary'">
      {{ isRecording ? 'Stop Recording' : 'Start Recording' }}
    </button>
    
    <!-- Playback Recording Button -->
    <button v-if="recordedAudio" @click="playRecordedAudio" class="btn btn-secondary">
      {{ isPlayingRecording ? 'Playing Recording...' : 'Play Recording' }}
    </button>
    
    <!-- Start Exam Button -->
    <button
      @click="startExam"
      class="btn btn-primary"
      :disabled="!canStartExam()"
    >
      {{ getStartButtonText() }}
    </button>
    
    <!-- Audio elements (hidden) -->
    <audio ref="testAudioPlayer" hidden></audio>
    <audio ref="recordedAudioPlayer" hidden></audio>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import Mp3Recorder from '../utils/mp3Recorder.js'

export default {
  name: 'AudioTest',
  props: {
    sessionId: {
      type: String,
      required: true
    }
  },
  emits: ['complete'],
  setup(props, { emit }) {
    // Audio elements
    const testAudioPlayer = ref(null)
    const recordedAudioPlayer = ref(null)
    
    // State management
    const isPlaying = ref(false)
    const isRecording = ref(false)
    const isPlayingRecording = ref(false)
    const recordedAudio = ref(null)
    
    // MP3 recorder
    let mp3Recorder = null

    // Initialize audio context on component mount
    onMounted(async () => {
      await initializeAudio()
      // Start checking session status
      checkSessionStatus()
    })

    // Initialize audio permissions and setup
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
        alert('Please allow microphone access to use this feature')
      }
    }

    // Play test audio (we'll use a simple beep for now)
    const playTestAudio = async () => {
      if (isPlaying.value) return
      
      try {
        isPlaying.value = true
        
        // Create a simple beep sound using Web Audio API
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()
        
        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime) // 800 Hz beep
        oscillator.type = 'sine'
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 1)
        
        oscillator.start(audioContext.currentTime)
        oscillator.stop(audioContext.currentTime + 1)
        
        setTimeout(() => {
          isPlaying.value = false
        }, 1000)
        
      } catch (error) {
        console.error('Failed to play test audio:', error)
        isPlaying.value = false
      }
    }

    // Toggle recording on/off
    const toggleRecording = async () => {
      if (isRecording.value) {
        // Stop recording
        if (mp3Recorder) {
          try {
            const mp3Blob = await mp3Recorder.stop()
            recordedAudio.value = URL.createObjectURL(mp3Blob)
            mp3Recorder = null  // Reset for next recording

            // Auto-play the recording after stopping
            setTimeout(() => {
              playRecordedAudio()
            }, 500)
          } catch (error) {
            console.error('Failed to stop MP3 recording:', error)
          }
        }
        isRecording.value = false
      } else {
        // Start recording
        if (mp3Recorder) {
          try {
            await mp3Recorder.start()
            isRecording.value = true
          } catch (error) {
            console.error('Failed to start MP3 recording:', error)
          }
        } else {
          // Create new recorder instance
          mp3Recorder = new Mp3Recorder()
          try {
            await mp3Recorder.start()
            isRecording.value = true
          } catch (error) {
            console.error('Failed to start MP3 recording:', error)
          }
        }
      }
    }

    // Play the recorded audio
    const playRecordedAudio = () => {
      if (!recordedAudio.value || isPlayingRecording.value) return
      
      try {
        isPlayingRecording.value = true
        
        if (recordedAudioPlayer.value) {
          recordedAudioPlayer.value.src = recordedAudio.value
          recordedAudioPlayer.value.onended = () => {
            isPlayingRecording.value = false
          }
          recordedAudioPlayer.value.play()
        }
      } catch (error) {
        console.error('Failed to play recorded audio:', error)
        isPlayingRecording.value = false
      }
    }

    // Audio generation status
    const audioGenerationStatus = ref('unknown') // 'unknown', 'generating', 'completed'
    const isCheckingStatus = ref(false)

    // Check session status (unified endpoint)
    const checkSessionStatus = async () => {
      if (isCheckingStatus.value) return

      try {
        isCheckingStatus.value = true
        const response = await fetch(`/session/${props.sessionId}/status`)
        const data = await response.json()

        if (data.audio_generation === 'completed') {
          audioGenerationStatus.value = 'completed'
        } else if (data.audio_generation === 'generating') {
          audioGenerationStatus.value = 'generating'
          // Continue checking after a delay
          setTimeout(checkSessionStatus, 2000)
        } else {
          audioGenerationStatus.value = 'unknown'
        }
      } catch (error) {
        console.error('Failed to check session status:', error)
        audioGenerationStatus.value = 'unknown'
      } finally {
        isCheckingStatus.value = false
      }
    }

    // Start the exam (navigate to first question)
    const startExam = () => {
      console.log('AudioTest: Starting exam, emitting complete event')
      emit('complete', {
        sessionId: props.sessionId,
        audioTestPassed: true
      })
    }

    // Check if start button should be enabled
    const canStartExam = () => {
      return audioGenerationStatus.value === 'completed' || audioGenerationStatus.value === 'unknown'
    }

    // Get start button text
    const getStartButtonText = () => {
      if (audioGenerationStatus.value === 'generating') {
        return 'Generating Audio... Please Wait'
      }
      return 'Start Exam'
    }

    return {
      testAudioPlayer,
      recordedAudioPlayer,
      isPlaying,
      isRecording,
      isPlayingRecording,
      recordedAudio,
      audioGenerationStatus,
      playTestAudio,
      toggleRecording,
      playRecordedAudio,
      startExam,
      canStartExam,
      getStartButtonText
    }
  }
}
</script>

<style scoped>
.audio-test {
  text-align: center;
  max-width: 500px;
  margin: 0 auto;
  padding: 2rem;
}

.audio-test h2 {
  color: #16a34a;
  margin-bottom: 1rem;
}

.audio-test p {
  color: #374151;
  margin-bottom: 2rem;
}

/* Button Layout */
.audio-test .btn {
  margin: 0.5rem;
  min-width: 200px;
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

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-danger:hover {
  background: #b91c1c;
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}
</style>