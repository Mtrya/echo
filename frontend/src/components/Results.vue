<template>
  <div class="results">
    <div class="results-container">
      <div class="results-header">
        <h1>🎉 Exam Completed!</h1>
        <p>Congratulations on finishing your exam</p>
      </div>

      <div class="score-section">
        <div class="score-circle">
          <div class="score-number">{{ score || '?' }}</div>
          <div class="score-label">out of {{ totalQuestions || '?' }}</div>
        </div>
      </div>

      <div class="results-details">
        <!-- Show processing status -->
        <div v-if="processingStatus === 'processing'" class="processing-message">
          <h3>⏳ Processing Your Answers</h3>
          <p>We're analyzing your responses and calculating your scores...</p>
          <div class="loading-indicator">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
          </div>
        </div>

        <!-- Debug: Show raw API response -->
        <div v-else-if="resultsData" class="debug-results">
          <h3>🔧 Debug: API Response</h3>
          <pre>{{ JSON.stringify(resultsData, null, 2) }}</pre>
        </div>

        <div v-else class="placeholder-message">
          <h3>📊 {{ processingStatus === 'unknown' ? 'Connecting to Server...' : 'Loading Results...' }}</h3>
          <p>{{ processingStatus === 'unknown' ? 'Establishing connection to backend...' : 'Finalizing your exam results...' }}</p>
        </div>
      </div>

      <div class="results-actions">
        <button @click="startNewExam" class="btn btn-primary">
          📝 Start New Exam
        </button>
        <button @click="goHome" class="btn btn-secondary">
          🏠 Back to Home
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'Results',
  props: {
    sessionId: {
      type: String,
      required: true
    }
  },
  setup(props, { emit }) {
    const score = ref(null)
    const totalQuestions = ref(null)
    const percentage = ref(null)
    const resultsData = ref(null)
    const processingStatus = ref('unknown') // 'unknown', 'processing', 'idle'
    const isCheckingStatus = ref(false)

    // Start checking status when component mounts
    onMounted(async () => {
      await checkSessionStatus()
    })

    // Check session status (polling)
    const checkSessionStatus = async () => {
      if (isCheckingStatus.value) return

      try {
        isCheckingStatus.value = true
        console.log('Checking session status for:', props.sessionId)
        const response = await fetch(`/session/${props.sessionId}/status`)
        const data = await response.json()

        console.log('Session status:', data)

        if (data.processing === 'idle') {
          // Processing is complete, load results
          processingStatus.value = 'idle'
          await loadResults()
        } else {
          // Still processing or unknown status, check again after 2 seconds
          processingStatus.value = data.processing || 'unknown'
          setTimeout(checkSessionStatus, 2000)
        }
      } catch (error) {
        console.error('Failed to check session status:', error)
        processingStatus.value = 'unknown'
        setTimeout(checkSessionStatus, 2000)
      } finally {
        isCheckingStatus.value = false
      }
    }

    // Load results from backend (only called when processing is complete)
    const loadResults = async () => {
      try {
        console.log('Loading results for session:', props.sessionId)
        const response = await fetch(`/session/${props.sessionId}/results`)
        console.log('Response status:', response.status)

        if (response.ok) {
          const data = await response.json()
          console.log('Results loaded:', data)
          resultsData.value = data
          score.value = data.total_score
          totalQuestions.value = data.max_score
          percentage.value = data.percentage
        } else {
          const errorText = await response.text()
          console.error('Failed to load results:', response.status, errorText)

          // If exam is not completed, go back to checking status
          if (response.status === 400 && errorText.includes('Exam not completed')) {
            console.log('Exam not completed yet, resuming status check...')
            processingStatus.value = 'processing'
            setTimeout(checkSessionStatus, 2000)
            return
          }

          // Use placeholder data if backend fails for other reasons
          score.value = '?'
          totalQuestions.value = '?'
        }
      } catch (error) {
        console.error('Error loading results:', error)
        // Use placeholder data if there's an error
        score.value = '?'
        totalQuestions.value = '?'
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

    return {
      score,
      totalQuestions,
      percentage,
      resultsData,
      processingStatus,
      startNewExam,
      goHome
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

.results-actions {
  margin-top: 3rem;
  display: flex;
  gap: 1rem;
  justify-content: center;
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