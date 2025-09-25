<template>
  <div class="settings">
    <div class="settings-header">
      <h1>Settings</h1>
      <button @click="$emit('close-settings')" class="close-btn">×</button>
    </div>

    <div class="settings-tabs">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        @click="currentTab = tab.id"
        :class="['tab-btn', { active: currentTab === tab.id }]"
      >
        {{ tab.name }}
      </button>
    </div>

    <div class="settings-content">
      <!-- API Settings -->
      <div v-if="currentTab === 'api'" class="tab-content">
        <div class="setting-group">
          <label>Dashscope API Key</label>
          <div class="api-input-group">
            <input
              v-model="settings.api.dashscope_key"
              type="password"
              placeholder="sk-..."
              :disabled="isTesting"
            />
            <button
              @click="testApiConnection"
              :disabled="!settings.api.dashscope_key || isTesting"
              class="test-btn"
            >
              {{ isTesting ? 'Testing...' : 'Test' }}
            </button>
          </div>
          <div v-if="apiTestResult" :class="['api-result', apiTestResult.success ? 'success' : 'error']">
            {{ apiTestResult.message || apiTestResult.error }}
          </div>
        </div>
      </div>

      <!-- Model Settings -->
      <div v-if="currentTab === 'models'" class="tab-content">
        <div class="setting-group">
          <label>Omni Model (for TTS, ASR, Grading)</label>
          <select v-model="settings.models.omni_model" @change="updateVoiceOptions">
            <option v-for="model in options.omni_models" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <div class="setting-group">
          <label>Vision Model (for File Conversion)</label>
          <select v-model="settings.models.vision_model">
            <option v-for="model in options.vision_models" :key="model" :value="model">
              {{ model }}
            </option>
          </select>
        </div>

        <div class="setting-group">
          <label>Instruction Voice (for exam instructions)</label>
          <select v-model="settings.models.instruction_voice">
            <option v-for="voice in availableVoices" :key="voice" :value="voice">
              {{ voice }}
            </option>
          </select>
        </div>

        <div class="setting-group">
          <label>Response Voice (for quick-response questions)</label>
          <select v-model="settings.models.response_voice">
            <option v-for="voice in availableVoices" :key="voice" :value="voice">
              {{ voice }}
            </option>
          </select>
        </div>
      </div>

      <!-- Timer Settings -->
      <div v-if="currentTab === 'timers'" class="tab-content">
        <div class="setting-group">
          <label>Multiple Choice (seconds)</label>
          <input
            v-model.number="settings.time_limits.multiple_choice"
            type="number"
            min="5"
            max="300"
          />
        </div>

        <div class="setting-group">
          <label>Read Aloud (seconds)</label>
          <input
            v-model.number="settings.time_limits.read_aloud"
            type="number"
            min="5"
            max="300"
          />
        </div>

        <div class="setting-group">
          <label>Quick Response (seconds)</label>
          <input
            v-model.number="settings.time_limits.quick_response"
            type="number"
            min="5"
            max="300"
          />
        </div>

        <div class="setting-group">
          <label>Translation (seconds)</label>
          <input
            v-model.number="settings.time_limits.translation"
            type="number"
            min="5"
            max="300"
          />
        </div>
      </div>

    </div>

    <div class="settings-actions">
      <button @click="resetToDefaults" class="reset-btn">Reset to Defaults</button>
      <button @click="saveSettings" :disabled="isSaving" class="save-btn">
        {{ isSaving ? 'Saving...' : 'Save Changes' }}
      </button>
    </div>

    <div v-if="saveResult" :class="['save-result', saveResult.success ? 'success' : 'error']">
      {{ saveResult.message }}
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, watch } from 'vue'

