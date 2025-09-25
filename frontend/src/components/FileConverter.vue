<template>
  <div class="file-converter">
    <h1>File Converter</h1>
    <p>Upload files to convert them into exam questions</p>

    <!-- File Upload Area -->
    <div
      class="upload-area"
      :class="{ 'drag-over': isDragOver }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div class="upload-content">
        <div class="upload-icon">📁</div>
        <div class="upload-text">
          <p><strong>Drop files here or click to upload</strong></p>
          <p>Supported formats: .txt, .md, .docx, .pdf, .jpg, .jpeg, .png</p>
        </div>
        <input
          type="file"
          ref="fileInput"
          multiple
          @change="handleFileSelect"
          style="display: none"
          accept=".txt,.md,.docx,.pdf,.jpg,.jpeg,.png"
        >
      </div>
    </div>

    <!-- Selected Files List -->
    <div v-if="selectedFiles.length > 0" class="selected-files">
      <h3>Selected Files ({{ selectedFiles.length }})</h3>
      <div class="file-list">
        <div v-for="(file, index) in selectedFiles" :key="index" class="file-item">
          <span class="file-name">{{ file.name }}</span>
          <span class="file-size">{{ formatFileSize(file.size) }}</span>
          <button @click="removeFile(index)" class="remove-btn">×</button>
        </div>
      </div>

      <div class="upload-actions">
        <button
          @click="convertFiles"
          :disabled="isConverting || selectedFiles.length === 0"
          class="convert-btn"
        >
          {{ isConverting ? 'Converting...' : 'Convert to Exam' }}
        </button>
        <button
          @click="clearFiles"
          :disabled="isConverting"
          class="clear-btn"
        >
          Clear All
        </button>
      </div>
    </div>

    <!-- Conversion Result -->
    <div v-if="conversionResult" class="conversion-result">
      <h3>Conversion Result</h3>

      <div v-if="conversionResult.success" class="success-result">
        <div class="success-icon">✅</div>
        <p><strong>Success!</strong> {{ conversionResult.message }}</p>
        <p>Generated {{ conversionResult.extracted_questions?.length || 0 }} questions</p>

        <div v-if="conversionResult.output_filename" class="output-file">
          <p><strong>Output file:</strong> {{ conversionResult.output_filename }}</p>
        </div>

        <!-- Exam Preview -->
        <div v-if="conversionResult.extracted_questions && conversionResult.extracted_questions.length > 0" class="exam-preview">
          <h4>Exam Preview</h4>
          <div class="questions-list">
            <div v-for="(question, index) in conversionResult.extracted_questions" :key="question.id" class="question-item">
              <div class="question-header">
                <span class="question-number">{{ index + 1 }}.</span>
                <span class="question-type">{{ formatQuestionType(question.type) }}</span>
              </div>
              <div class="question-text">{{ question.text }}</div>

              <div v-if="question.options && question.options.length > 0" class="question-options">
                <div v-for="option in question.options" :key="option" class="option">
                  {{ option }}
                </div>
              </div>

              <div v-if="question.reference_answer" class="question-answer">
                <strong>Answer:</strong> {{ question.reference_answer }}
              </div>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button @click="resetConverter" class="reset-btn">Convert More Files</button>
          <button @click="goHome" class="home-btn">Go Home</button>
        </div>
      </div>

      <div v-else class="error-result">
        <div class="error-icon">❌</div>
        <p><strong>Conversion Failed</strong></p>
        <p>{{ conversionResult.message }}</p>
        <div v-if="conversionResult.raw_error" class="error-details">
          <details>
            <summary>Error Details</summary>
            <pre>{{ conversionResult.raw_error }}</pre>
          </details>
        </div>
        <button @click="resetConverter" class="retry-btn">Try Again</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'

