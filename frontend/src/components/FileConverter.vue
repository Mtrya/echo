<template>
  <div class="file-converter">
    <!-- Header with Go Home button -->
    <div class="header-section">
      <div>
        <h1>{{ translate('fileConverter.title') }}</h1>
        <p>{{ translate('fileConverter.description') }}</p>
      </div>
      <button @click="goHome" class="go-home-btn">🏠 {{ translate('fileConverter.goHome') }}</button>
    </div>

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
          <p><strong>{{ translate('fileConverter.dragOver') }}</strong></p>
          <p>{{ translate('fileConverter.supportedFormats') }}</p>
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
      <h3>{{ translate('fileConverter.selectedFiles') }} ({{ selectedFiles.length }})</h3>
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
          {{ isConverting ? translate('fileConverter.converting') : translate('fileConverter.convert') }}
        </button>
        <button
          @click="clearFiles"
          :disabled="isConverting"
          class="clear-btn"
        >
          {{ translate('fileConverter.clearAll') }}
        </button>
      </div>
    </div>

    <!-- Conversion Result -->
    <!-- Rename Modal -->
    <div v-if="showRenameModal" class="modal-overlay" @click="cancelRename">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📝 {{ translate('fileConverter.nameYourExam') }}</h3>
          <button @click="cancelRename" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <p><strong>{{ translate('fileConverter.currentName') }}</strong> {{ currentFileName }}</p>
          <div class="input-group">
            <label for="exam-name">{{ translate('fileConverter.enterCustomName') }}</label>
            <input
              id="exam-name"
              v-model="customExamName"
              type="text"
              :placeholder="translate('fileConverter.enterExamName')"
              class="text-input"
              @keyup.enter="confirmRename"
            >
          </div>
        </div>
        <div class="modal-actions">
          <button @click="cancelRename" class="btn btn-secondary">{{ translate('common.cancel') }}</button>
          <button @click="confirmRename" class="btn btn-primary">{{ translate('common.save') }}</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click="cancelDelete">
      <div class="modal-content delete-modal" @click.stop>
        <div class="modal-header">
          <h3>🗑️ {{ translate('fileConverter.discardExam') }}</h3>
          <button @click="cancelDelete" class="close-btn">×</button>
        </div>
        <div class="modal-body">
          <div class="warning-icon">⚠️</div>
          <p>{{ translate('fileConverter.discardConfirm') }}</p>
          <p class="file-name"><strong>{{ examToDelete }}</strong></p>
          <p class="warning-text">{{ translate('fileConverter.cannotUndone') }}</p>
        </div>
        <div class="modal-actions">
          <button @click="cancelDelete" class="btn btn-secondary">{{ translate('common.cancel') }}</button>
          <button @click="confirmDelete" class="btn btn-danger">{{ translate('fileConverter.deleteFile') }}</button>
        </div>
      </div>
    </div>

    <!-- Conversion Result -->
    <div v-if="conversionResult" class="conversion-result">
      <h3>{{ translate('fileConverter.conversionResult') }}</h3>

      <div v-if="conversionResult.success" class="success-result">
        <div class="success-icon">✅</div>
        <p><strong>{{ translate('common.success') }}!</strong> {{ translate('fileConverter.examCreatedSuccessfully') }}</p>
        <p>{{ conversionResult.extracted_questions?.length || 0 }} {{ translate('fileConverter.questionsExtracted') }}</p>

        <!-- File Converter Message Box -->
        <div v-if="conversionResult.message" class="converter-message">
          <h4>{{ translate('fileConverter.converterMessage') }}</h4>
          <p>{{ conversionResult.message }}</p>
        </div>

        <div v-if="conversionResult.output_filename" class="output-file">
          <p><strong>{{ translate('fileConverter.outputFile') }}</strong> {{ conversionResult.output_filename }}</p>
        </div>

        <!-- Exam Preview -->
        <div v-if="conversionResult.extracted_questions && conversionResult.extracted_questions.length > 0" class="exam-preview">
          <h4>{{ translate('fileConverter.examPreview') }}</h4>
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
                <strong>{{ translate('fileConverter.answer') }}</strong> {{ question.reference_answer }}
              </div>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button @click="resetConverter" class="reset-btn">{{ translate('fileConverter.back') }}</button>
          <button @click="discardExam" class="discard-btn">🗑️ {{ translate('fileConverter.discardExam') }}</button>
        </div>
      </div>

      <div v-else class="error-result">
        <div class="error-icon">❌</div>
        <p><strong>{{ translate('fileConverter.conversionFailed') }}</strong></p>

        <!-- File Converter Message Box for Errors -->
        <div v-if="conversionResult.message" class="converter-message error">
          <h4>{{ translate('fileConverter.converterMessage') }}</h4>
          <p>{{ conversionResult.message }}</p>
        </div>
        <div v-if="conversionResult.raw_error" class="error-details">
          <details>
            <summary>{{ translate('fileConverter.errorDetails') }}</summary>
            <pre>{{ conversionResult.raw_error }}</pre>
          </details>
        </div>
        <button @click="resetConverter" class="retry-btn">{{ translate('common.retry') }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useTranslations } from '../composables/useTranslations.js'
