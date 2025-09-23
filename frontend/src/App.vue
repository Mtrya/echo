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

      <!-- Instruction Page -->
      <div v-else-if="currentPage === 'instruction'">
        <InstructionPage
          :key="currentQuestionType + '-' + (currentInstruction?.text || '')"
          :instruction="currentInstruction"
          :audio-file="currentInstructionAudio"
          :question-type="currentQuestionType"
          @start-section="handleInstructionComplete"
        />
      </div>

      <!-- Read Aloud Question -->
      <div v-else-if="currentPage === 'read-aloud'">
        <ReadAloud
          :key="currentQuestion?.id || 'read-aloud'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Multiple Choice Question -->
      <div v-else-if="currentPage === 'multiple-choice'">
        <MultipleChoice
          :key="currentQuestion?.id || 'multiple-choice'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Quick Response Question -->
      <div v-else-if="currentPage === 'quick-response'">
        <QuickResponse
          :key="currentQuestion?.id || 'quick-response'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Translation Question -->
      <div v-else-if="currentPage === 'translation'">
        <Translation
          :key="currentQuestion?.id || 'translation'"
          :session-id="sessionId"
          :current-question="currentQuestion"
          @complete="handleQuestionComplete"
        />
      </div>

      <!-- Results Page -->
      <div v-else-if="currentPage === 'results'">
        <Results
          :session-id="sessionId"
          @new-exam="handleNewExam"
          @go-home="handleGoHome"
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
import InstructionPage from './components/InstructionPage.vue'
import ReadAloud from './components/ReadAloud.vue'
import MultipleChoice from './components/MultipleChoice.vue'
import QuickResponse from './components/QuickResponse.vue'
import Translation from './components/Translation.vue'
import Results from './components/Results.vue'

export default {
  name: 'App',
  components: {
    HomePage,
    AudioTest,
    InstructionPage,
    ReadAloud,
    MultipleChoice,
    QuickResponse,
    Translation,
    Results
  },
  setup() {
    // Navigation state
    const currentPage = ref('home')
    const sessionId = ref(null)
    const currentQuestion = ref(null)
    const currentInstruction = ref(null)
    const currentInstructionAudio = ref(null)
    const currentQuestionType = ref(null)

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
          currentQuestion.value.audio_file_path = data.audio_file_path

          console.log('Setting up question:', data.question.type, 'has instruction:', !!data.instruction)

          // Check if this is the first question in a section (has instruction)
          if (data.instruction) {
            // Show instruction page first
            currentQuestionType.value = data.question.type
            currentInstruction.value = data.instruction
            currentInstructionAudio.value = data.instruct_audio_file_path
            currentPage.value = 'instruction'
            console.log('Navigating to instruction page for section:', data.question.type)
          } else {
            // Go directly to question
            navigateToQuestion(data.question.type)
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

    // Navigate to the appropriate question page
    const navigateToQuestion = (questionType) => {
      console.log('Navigating to question type:', questionType)
      if (questionType === 'read_aloud') {
        currentPage.value = 'read-aloud'
      } else if (questionType === 'multiple_choice') {
        currentPage.value = 'multiple-choice'
      } else if (questionType === 'quick_response') {
        currentPage.value = 'quick-response'
      } else if (questionType === 'translation') {
        currentPage.value = 'translation'
      } else {
        console.log('Unknown question type:', questionType)
        currentPage.value = 'home'
      }
    }

    // Handle instruction page completion
    const handleInstructionComplete = async () => {
      console.log('Instruction completed, starting question section:', currentQuestionType.value)
      navigateToQuestion(currentQuestionType.value)
    }

    // Handle question completion
    const handleQuestionComplete = async (result) => {
      console.log('Question completed:', result)

      if (result.success) {
        if (currentQuestion.value.is_last) {
          // Go to results page
          console.log('Exam completed! Navigating to results...')
          currentPage.value = 'results'
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

    // Handle new exam request from results page
    const handleNewExam = () => {
      // Reset state for new exam
      currentPage.value = 'home'
      sessionId.value = null
      currentQuestion.value = null
    }

    // Handle go home request from results page
    const handleGoHome = () => {
      currentPage.value = 'home'
    }

    return {
      currentPage,
      sessionId,
      currentQuestion,
      currentInstruction,
      currentInstructionAudio,
      currentQuestionType,
      handleStartExam,
      handleAudioTestComplete,
      handleInstructionComplete,
      handleQuestionComplete,
      getNextQuestion,
      handleNewExam,
      handleGoHome
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