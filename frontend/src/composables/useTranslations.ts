import { ref, computed, type Ref, type ComputedRef } from 'vue'
import { translations, type Language } from '@/translations'

// Global language state
const currentLanguage = ref<Language>('en')

// Load language preference from localStorage
const loadLanguagePreference = (): void => {
  try {
    const saved = localStorage.getItem('echo-language')
    if (saved && (saved === 'en' || saved === 'zh')) {
      currentLanguage.value = saved as Language
    }
  } catch (error) {
    console.error('Failed to load language preference:', error)
  }
}

// Save language preference to localStorage
const saveLanguagePreference = (language: Language): void => {
  try {
    localStorage.setItem('echo-language', language)
    currentLanguage.value = language
  } catch (error) {
    console.error('Failed to save language preference:', error)
  }
}

// Initialize language preference
loadLanguagePreference()

// eslint-disable-next-line @typescript-eslint/no-empty-object-type
export interface TranslationKeys extends Record<string, unknown> {}

export interface UseTranslationsReturn {
  t: ComputedRef<TranslationKeys>
  language: Ref<Language>
  translate: (key: string, params?: (string | number)[]) => string
  isChinese: ComputedRef<boolean>
  isEnglish: ComputedRef<boolean>
}

export function useTranslations(): UseTranslationsReturn {
  // Computed property to get current translations
  const t = computed(() => translations[currentLanguage.value])

  // Current language getter/setter
  const language = computed<Language>({
    get: () => currentLanguage.value,
    set: (value: Language) => {
      if (value === 'en' || value === 'zh') {
        saveLanguagePreference(value)
      }
    }
  })

  // Helper function to get nested translation keys
  const translate = (key: string, params: (string | number)[] = []): string => {
    const keys = key.split('.')
    let value: unknown = t.value

    for (const k of keys) {
      if (value && typeof value === 'object' && k in value) {
        value = (value as Record<string, unknown>)[k]
      } else {
        return key // Return key if translation not found
      }
    }

    // Handle parameter substitution
    if (typeof value === 'string' && params.length > 0) {
      let result = value
      params.forEach((param, index) => {
        result = result.replace(`{${index}}`, String(param))
      })
      return result
    }

    return typeof value === 'string' ? value : key
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