export default {
  name: 'Settings',
  emits: ['close-settings', 'settings-updated'],
  setup(_, { emit }) {
    const currentTab = ref('api')
    const isTesting = ref(false)
    const isSaving = ref(false)
    const apiTestResult = ref(null)
    const saveResult = ref(null)

    const tabs = [
      { id: 'api', name: 'API' },
      { id: 'models', name: 'Models' },
      { id: 'timers', name: 'Timers' }
    ]

    const settings = reactive({
      api: {
        dashscope_key: ''
      },
      models: {
        omni_model: 'qwen3-omni-flash',
        vision_model: 'qwen3-vl-plus',
        instruction_voice: 'Elias',
        response_voice: 'Cherry'
      },
      time_limits: {
        multiple_choice: 30,
        read_aloud: 15,
        quick_response: 15,
        translation: 30
      },
      })

    const originalSettings = reactive({})
    const options = reactive({
      omni_models: [],
      vision_models: [],
      voice_options: {}
    })

    const availableVoices = computed(() => {
      return options.voice_options[settings.models.omni_model] || options.voice_options['qwen3-omni-flash'] || []
    })

  
    const hasChanges = computed(() => {
      return JSON.stringify(settings) !== JSON.stringify(originalSettings)
    })

    const loadSettings = async () => {
      try {
        const response = await fetch('http://localhost:8000/settings')
        const data = await response.json()

        if (data.success) {
          // Merge with defaults
          Object.assign(settings, data.config)
          Object.assign(originalSettings, JSON.parse(JSON.stringify(data.config)))
          Object.assign(options, data.options)

          }
      } catch (error) {
        console.error('Failed to load settings:', error)
      }
    }

    const testApiConnection = async () => {
      if (!settings.api.dashscope_key) return

      isTesting.value = true
      apiTestResult.value = null

      try {
        const response = await fetch('http://localhost:8000/test-api', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ api_key: settings.api.dashscope_key })
        })

        const result = await response.json()
        apiTestResult.value = result
      } catch (error) {
        apiTestResult.value = {
          success: false,
          error: 'Connection failed'
        }
      } finally {
        isTesting.value = false
      }
    }

    const updateVoiceOptions = () => {
      // Reset voices if they're not available for the selected model
      if (!availableVoices.value.includes(settings.models.instruction_voice)) {
        settings.models.instruction_voice = availableVoices.value[0] || 'Elias'
      }
      if (!availableVoices.value.includes(settings.models.response_voice)) {
        settings.models.response_voice = availableVoices.value[0] || 'Cherry'
      }
    }

    const saveSettings = async () => {
      isSaving.value = true
      saveResult.value = null

      try {
        const response = await fetch('http://localhost:8000/settings', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ config: settings })
        })

        const result = await response.json()

        if (result.success) {
          saveResult.value = { success: true, message: 'Settings saved successfully' }
          Object.assign(originalSettings, JSON.parse(JSON.stringify(settings)))
          emit('settings-updated', settings)
          emit('close-settings')
        } else {
          saveResult.value = { success: false, message: result.errors.join(', ') }
        }
      } catch (error) {
        saveResult.value = { success: false, message: 'Failed to save settings' }
      } finally {
        isSaving.value = false
      }
    }

    const resetToDefaults = () => {
      // Preserve API key, reset other settings to defaults
      const currentApiKey = settings.api.dashscope_key
      settings.models.omni_model = 'qwen3-omni-flash'
      settings.models.vision_model = 'qwen3-vl-plus'
      settings.models.instruction_voice = 'Elias'
      settings.models.response_voice = 'Cherry'
      settings.time_limits.multiple_choice = 20
      settings.time_limits.read_aloud = 10
      settings.time_limits.quick_response = 10
      settings.time_limits.translation = 20
      // Restore API key
      settings.api.dashscope_key = currentApiKey
    }


    onMounted(() => {
      loadSettings()
    })

    return {
      currentTab,
      tabs,
      settings,
      originalSettings,
      options,
      availableVoices,
      isTesting,
      isSaving,
      apiTestResult,
      saveResult,
      hasChanges,
      testApiConnection,
      updateVoiceOptions,
      saveSettings,
      resetToDefaults
    }
  }
}
</script>

<style scoped>
.settings {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}


.settings-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.settings-header h1 {
  margin: 0;
  color: #2c3e50;
}


.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: #f0f0f0;
}

.settings.tabs {
  display: flex;
  border-bottom: 2px solid #e0e0e0;
  margin-bottom: 20px;
}

.tab-btn {
  background: none;
  border: none;
  padding: 10px 20px;
  cursor: pointer;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.3s;
}

.tab-btn.active {
  border-bottom-color: #3498db;
  color: #3498db;
}

.tab-btn:hover {
  background: #f8f9fa;
}

.setting-group {
  margin-bottom: 20px;
}

.setting-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
}

.setting-group input,
.setting-group select {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 5px;
  font-size: 14px;
}


.api-input-group {
  display: flex;
  gap: 10px;
}

.api-input-group input {
  flex: 1;
}

.test-btn {
  padding: 8px 16px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  white-space: nowrap;
}

.test-btn:hover:not(:disabled) {
  background: #2980b9;
}

.test-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.api-result {
  margin-top: 10px;
  padding: 8px 12px;
  border-radius: 5px;
  font-size: 14px;
}

.api-result.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.api-result.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.theme-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}

.theme-option {
  text-align: center;
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.theme-option:hover {
  border-color: #3498db;
}

.theme-option.active {
  border-color: #3498db;
  background: #e3f2fd;
}

.theme-preview {
  width: 100%;
  height: 60px;
  border-radius: 5px;
  margin-bottom: 8px;
}

.theme-preview.default {
  background: linear-gradient(45deg, #ffffff, #f8f9fa);
}

.theme-preview.dark {
  background: linear-gradient(45deg, #2d2d2d, #3d3d3d);
}

.theme-preview.nature {
  background: linear-gradient(45deg, #e8f5e8, #f0f8f0);
}

.theme-name {
  font-weight: 500;
  text-transform: capitalize;
}

.settings-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.reset-btn,
.save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 14px;
}

.reset-btn {
  background: #6c757d;
  color: white;
}

.reset-btn:hover {
  background: #5a6268;
}

.save-btn {
  background: #28a745;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #218838;
}

.save-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.save-result {
  margin-top: 15px;
  padding: 8px 12px;
  border-radius: 5px;
  font-size: 14px;
  text-align: center;
}

.save-result.success {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.save-result.error {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}
</style>