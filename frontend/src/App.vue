<template>
  <div class="app">
    <!-- Header -->
    <header class="header">
      <h1>ECHO - English & Math Exam Platform</h1>
    </header>

    <!-- Main Content Area -->
    <main class="main-content">
      <!-- Home Page -->
      <div v-if="currentPage === 'home'">
        <HomePage @start-exam="handleStartExam" />
      </div>

      <!-- Audio Test Page -->
      <div v-else-if="currentPage === 'audio-test'">
        <AudioTest
          :session-id="sessionId"
          @complete="handleAudioTestComplete"
        />
      </div>

      <!-- Read Aloud Question -->
      <div v-else-if="currentPage === 'read-aloud'">
        <ReadAloud
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Other pages will be added later -->
      <div v-else class="placeholder-page">
        <h2>{{ currentPage }} - Coming Soon</h2>
        <button @click="currentPage = 'home'" class="btn btn-secondary">Back to Home</button>
      </div>
    </main>
  </div>
</template>

<script>
import { ref } from 'vue'
import HomePage from './components/HomePage.vue'
import AudioTest from './components/AudioTest.vue'
import ReadAloud from './components/ReadAloud.vue'

export default {
  name: 'App',
  components: {
    HomePage,
    AudioTest,
    ReadAloud
  },
  setup() {
    // Navigation state
    const currentPage = ref('home')
    const sessionId = ref(null)
    const currentQuestion = ref(null)

    // Handle exam start event from HomePage component
    const handleStartExam = (examData) => {
      sessionId.value = examData.sessionId
      currentPage.value = 'audio-test' // Navigate to audio test page
      console.log('Exam started:', examData)
    }

    // Start the first question
    const startFirstQuestion = async () => {
      console.log('Starting first question for session:', sessionId.value)
      await getNextQuestion()
    }

    // Handle audio test completion
    const handleAudioTestComplete = async (testData) => {
      console.log('Audio test completed:', testData)

      // Start the first question
      await startFirstQuestion()
    }

    // Get the next question
    const getNextQuestion = async () => {
      try {
        console.log('Fetching next question for session:', sessionId.value)
        const response = await fetch(`/session/${sessionId.value}/question`)
        const data = await response.json()

        console.log('Question response:', data)

        if (data.question) {
          currentQuestion.value = data.question
          currentQuestion.value.question_index = data.question_index
          currentQuestion.value.is_last = data.is_last

          console.log('Setting up question:', data.question.type)

          // Navigate to appropriate question type
          if (data.question.type === 'read_aloud') {
            currentPage.value = 'read-aloud'
            console.log('Navigating to read-aloud page')
          } else if (data.question.type === 'multiple_choice') {
            console.log('Multiple choice question not yet implemented:', data.question.type)
            currentPage.value = 'home'
          } else if (data.question.type === 'quick_response') {
            console.log('Quick response question not yet implemented:', data.question.type)
            currentPage.value = 'home'
          } else if (data.question.type === 'translation') {
            console.log('Translation question not yet implemented:', data.question.type)
            currentPage.value = 'home'
          } else {
            console.log('Unknown question type:', data.question.type)
            currentPage.value = 'home'
          }
        } else {
          console.error('No question in response:', data)
          currentPage.value = 'home'
        }
      } catch (error) {
        console.error('Failed to get next question:', error)
        currentPage.value = 'home'
      }
    }

    // Handle question completion
    const handleQuestionComplete = async (result) => {
      console.log('Question completed:', result)

      if (result.success) {
        if (currentQuestion.value.is_last) {
          // Go to results page (not implemented yet)
          console.log('Exam completed!')
          currentPage.value = 'home'
        } else {
          // Get next question
          await getNextQuestion()
        }
      } else {
        // Handle error
        console.error('Question failed:', result.error)
        currentPage.value = 'home'
      }
    }

    return {
      currentPage,
      sessionId,
      currentQuestion,
      handleStartExam,
      handleAudioTestComplete,
      handleQuestionComplete,
      getNextQuestion
    }
  }
}
</script>

<style scoped>
/* App Layout */
.app {
  min-height: 100vh;
  background: linear-gradient(135deg, #4ade80 0%, #ffffff 100%);
  display: flex;
  flex-direction: column;
}

.header {
  background: rgba(255, 255, 255, 0.9);
  padding: 1rem;
  text-align: center;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.header h1 {
  color: #16a34a;
  margin: 0;
  font-size: 2rem;
}

.main-content {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 2rem;
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

/* Placeholder Page */
.placeholder-page {
  text-align: center;
}

.placeholder-page h2 {
  color: #16a34a;
  margin-bottom: 1rem;
}
</style>