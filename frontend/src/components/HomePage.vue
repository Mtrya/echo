<template>
  <div class="home-page">
    <div class="button-column">      
      <!-- Placeholder Buttons -->
      <button class="btn btn-secondary">Settings</button>
      <button class="btn btn-secondary">Files</button>
      
      <!-- Exam Selection -->
      <button @click="showExamList = true" class="btn btn-primary">
        Select Exam
      </button>
      
      <!-- Start Exam -->
      <button @click="startExam" class="btn btn-primary">
        {{ selectedExam ? `Start Exam: ${selectedExam}` : 'Start Exam' }}
      </button>
    </div>

    <!-- Exam Selection Modal -->
    <div v-if="showExamList" class="modal-overlay" @click="showExamList = false">
      <div class="modal-content" @click.stop>
        <h3>Select an Exam</h3>
        <div class="exam-list">
          <div 
            v-for="exam in availableExams" 
            :key="exam"
            class="exam-item"
            :class="{ selected: selectedExam === exam }"
            @click="selectExam(exam)"
          >
            {{ exam }}
          </div>
        </div>
        <button @click="showExamList = false" class="btn btn-secondary">Close</button>
      </div>
    </div>

    <!-- Alert Modal -->
    <div v-if="showAlert" class="modal-overlay" @click="showAlert = false">
      <div class="modal-content alert-content" @click.stop>
        <p>{{ alertMessage }}</p>
        <button @click="showAlert = false" class="btn btn-primary">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'HomePage',
  emits: ['start-exam'], // Declare that this component can emit events
  setup(_, { emit }) {
    // State management
    const showExamList = ref(false)
    const showAlert = ref(false)
    const alertMessage = ref('')
    const selectedExam = ref(null)
    const availableExams = ref([])

    // Load available exams when component mounts
    onMounted(async () => {
      await loadExams()
    })

    // API call to get exam list
    const loadExams = async () => {
      try {
        const response = await fetch('/exams/list')
        const data = await response.json()
        availableExams.value = data.exams || []
      } catch (error) {
        console.error('Failed to load exams:', error)
        showAlert.value = true
        alertMessage.value = 'Failed to load exam list'
      }
    }

    // Select an exam from the list
    const selectExam = (exam) => {
      selectedExam.value = exam
      showExamList.value = false
    }

    // Start the exam
    const startExam = async () => {
      if (!selectedExam.value) {
        showAlert.value = true
        alertMessage.value = 'Please select an exam first!'
        return
      }

      try {
        const response = await fetch('/session/start', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            exam_file_path: selectedExam.value
          })
        })
        
        const data = await response.json()
        
        if (data.session_id) {
          // Emit event to parent component with session data
          emit('start-exam', {
            sessionId: data.session_id,
            examName: selectedExam.value
          })
        } else {
          showAlert.value = true
          alertMessage.value = 'Failed to start exam session'
        }
      } catch (error) {
        console.error('Failed to start exam:', error)
        showAlert.value = true
        alertMessage.value = 'Failed to start exam session'
      }
    }

    return {
      showExamList,
      showAlert,
      alertMessage,
      selectedExam,
      availableExams,
      selectExam,
      startExam
    }
  }
}
</script>

<style scoped>
.home-page {
  width: 100%;
  max-width: 300px;
}

.button-column {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.selected-display {
  background: rgba(255, 255, 255, 0.9);
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  color: #16a34a;
  font-weight: 600;
  border: 2px solid #16a34a;
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

/* Modal Styles */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  max-width: 400px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  color: #16a34a;
  text-align: center;
}

/* Exam List Styles */
.exam-list {
  max-height: 300px;
  overflow-y: auto;
  margin: 1rem 0;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.exam-item {
  padding: 1rem;
  cursor: pointer;
  border-bottom: 1px solid #e5e7eb;
  transition: background-color 0.2s;
}

.exam-item:hover {
  background: #f3f4f6;
}

.exam-item.selected {
  background: #dcfce7;
  color: #16a34a;
  font-weight: 600;
}

.exam-item:last-child {
  border-bottom: none;
}

/* Alert Styles */
.alert-content {
  text-align: center;
}

.alert-content p {
  margin: 0 0 1rem 0;
  color: #374151;
}
</style>