import { apiUrl } from '../utils/api.js'

export default {
  name: 'FileConverter',
  emits: ['start-exam', 'go-home'],
  setup(_, { emit }) {
    const { translate } = useTranslations()
    const fileInput = ref(null)
    const isDragOver = ref(false)
    const isConverting = ref(false)
    const selectedFiles = ref([])
    const conversionResult = ref(null)
    const generatedExamPath = ref('')

    // Modal state
    const showRenameModal = ref(false)
    const showDeleteModal = ref(false)
    const currentFileName = ref('')
    const customExamName = ref('')
    const examToDelete = ref('')

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
        console.log(translate('fileConverter.filesSkipped'))
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
        const response = await fetch(apiUrl('/convert/file'), {
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

          // Show rename modal instead of browser prompt
          const fullPath = result.output_filename
          const fileName = fullPath.split('/').pop() // Extract just filename
          const defaultName = fileName.replace('.yaml', '')

          currentFileName.value = fileName
          customExamName.value = defaultName
          showRenameModal.value = true
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

    const discardExam = async () => {
      if (!generatedExamPath.value) {
        return
      }

      // Show delete confirmation modal instead of browser confirm
      const examFilename = generatedExamPath.value.split('/').pop()
      examToDelete.value = examFilename
      showDeleteModal.value = true
    }

    // Modal methods
    const cancelRename = () => {
      showRenameModal.value = false
      currentFileName.value = ''
      customExamName.value = ''
    }

    const confirmRename = async () => {
      if (!customExamName.value.trim()) {
        return
      }

      const oldName = conversionResult.value.output_filename
      const newName = customExamName.value.trim() + '.yaml'

      if (oldName.split('/').pop() === newName) {
        // No change needed
        cancelRename()
        return
      }

      try {
        const renameResponse = await fetch(apiUrl('/rename-exam'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            old_name: oldName,
            new_name: newName
          })
        })

        if (renameResponse.ok) {
          const renameResult = await renameResponse.json()
          if (renameResult.success) {
            conversionResult.value.output_filename = renameResult.new_filename
            generatedExamPath.value = renameResult.new_filename
          }
        }
      } catch (renameError) {
        console.warn(translate('fileConverter.failedToRename'), renameError)
      } finally {
        cancelRename()
      }
    }

    const cancelDelete = () => {
      showDeleteModal.value = false
      examToDelete.value = ''
    }

    const confirmDelete = async () => {
      const examFilename = examToDelete.value

      try {
        const response = await fetch(apiUrl('/delete-exam'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            exam_filename: examFilename
          })
        })

        const result = await response.json()

        if (result.success) {
          resetConverter()
        } else {
          // Show error in a more elegant way - could add a toast notification here
          console.error(translate('fileConverter.failedToDiscard'), result.message)
        }
      } catch (error) {
        console.error('Error discarding exam:', error)
        // Network errors logged to console instead of showing alert
      } finally {
        cancelDelete()
      }
    }

    return {
      fileInput,
      isDragOver,
      isConverting,
      selectedFiles,
      conversionResult,
      showRenameModal,
      showDeleteModal,
      currentFileName,
      customExamName,
      examToDelete,
      translate,
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
      resetConverter,
      discardExam,
      cancelRename,
      confirmRename,
      cancelDelete,
      confirmDelete
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

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 30px;
}

