<template>
  <div class="instruction-content">
  <p class="instruction-text">{{ instruction.text }}</p>

  <!-- Hidden audio player for instruction audio -->
  <audio ref="audioPlayer" hidden></audio>
</div>
</template>

<script>
import { ref, onMounted, onUnmounted } from 'vue'

export default {
  name: 'InstructionPage',
  props: {
    instruction: {
      type: Object,
      required: true
    },
    audioFile: {
      type: String,
      default: null
    },
    questionType: {
      type: String,
      required: true
    }
  },
  emits: ['start-section'],
  setup(props, { emit }) {
    const audioPlayer = ref(null)
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

    const playInstructionAudio = () => {
      return new Promise((resolve, reject) => {
        if (props.audioFile && audioPlayer.value) {
          console.log(`▶️ Playing instruction audio: ${props.audioFile}`)
          const player = audioPlayer.value

          // Force complete reset of audio element (simulate HMR refresh)
          const forceResetAudio = () => {
            console.log(`🔄 Force resetting audio element for ${componentId}`)

            // Remove from DOM
            const parent = player.parentNode
            if (parent) {
              parent.removeChild(player)
            }

            // Create fresh audio element
            const freshPlayer = document.createElement('audio')
            freshPlayer.hidden = true
            freshPlayer.id = `audio-${componentId}`

            // Add back to DOM
            if (parent) {
              parent.appendChild(freshPlayer)
            }

            // Update ref
            audioPlayer.value = freshPlayer

            return freshPlayer
          }

          // Clean up any existing audio state
          player.pause()
          player.currentTime = 0
          player.src = ''

          let playTimeout = null
          let isStuck = false
          let stuckTime = 0

          const cleanupAndResolve = () => {
            clearTimeout(playTimeout)
            player.removeEventListener('ended', cleanupAndResolve)
            player.removeEventListener('error', cleanupAndReject)
            player.removeEventListener('timeupdate', checkProgress)
            resolve()
          }

          const cleanupAndReject = (err) => {
            clearTimeout(playTimeout)
            player.removeEventListener('ended', cleanupAndResolve)
            player.removeEventListener('error', cleanupAndReject)
            player.removeEventListener('timeupdate', checkProgress)
            console.error('❌ Audio play error:', err)
            reject(err)
          }

          const checkProgress = () => {
            if (!isStuck && player.currentTime > 0) {
              console.log(`📊 Audio progress: ${player.currentTime.toFixed(2)}s`)
              stuckTime = player.currentTime // Track current position
            }
          }

          const handleStuckAudio = () => {
            console.log(`⚠️ Audio appears stuck at ${stuckTime.toFixed(2)}s, attempting reset for ${componentId}`)
            isStuck = true

            // Force reset audio element
            const freshPlayer = forceResetAudio()

            // Set up event listeners on the fresh player
            freshPlayer.addEventListener('ended', cleanupAndResolve)
            freshPlayer.addEventListener('error', cleanupAndReject)

            // Try playing with fresh audio element, resuming from stuck position
            setTimeout(() => {
              try {
                freshPlayer.src = props.audioFile
                freshPlayer.load()

                // Set current time to where we got stuck (with a small offset to avoid getting stuck again)
                freshPlayer.currentTime = stuckTime + 0.075

                freshPlayer.play().then(() => {
                  console.log(`✅ Audio recovered after reset, resuming from ${stuckTime.toFixed(2)}s for ${componentId}`)
                }).catch(() => {
                  console.log(`❌ Reset failed, proceeding anyway for ${componentId}`)
                  cleanupAndResolve() // Just proceed if reset fails
                })
              } catch (err) {
                console.log(`❌ Reset failed completely, proceeding anyway for ${componentId}`)
                cleanupAndResolve() // Just proceed if everything fails
              }
            }, 100)
          }

          // Set up event listeners first
          player.addEventListener('ended', cleanupAndResolve)
          player.addEventListener('error', cleanupAndReject)
          player.addEventListener('timeupdate', checkProgress)

          // Set up stuck detection - if no progress for 3 seconds, force reset
          playTimeout = setTimeout(handleStuckAudio, 3000)

          // Then set source and load
          player.src = props.audioFile
          player.load()

          // Finally play
          player.play().catch(cleanupAndReject)
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

    return {
      audioPlayer,
      isProceeding,
      instruction: props.instruction
    }
  }
}
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
