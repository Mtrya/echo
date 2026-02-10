<template>
  <div class="audio-test">
    <div class="audio-test-card">
      <!-- Test Audio Section -->
      <div class="test-section">
        <div class="section-title">{{ translate('audioTest.testSpeaker') }}</div>
        <button @click="playTestAudio" class="btn btn-primary" :disabled="isPlaying">
          {{ isPlaying ? translate('audioTest.playing') : translate('audioTest.playTestAudio') }}
        </button>
      </div>

      <!-- Reading Practice Section -->
      <div class="reading-section">
        <div class="section-title">{{ translate('audioTest.practiceReading') }}</div>
        <div class="reading-card">
          <div class="reading-text">
            {{ translate('audioTest.readingText') }}
          </div>
        </div>
      </div>

      <!-- Recording Section -->
      <div class="recording-section">
        <div class="section-title">{{ translate('audioTest.testMicrophone') }}</div>
        <div class="recording-controls">
          <button @click="toggleRecording" class="btn" :class="isRecording ? 'btn-danger' : 'btn-secondary'">
            {{ isRecording ? translate('audioTest.stopRecording') : translate('audioTest.startRecording') }}
          </button>

          <!-- Recording Visual Feedback -->
          <div v-if="isRecording" class="recording-visual">
            <div class="recording-indicator">●</div>
            <div class="recording-timer">{{ formatTime(recordingTime) }}</div>
            <div class="waveform">
              <div v-for="i in 8" :key="i" class="wave-bar" :style="{ height: getWaveHeight(i) + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- Playback Recording -->
        <div v-if="recordedAudio" class="playback-section">
          <button @click="playRecordedAudio" class="btn btn-secondary" :disabled="isPlayingRecording">
            {{ isPlayingRecording ? translate('audioTest.playingRecording') : translate('audioTest.playRecording') }}
          </button>
        </div>
      </div>

      <!-- Start Exam Section -->
      <div class="start-section">
        <button
          @click="startExam"
          class="btn btn-primary start-btn"
          :disabled="!canStartExam()"
        >
          {{ getStartButtonText() }}
        </button>
      </div>
    </div>

    <!-- Audio elements (hidden) -->
    <audio ref="testAudioPlayer" hidden></audio>
    <audio ref="recordedAudioPlayer" hidden></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTranslations } from '@/composables/useTranslations'
import { apiUrl } from '@/utils/api'
import { Mp3Recorder } from '@/utils/mp3Recorder'

interface Props {
  sessionId: string
}

interface Emits {
  (e: 'complete', result: { sessionId: string; audioTestPassed: boolean }): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const { translate } = useTranslations()

// Audio elements
const testAudioPlayer = ref<HTMLAudioElement | null>(null)
const recordedAudioPlayer = ref<HTMLAudioElement | null>(null)

// State management
const isPlaying = ref(false)
const isRecording = ref(false)
const isPlayingRecording = ref(false)
const recordedAudio = ref<string | null>(null)
const recordingTime = ref(0)
const recordingInterval = ref<ReturnType<typeof setInterval> | null>(null)

// MP3 recorder
let mp3Recorder: Mp3Recorder | null = null

// Audio context for test beep
let testAudioContext: AudioContext | null = null

// Audio generation status
const audioGenerationStatus = ref<'unknown' | 'generating' | 'completed'>('unknown')
const isCheckingStatus = ref(false)

// Initialize audio context on component mount
onMounted(async () => {
  await initializeAudio()
  // Start checking session status
  checkSessionStatus()
})

// Cleanup on component unmount
onUnmounted(() => {
  cleanup()
})

// Initialize audio permissions and setup
const initializeAudio = async (): Promise<void> => {
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
    alert(translate('audioTest.microphoneAccess'))
  }
}

// Play test audio using pre-recorded voice file
const playTestAudio = async (): Promise<void> => {
  if (isPlaying.value) return

  try {
    isPlaying.value = true

    if (testAudioPlayer.value) {
      testAudioPlayer.value.src = apiUrl('/audio_cache/tts/audio-test.mp3')
      testAudioPlayer.value.onended = () => {
        isPlaying.value = false
      }
      await testAudioPlayer.value.play()
    }
  } catch (error) {
    console.error('Failed to play test audio:', error)
    // Fallback to beep if audio file fails
    playBeepSound()
    isPlaying.value = false
  }
}

// Fallback beep sound
const playBeepSound = (): void => {
  try {
    testAudioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = testAudioContext.createOscillator()
    const gainNode = testAudioContext.createGain()

    oscillator.connect(gainNode)
    gainNode.connect(testAudioContext.destination)

    oscillator.frequency.setValueAtTime(800, testAudioContext.currentTime)
    oscillator.type = 'sine'

    gainNode.gain.setValueAtTime(0.3, testAudioContext.currentTime)
    gainNode.gain.exponentialRampToValueAtTime(0.01, testAudioContext.currentTime + 1)

    oscillator.start(testAudioContext.currentTime)
    oscillator.stop(testAudioContext.currentTime + 1)

    setTimeout(() => {
      if (testAudioContext) {
        testAudioContext.close()
        testAudioContext = null
      }
    }, 1000)
  } catch (error) {
    console.error('Failed to play beep sound:', error)
  }
}