.header-section > div {
  flex: 1;
}

h1 {
  color: #2c3e50;
  text-align: left;
  margin-bottom: 10px;
}

p {
  text-align: left;
  color: #666;
  margin-bottom: 0;
}

.go-home-btn {
  background: #16a34a;
  color: white;
  border: none;
  border-radius: 8px;
  padding: 12px 20px;
  cursor: pointer;
  font-size: 16px;
  font-weight: 600;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.go-home-btn:hover {
  background: #15803d;
  transform: translateY(-2px);
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

.converter-message {
  margin: 15px 0;
  padding: 15px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #cce5ff;
  border-radius: 8px;
}

.converter-message h4 {
  margin: 0 0 10px 0;
  color: #004085;
  font-size: 16px;
  font-weight: 600;
}

.converter-message p {
  margin: 0;
  color: #0056b3;
  font-style: italic;
}

.converter-message.error {
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid #f8d7da;
}

.converter-message.error h4 {
  color: #721c24;
}

.converter-message.error p {
  color: #721c24;
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

.reset-btn, .home-btn, .retry-btn, .discard-btn {
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

.discard-btn {
  background: #dc3545;
  color: white;
}

.discard-btn:hover {
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
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 12px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  animation: modalSlideIn 0.3s ease-out;
}

.delete-modal {
  border-top: 4px solid #dc3545;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.modal-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  color: #6b7280;
  cursor: pointer;
  padding: 0.25rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #e5e7eb;
  color: #374151;
}

.modal-body {
  padding: 1.5rem;
}

.modal-body p {
  margin: 0 0 1rem 0;
  color: #374151;
}

.input-group {
  margin-bottom: 1rem;
}

.input-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #374151;
  font-weight: 500;
}

.text-input {
  width: 100%;
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.text-input:focus {
  outline: none;
  border-color: #16a34a;
  box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.1);
}

.warning-icon {
  font-size: 3rem;
  text-align: center;
  margin-bottom: 1rem;
  color: #dc3545;
}

.file-name {
  background: #f3f4f6;
  padding: 0.75rem;
  border-radius: 0.5rem;
  text-align: center;
  font-family: 'Courier New', monospace;
  word-break: break-all;
}

.warning-text {
  color: #dc3545;
  font-weight: 500;
  text-align: center;
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  justify-content: flex-end;
  padding: 1.5rem;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
}

.modal-actions .btn {
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 600;
  min-width: 120px;
}

.modal-actions .btn-primary {
  background: #16a34a;
  color: white;
}

.modal-actions .btn-primary:hover {
  background: #15803d;
  transform: translateY(-2px);
}

.modal-actions .btn-secondary {
  background: rgba(255, 255, 255, 0.8);
  color: #16a34a;
  border: 2px solid #16a34a;
}

.modal-actions .btn-secondary:hover {
  background: white;
  transform: translateY(-2px);
}

.modal-actions .btn-danger {
  background: #dc2626;
  color: white;
}

.modal-actions .btn-danger:hover {
  background: #b91c1c;
  transform: translateY(-2px);
}

.modal-actions .btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-20px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
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

  .modal-content {
    width: 95%;
    margin: 1rem;
  }

  .modal-actions {
    flex-direction: column-reverse;
  }

  .modal-actions .btn {
    width: 100%;
  }
}
</style>