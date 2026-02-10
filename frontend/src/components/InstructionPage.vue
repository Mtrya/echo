<template>
  <div v-if="props.instruction" class="instruction-content">
    <p class="instruction-text">{{ props.instruction.text }}</p>

    <!-- Hidden audio player for instruction audio -->
    <audio ref="audioPlayer" hidden></audio>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import type { Instruction } from '@/types'

interface Props {
  instruction: Instruction | null
  audioFile: string | null
  questionType: string | null
}

interface Emits {
  (e: 'start-section'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const audioPlayer = ref<HTMLAudioElement | null>(null)
const isProceeding = ref(false)

// Generate unique component ID for logging
const componentId = Math.random().toString(36).substr(2, 9)
console.log(`📱 InstructionPage [${componentId}] setup called for ${props.questionType}`)
console.log(`📱 InstructionPage [${componentId}] instruction text:`, props.instruction?.text?.substring(0, 50))
console.log(`📱 InstructionPage [${componentId}] audio file:`, props.audioFile)

onMounted(() => {
  console.log(`🔧 InstructionPage [${componentId}] mounted for ${props.questionType}, audioFile:`, props.audioFile)
  if (props.audioFile) {
    // Play instruction audio and proceed when complete
    playInstructionAudio().then(() => {
      // Audio completed successfully, proceed after short delay
      console.log(`✅ Instruction audio finished for ${props.questionType}`)
      setTimeout(() => {
        proceedToSection()
      }, 500)
    }).catch((error) => {
      console.log(`❌ Audio play failed for ${props.questionType}, proceeding anyway:`, error)
      // 2-second fallback when audio fails
      setTimeout(() => {
        proceedToSection()
      }, 2000)
    })
  } else {
    // No audio file, proceed after 3 seconds
    console.log(`InstructionPage [${componentId}] No audio file, proceeding after 3 seconds`)
    setTimeout(() => {
      proceedToSection()
    }, 3000)
  }
})

const playInstructionAudio = (): Promise<void> => {
  return new Promise((resolve, reject) => {
    if (props.audioFile && audioPlayer.value) {
      console.log(`▶️ Playing instruction audio: ${props.audioFile}`)
      const player = audioPlayer.value

      const handleAudioEnd = () => {
        player.removeEventListener('ended', handleAudioEnd)
        player.removeEventListener('error', handleAudioError)
        resolve()
      }

      const handleAudioError = (err: Event) => {
        player.removeEventListener('ended', handleAudioEnd)
        player.removeEventListener('error', handleAudioError)
        console.error('❌ Audio play error:', err)
        reject(err)
      }

      // Set up event listeners
      player.addEventListener('ended', handleAudioEnd)
      player.addEventListener('error', handleAudioError)

      // Set source and play
      player.src = props.audioFile
      player.play().catch(handleAudioError)
    } else {
      const msg = 'InstructionPage: No audio file or audio player available.'
      console.warn(msg)
      reject(new Error(msg))
    }
  })
}

const proceedToSection = () => {
  if (!isProceeding.value) {
    console.log('Proceeding to section:', props.questionType)
    isProceeding.value = true
    emit('start-section')
  }
}

// Clean up when component is destroyed
onUnmounted(() => {
  console.log(`🗑️ InstructionPage [${componentId}] unmounting for ${props.questionType}`)
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.src = ''
  }
})
</script>

<style scoped>
.instruction-content {
  background: rgba(255, 255, 255, 0.9);
  border-radius: 15px;
  padding: 2rem;
  max-width: 600px;
  width: 90%;
  text-align: center;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  margin: 0 auto;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.instruction-text {
  color: #374151;
  font-size: 1.8rem;
  line-height: 1.5;
  margin: 0;
  font-weight: 600;
}

.audio-section {
  margin-top: 20px;
}

/* Responsive design */
@media (max-width: 600px) {
  .instruction-content {
    padding: 20px;
    margin: 20px;
  }

  .instruction-text {
    font-size: 18px;
  }
}
</style>
