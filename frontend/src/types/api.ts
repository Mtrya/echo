export type QuestionType = 'multiple_choice' | 'read_aloud' | 'quick_response' | 'translation'

export interface Question {
  id: string
  type: QuestionType
  text: string
  options?: string[]
  reference_answer?: string
  audio_file_path?: string
  time_limit?: number
  question_index?: number
  is_last?: boolean
}

export interface Instruction {
  text: string
  tts: string
}

export interface GetQuestionResponse {
  question: Question
  time_limit: number
  audio_file_path: string
  question_index: number
  is_last: boolean
  instruction?: Instruction
  instruct_audio_file_path?: string
}

export interface StartSessionResponse {
  session_id: string
  exam_title: string
  total_questions: number
  message: string
}

export interface SubmitAnswerRequest {
  answer_text?: string
  audio_data?: string
}

export interface SubmitAnswerResponse {
  message: string
  question_index: number
  processing: boolean
}

export interface AudioStatusResponse {
  audio_generation: string
  session_id: string
}

export interface QuestionResult {
  question_index: number
  question_id: string
  question_type: string
  question_text: string
  score: number
  feedback: string
  explanation?: string
  suggested_answer?: string
  student_answer?: string
  reference_answer?: string
  student_audio_path?: string
}

export interface ExamResultsResponse {
  session_id: string
  exam_title: string
  total_score: number
  max_score: number
  percentage: number
  total_questions: number
  processed_count: number
  all_processed: boolean
  duration_seconds: number
  start_time: string
  end_time: string
  question_results: QuestionResult[]
}

export interface ConvertFileRequest {
  filenames: string[]
  file_contents: string[]
}

export interface ConvertFileResponse {
  success: boolean
  message: string
  extracted_questions?: Question[]
  yaml_output?: string
  output_filename?: string
  raw_error?: string
}

export interface RenameExamRequest {
  old_name: string
  new_name: string
}

export interface RenameExamResponse {
  success: boolean
  message: string
  new_filename?: string
}

export interface DeleteExamRequest {
  exam_filename: string
}

export interface DeleteExamResponse {
  success: boolean
  message: string
}

export interface ApiConfig {
  dashscope_key: string
}

export interface ModelConfig {
  omni_model: string
  vision_model: string
  instruction_voice: string
  response_voice: string
}

export interface TimeLimitsConfig {
  multiple_choice: number
  read_aloud: number
  quick_response: number
  translation: number
}

export interface UiConfig {
  language: string
}

export interface AppConfig {
  api: ApiConfig
  models: ModelConfig
  time_limits: TimeLimitsConfig
  ui: UiConfig
}

export interface SettingsOptions {
  omni_models: string[]
  vision_models: string[]
  voice_options: Record<string, string[]>
}

export interface SettingsResponse {
  success: boolean
  config: AppConfig
  options: SettingsOptions
}

export interface SettingsUpdateRequest {
  config: Partial<AppConfig>
}

export interface SettingsUpdateResponse {
  success: boolean
  message: string
}

export interface TestApiRequest {
  api_key: string
}

export interface TestApiResponse {
  success: boolean
  message: string
  model_info?: {
    model: string
    capabilities: string[]
  }
}

export interface VoicesResponse {
  success: boolean
  voices: string[]
}

export interface ApiKeyStatusResponse {
  has_api_key: boolean
  message: string
}

export interface ExamsListResponse {
  exams: string[]
}

export interface CompletedExamsResponse {
  completed_exams: string[]
}

export interface ApiInfoResponse {
  message: string
  version: string
  docs: string
  endpoints: {
    exams: string
    session: string
    health: string
  }
}

export interface HealthResponse {
  status: string
}