export default {
  name: 'FileConverter',
  emits: ['start-exam', 'go-home'],
  setup(_, { emit }) {
    const fileInput = ref(null)
    const isDragOver = ref(false)
    const isConverting = ref(false)
    const selectedFiles = ref([])
    const conversionResult = ref(null)
    const generatedExamPath = ref('')

    const triggerFileInput = () => {
      fileInput.value.click()
    }

    const handleDragOver = (e) => {
      isDragOver.value = true
    }

    const handleDragLeave = (e) => {
      isDragOver.value = false
    }

    const handleDrop = (e) => {
      isDragOver.value = false
      const files = Array.from(e.dataTransfer.files)
      addFiles(files)
    }

    const handleFileSelect = (e) => {
      const files = Array.from(e.target.files)
      addFiles(files)
    }

    const addFiles = (files) => {
      // Filter for supported file types
      const supportedTypes = ['.txt', '.md', '.docx', '.pdf', '.jpg', '.jpeg', '.png']
      const validFiles = files.filter(file => {
        const extension = '.' + file.name.split('.').pop().toLowerCase()
        return supportedTypes.includes(extension)
      })

      if (validFiles.length !== files.length) {
        alert('Some files were skipped. Only .txt, .md, .docx, .pdf, .jpg, .jpeg, .png files are supported.')
      }

      selectedFiles.value = [...selectedFiles.value, ...validFiles]
    }

    const removeFile = (index) => {
      selectedFiles.value.splice(index, 1)
    }

    const clearFiles = () => {
      selectedFiles.value = []
      fileInput.value.value = ''
    }

    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes'
      const k = 1024
      const sizes = ['Bytes', 'KB', 'MB', 'GB']
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    const encodeFileToBase64 = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(',')[1]) // Remove data URL prefix
        reader.onerror = reject
        reader.readAsDataURL(file)
      })
    }

    const convertFiles = async () => {
      if (selectedFiles.value.length === 0) {
        alert('Please select at least one file')
        return
      }

      isConverting.value = true
      conversionResult.value = null

      try {
        // Encode all files to base64
        const fileContents = await Promise.all(
          selectedFiles.value.map(file => encodeFileToBase64(file))
        )

        const filenames = selectedFiles.value.map(file => file.name)

        // Send to backend
        const response = await fetch('http://localhost:8000/convert/file', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            filenames: filenames,
            file_contents: fileContents
          })
        })

        const result = await response.json()
        conversionResult.value = result

        if (result.success && result.output_filename) {
          generatedExamPath.value = result.output_filename

          // Prompt user for custom filename with better UI
          const fullPath = result.output_filename
          const fileName = fullPath.split('/').pop() // Extract just filename
          const defaultName = fileName.replace('.yaml', '')

          // Create a more visually appealing modal-like prompt
          const customName = prompt(
            `📝 Name Your Exam\n\n` +
            `Current name: ${fileName}\n\n` +
            `Enter a custom name for your exam (without .yaml extension):`,
            defaultName
          )

          if (customName && customName.trim() && customName.trim() !== defaultName) {
            try {
              const renameResponse = await fetch('http://localhost:8000/rename-exam', {
                method: 'POST',
                headers: {
                  'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                  old_name: result.output_filename, // Send full path to backend
                  new_name: customName.trim() + '.yaml'
                })
              })

              if (renameResponse.ok) {
                const renameResult = await renameResponse.json()
                if (renameResult.success) {
                  result.output_filename = renameResult.new_filename
                  generatedExamPath.value = renameResult.new_filename
                }
              }
            } catch (renameError) {
              console.warn('Failed to rename file:', renameError)
              // Don't fail the whole conversion if rename fails
            }
          }
        }

      } catch (error) {
        conversionResult.value = {
          success: false,
          message: 'Network error: ' + error.message,
          raw_error: error.stack
        }
      } finally {
        isConverting.value = false
      }
    }

    const formatQuestionType = (type) => {
      const types = {
        'multiple_choice': 'Multiple Choice',
        'read_aloud': 'Read Aloud',
        'quick_response': 'Quick Response',
        'translation': 'Translation'
      }
      return types[type] || type
    }

    const goHome = () => {
      emit('go-home')
    }

    const resetConverter = () => {
      conversionResult.value = null
      generatedExamPath.value = ''
      clearFiles()
    }

    return {
      fileInput,
      isDragOver,
      isConverting,
      selectedFiles,
      conversionResult,
      triggerFileInput,
      handleDragOver,
      handleDragLeave,
      handleDrop,
      handleFileSelect,
      removeFile,
      clearFiles,
      formatFileSize,
      convertFiles,
      formatQuestionType,
      goHome,
      resetConverter
    }
  }
}
</script>