// Toggle recording on/off
const toggleRecording = async (): Promise<void> => {
  if (isRecording.value) {
    // Stop recording
    if (mp3Recorder) {
      try {
        const mp3Blob = await mp3Recorder.stop()
        recordedAudio.value = URL.createObjectURL(mp3Blob)
        mp3Recorder = null  // Reset for next recording

        // Stop recording timer
        if (recordingInterval.value) {
          clearInterval(recordingInterval.value)
          recordingInterval.value = null
        }
        recordingTime.value = 0

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
        startRecordingTimer()
      } catch (error) {
        console.error('Failed to start MP3 recording:', error)
      }
    } else {
      // Create new recorder instance
      mp3Recorder = new Mp3Recorder()
      try {
        await mp3Recorder.start()
        isRecording.value = true
        startRecordingTimer()
      } catch (error) {
        console.error('Failed to start MP3 recording:', error)
      }
    }
  }
}

// Start recording timer
const startRecordingTimer = (): void => {
  recordingTime.value = 0
  recordingInterval.value = setInterval(() => {
    recordingTime.value++
  }, 1000)
}

// Format time as MM:SS
const formatTime = (seconds: number): string => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// Generate waveform height for visual effect
const getWaveHeight = (index: number): number => {
  if (!isRecording.value) return 20
  // Create a simple wave effect
  const base = 30
  const variation = Math.sin((Date.now() / 200) + (index * 0.5)) * 20
  return Math.max(20, Math.min(80, base + variation))
}

// Play the recorded audio
const playRecordedAudio = (): void => {
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

// Cleanup resources
const cleanup = (): void => {
  // Clean up test audio context
  if (testAudioContext) {
    testAudioContext.close()
    testAudioContext = null
  }

  // Clean up MP3 recorder
  if (mp3Recorder) {
    try {
      mp3Recorder.cleanup()
    } catch (error) {
      console.error('Error cleaning up MP3 recorder:', error)
    }
    mp3Recorder = null
  }

  // Clean up recorded audio URL
  if (recordedAudio.value) {
    URL.revokeObjectURL(recordedAudio.value)
    recordedAudio.value = null
  }

  // Clean up recording timer
  if (recordingInterval.value) {
    clearInterval(recordingInterval.value)
    recordingInterval.value = null
  }
}

// Check session status (unified endpoint)
const checkSessionStatus = async (): Promise<void> => {
  if (isCheckingStatus.value) return

  try {
    isCheckingStatus.value = true
    const response = await fetch(apiUrl(`/session/${props.sessionId}/audio-status`))
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
const startExam = (): void => {
  console.log('AudioTest: Starting exam, emitting complete event')
  emit('complete', {
    sessionId: props.sessionId,
    audioTestPassed: true
  })
}

// Check if start button should be enabled
const canStartExam = (): boolean => {
  return audioGenerationStatus.value === 'completed' || audioGenerationStatus.value === 'unknown'
}

// Get start button text
const getStartButtonText = (): string => {
  if (audioGenerationStatus.value === 'generating') {
    return translate('audioTest.generatingAudio')
  }
  return translate('audioTest.startExam')
}
</script>

<style scoped>
.audio-test {
  text-align: center;
  max-width: 500px;
  margin: 0 auto;
  padding: 2rem;
}

.audio-test-card {
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07), 0 1px 3px rgba(0, 0, 0, 0.06);
  padding: 1.5rem;
  border: 1px solid rgba(22, 163, 74, 0.1);
}

.card-header {
  margin-bottom: 1.5rem;
}

.card-header h2 {
  color: #16a34a;
  margin-bottom: 0.5rem;
  font-size: 1.8rem;
  font-weight: 700;
}

.card-header p {
  color: #374151;
  font-size: 1rem;
  line-height: 1.5;
}

.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #16a34a;
  margin-bottom: 1rem;
  text-align: center;
}

.test-section,
.reading-section,
.recording-section,
.start-section {
  margin-bottom: 1.5rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(22, 163, 74, 0.1);
  text-align: center;
}

.test-section:last-child,
.reading-section:last-child,
.recording-section:last-child,
.start-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.reading-card {
  background: rgba(22, 163, 74, 0.03);
  border: 1px solid rgba(22, 163, 74, 0.1);
  border-radius: 12px;
  padding: 1rem;
  text-align: left;
}

.reading-text {
  font-size: 1rem;
  line-height: 1.5;
  color: #374151;
  font-weight: 500;
}

.recording-controls {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.recording-visual {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: rgba(22, 163, 74, 0.05);
  border-radius: 12px;
  min-width: 300px;
}

.recording-indicator {
  color: #dc2626;
  font-size: 1.5rem;
  animation: pulse 1s infinite;
}

.recording-timer {
  font-family: 'Courier New', monospace;
  font-size: 1.2rem;
  font-weight: 600;
  color: #374151;
  min-width: 60px;
}

.waveform {
  display: flex;
  align-items: center;
  gap: 3px;
  flex: 1;
}

.wave-bar {
  width: 4px;
  background: linear-gradient(to top, #16a34a, #22c55e);
  border-radius: 2px;
  transition: height 0.1s ease;
  min-height: 4px;
}

.playback-section {
  margin-top: 1rem;
}

.start-btn {
  min-width: 250px;
  font-size: 1.1rem;
  padding: 1.2rem 2rem;
}

/* Button Layout */
.audio-test .btn {
  margin: 0.5rem auto;
  min-width: 200px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
