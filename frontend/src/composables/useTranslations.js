import { ref, computed } from 'vue'
import { translations } from '../translations.js'

// Global language state
const currentLanguage = ref('en')

// Load language preference from localStorage
const loadLanguagePreference = () => {
  try {
    const saved = localStorage.getItem('echo-language')
    if (saved && (saved === 'en' || saved === 'zh')) {
      currentLanguage.value = saved
    }
  } catch (error) {
    console.error('Failed to load language preference:', error)
  }
}

// Save language preference to localStorage
const saveLanguagePreference = (language) => {
  try {
    localStorage.setItem('echo-language', language)
    currentLanguage.value = language
  } catch (error) {
    console.error('Failed to save language preference:', error)
  }
}

// Initialize language preference
loadLanguagePreference()

export function useTranslations() {
  // Computed property to get current translations
  const t = computed(() => translations[currentLanguage.value])

  // Current language getter/setter
  const language = computed({
    get: () => currentLanguage.value,
    set: (value) => {
      if (value === 'en' || value === 'zh') {
        saveLanguagePreference(value)
      }
    }
  })

  // Helper function to get nested translation keys
  const translate = (key, params = []) => {
    const keys = key.split('.')
    let value = t.value

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = value[k]
      } else {
        return key // Return key if translation not found
      }
    }

    // Handle parameter substitution
    if (typeof value === 'string' && params.length > 0) {
      params.forEach((param, index) => {
        value = value.replace(`{${index}}`, param)
      })
    }

    return value || key
  }

  // Check if Chinese is selected
  const isChinese = computed(() => currentLanguage.value === 'zh')

  // Check if English is selected
  const isEnglish = computed(() => currentLanguage.value === 'en')

  return {
    t,
    language,
    translate,
    isChinese,
    isEnglish
  }
}