<style scoped>
.file-converter {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
  font-family: Arial, sans-serif;
}

h1 {
  color: #2c3e50;
  text-align: center;
  margin-bottom: 10px;
}

p {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
}

.upload-area {
  border: 2px dashed #3498db;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: #f8f9fa;
}

.upload-area:hover {
  border-color: #2980b9;
  background: #e3f2fd;
}

.upload-area.drag-over {
  border-color: #27ae60;
  background: #e8f5e8;
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.upload-icon {
  font-size: 48px;
}

.upload-text p {
  margin: 5px 0;
}

.selected-files {
  margin-top: 30px;
}

.file-list {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #dee2e6;
}

.file-item:last-child {
  border-bottom: none;
}

.file-name {
  flex-grow: 1;
  font-weight: 500;
}

.file-size {
  color: #666;
  font-size: 0.9em;
  margin-right: 10px;
}

.remove-btn {
  background: #dc3545;
  color: white;
  border: none;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  cursor: pointer;
  font-size: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.remove-btn:hover {
  background: #c82333;
}

.upload-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.convert-btn, .clear-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.convert-btn {
  background: #28a745;
  color: white;
}

.convert-btn:hover:not(:disabled) {
  background: #218838;
}

.convert-btn:disabled {
  background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #45b7d1, #96ceb4, #feca57);
  background-size: 300% 300%;
  animation: gradientShift 2s ease infinite;
  cursor: not-allowed;
  color: white;
  font-weight: bold;
  text-shadow: 0 0 10px rgba(255, 255, 255, 0.8);
}

@keyframes gradientShift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.clear-btn {
  background: #6c757d;
  color: white;
}

.clear-btn:hover:not(:disabled) {
  background: #5a6268;
}

.conversion-result {
  margin-top: 30px;
  padding: 20px;
  border-radius: 8px;
}

.success-result {
  background: #d4edda;
  border: 1px solid #c3e6cb;
}

.error-result {
  background: #f8d7da;
  border: 1px solid #f5c6cb;
}

.success-icon, .error-icon {
  font-size: 24px;
  margin-bottom: 10px;
}

.output-file {
  margin: 15px 0;
  padding: 10px;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 5px;
}

.exam-preview {
  margin: 20px 0;
  background: white;
  border-radius: 8px;
  padding: 20px;
}

.questions-list {
  max-height: 400px;
  overflow-y: auto;
}

.question-item {
  border: 1px solid #dee2e6;
  border-radius: 5px;
  padding: 15px;
  margin-bottom: 15px;
}

.question-header {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  font-weight: 500;
}

.question-type {
  background: #007bff;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8em;
}

.question-time {
  background: #6c757d;
  color: white;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.8em;
}

.question-text {
  margin: 10px 0;
  line-height: 1.5;
}

.question-options {
  margin: 10px 0;
}

.option {
  padding: 5px 0;
  border-bottom: 1px solid #f0f0f0;
}

.question-answer {
  margin-top: 10px;
  padding: 10px;
  background: #e8f5e8;
  border-radius: 5px;
}

.result-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
  margin-top: 20px;
}

.reset-btn, .home-btn, .retry-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s;
}

.reset-btn {
  background: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #5a6268;
}

.home-btn {
  background: #16a34a;
  color: white;
}

.home-btn:hover {
  background: #15803d;
}

.retry-btn {
  background: #dc3545;
  color: white;
}

.retry-btn:hover {
  background: #c82333;
}

.error-details {
  margin-top: 15px;
}

.error-details pre {
  background: rgba(0, 0, 0, 0.1);
  padding: 10px;
  border-radius: 5px;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

/* Responsive design */
@media (max-width: 768px) {
  .file-converter {
    padding: 10px;
  }

  .upload-area {
    padding: 20px;
  }

  .result-actions {
    flex-direction: column;
  }

  .question-header {
    flex-wrap: wrap;
  }
}
</style>