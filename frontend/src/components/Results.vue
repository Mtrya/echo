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
        <div class="placeholder-message">
          <h3>📊 Detailed Results Coming Soon</h3>
          <p>This page will show:</p>
          <ul>
            <li>✓ Your overall score and percentage</li>
            <li>✓ Each question with your answer</li>
            <li>✓ Correct answers and explanations</li>
            <li>✓ Feedback for improvement</li>
            <li>✓ Time spent on each question</li>
          </ul>
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

    // Load results when component mounts
    onMounted(async () => {
      await loadResults()
    })

    // Load results from backend
    const loadResults = async () => {
      try {
        const response = await fetch(`/session/${props.sessionId}/results`)
        if (response.ok) {
          const data = await response.json()
          resultsData.value = data
          score.value = data.total_score
          totalQuestions.value = data.max_score
          percentage.value = data.percentage
          console.log('Results loaded:', data)
        } else {
          console.error('Failed to load results:', response.status)
          // Use placeholder data if backend fails
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