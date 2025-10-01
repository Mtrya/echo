// Translation mappings for Echo Exam Platform
export const translations = {
  en: {
    // Header
    header: {
      title: "ECHO - English & Math Exam Platform"
    },

    // HomePage
    home: {
      settings: "Settings",
      createExam: "Create Exam",
      selectExam: "Select Exam",
      startExam: "Start Exam",
      showCompleted: "Show completed",
      close: "Close",
      selectExamTitle: "Select an Exam",
      apiRequired: "Configure API key first",
      selectExamFirst: "Select an exam first"
    },

    // Settings
    settings: {
      title: "Settings",
      tabs: {
        api: "API",
        models: "Models",
        timers: "Timers",
        language: "Language"
      },
      api: {
        dashscopeKey: "Dashscope API Key",
        testing: "Testing...",
        test: "Test",
        getKey: "Get Dashscope API Key",
        helpText: "Don't have an API key? Get one from Alibaba Cloud Dashscope"
      },
      models: {
        omniModel: "Omni Model (for TTS, ASR, Grading)",
        visionModel: "Vision Model (for File Conversion)",
        instructionVoice: "Instruction Voice (for exam instructions)",
        responseVoice: "Response Voice (for quick-response questions)"
      },
      timers: {
        multipleChoice: "Multiple Choice (seconds)",
        readAloud: "Read Aloud (seconds)",
        quickResponse: "Quick Response (seconds)",
        translation: "Translation (seconds)"
      },
      language: {
        title: "Interface Language",
        english: "English",
        chinese: "中文 (Chinese)",
        description: "Choose your preferred interface language. Language switching is disabled during exams."
      },
      actions: {
        reset: "Reset to Defaults",
        save: "Save Changes",
        saving: "Saving..."
      },
      messages: {
        saved: "Settings saved successfully",
        connectionFailed: "Connection failed"
      }
    },

    // FileConverter
    fileConverter: {
      title: "File Converter",
      description: "Upload files to convert them into exam questions",
      goHome: "Go Home",
      dragOver: "Drop files here or click to upload",
      supportedFormats: "Supported formats: .txt, .md, .docx, .pdf, .jpg, .jpeg, .png",
      selectedFiles: "Selected Files",
      convert: "Convert to Exam",
      back: "Back",
      converting: "Converting...",
      conversionSuccess: "Files converted successfully!",
      conversionFailed: "Conversion failed",
      questionsExtracted: "questions extracted",
      downloadYaml: "Download YAML",
      renameFile: "Rename File",
      deleteFile: "Delete File",
      startExam: "Start Exam",
      clearAll: "Clear All",
      nameYourExam: "Name Your Exam",
      currentName: "Current name:",
      enterCustomName: "Enter custom name (without .yaml extension):",
      enterExamName: "Enter exam name",
      discardExam: "Discard Exam",
      discardConfirm: "Are you sure you want to discard this exam?",
      cannotUndone: "This action cannot be undone.",
      conversionResult: "Conversion Result",
      outputFile: "Output file:",
      examPreview: "Exam Preview",
      answer: "Answer:",
      errorDetails: "Error Details",
      filesSkipped: "Some files were skipped. Only .txt, .md, .docx, .pdf, .jpg, .jpeg, .png files are supported.",
      failedToRename: "Failed to rename file:",
      failedToDiscard: "Failed to discard exam:"
    },

    // AudioTest
    audioTest: {
      testSpeaker: "🔊 Test Speaker",
      playTestAudio: "🔊 Play Test Audio",
      playing: "🔊 Playing...",
      practiceReading: "📖 Practice Reading",
      readingText: "Computer is an amazing machine that helps us learn, work, and connect with people around the world.",
      testMicrophone: "🎙️ Test Microphone",
      startRecording: "🎙️ Start Recording",
      stopRecording: "⏹️ Stop Recording",
      playRecording: "🔊 Play Your Recording",
      playingRecording: "🔊 Playing Recording...",
      microphoneAccess: "Please allow microphone access to use this feature",
      generatingAudio: "Generating Audio... Please Wait",
      startExam: "Start Exam"
    },

    // InstructionPage
    instruction: {
      title: "Instructions",
      listenCarefully: "Please listen carefully to the instructions",
      playAudio: "Play Audio",
      stopAudio: "Stop Audio",
      understand: "I understand, start the section",
      playing: "Playing..."
    },

    // Questions
    questions: {
      readAloud: {
        title: "Read Aloud",
        instructions: "Please read the following text aloud",
        record: "Start Recording",
        stop: "Stop Recording",
        recording: "Recording...",
        next: "Next Question",
        submit: "Submit Answer",
        getReady: "Get ready to read...",
        stopRecording: "Stop Recording and Submit Immediately"
      },
      multipleChoice: {
        title: "Multiple Choice",
        instructions: "Read the question carefully and choose the best answer",
        selectAnswer: "Select your answer",
        submit: "Submit Answer",
        next: "Next Question",
        submitAnswer: "Submit Answer Immediately",
        timeUp: "Time's up! Submitting your answer..."
      },
      quickResponse: {
        title: "Quick Response",
        instructions: "Listen carefully and respond quickly",
        record: "Start Recording",
        stop: "Stop Recording",
        recording: "Recording...",
        next: "Next Question",
        submit: "Submit Answer",
        listening: "Listen carefully...",
        getReady: "Get ready to answer...",
        speakNow: "🎤 Speak your answer now",
        stopRecording: "Stop Recording and Submit Immediately",
        timeUp: "Time's up! Submitting your answer..."
      },
      translation: {
        title: "Translation",
        instructions: "Translate the following text to English",
        record: "Start Recording",
        stop: "Stop Recording",
        recording: "Recording...",
        next: "Next Question",
        submit: "Submit Answer",
        getReady: "Get ready to translate...",
        speakNow: "🎤 Speak your English translation now",
        stopRecording: "Stop Recording and Submit Immediately",
        timeUp: "Time's up! Submitting your answer..."
      }
    },

    // Results
    results: {
      title: "Exam Results",
      examCompleted: "Exam Completed!",
      congratulations: "Congratulations on completing your exam!",
      processing: "Processing {0} of {1} questions...",
      processingAnswers: "Processing Your Answers",
      analyzingResponses: "We're analyzing your responses and generating personalized feedback. This may take a moment.",
      yourResults: "Your Results",
      finalScore: "Final Score",
      timeTaken: "Time Taken",
      score: "Score",
      correct: "Correct",
      incorrect: "Incorrect",
      completed: "Completed",
      viewDetails: "View Details",
      newExam: "New Exam",
      goHome: "Go Home",
      noResults: "No results available",
      outOf: "out of",
      aiDisclaimer: "AI-Generated Content:",
      aiDisclaimerText: "All feedback, explanations, and suggested answers are generated by artificial intelligence. While we strive for accuracy, AI systems may occasionally produce incorrect or incomplete information (AI hallucinations). Please use this feedback as a learning tool rather than definitive assessment.",
      yourAnswer: "Your Answer:",
      correctAnswer: "Correct Answer:",
      feedback: "Feedback:",
      explanation: "Explanation:",
      suggestedAnswer: "Suggested Answer:",
      playStudentAnswer: "Play Student Answer",
      playing: "Playing...",
      loadingResults: "Loading Results...",
      finalizingResults: "Finalizing your exam results...",
      startNewExam: "Start New Exam",
      backToHome: "Back to Home",
      notAnswered: "Not answered"
    },

    // Common
    common: {
      loading: "Loading...",
      error: "Error",
      success: "Success",
      warning: "Warning",
      confirm: "Confirm",
      cancel: "Cancel",
      ok: "OK",
      yes: "Yes",
      no: "No",
      retry: "Retry",
      back: "Back",
      next: "Next",
      previous: "Previous",
      finish: "Finish",
      close: "Close",
      save: "Save",
      delete: "Delete",
      edit: "Edit",
      required: "Required",
      optional: "Optional"
    }
  },

  zh: {
    // Header
    header: {
      title: "ECHO - 英文数学考试平台"
    },

    // HomePage
    home: {
      settings: "设置",
      createExam: "创建考试",
      selectExam: "选择考试",
      startExam: "开始考试",
      showCompleted: "显示已完成",
      close: "关闭",
      selectExamTitle: "选择一个考试",
      apiRequired: "请先配置API密钥",
      selectExamFirst: "请先选择一个考试"
    },

    // Settings
    settings: {
      title: "设置",
      tabs: {
        api: "API配置",
        models: "模型设置",
        timers: "计时设置",
        language: "语言设置"
      },
      api: {
        dashscopeKey: "Dashscope API密钥",
        testing: "测试中...",
        test: "测试",
        getKey: "获取Dashscope API密钥",
        helpText: "没有API密钥？请从阿里云Dashscope获取"
      },
      models: {
        omniModel: "全模态模型 (用于TTS、ASR、评分)",
        visionModel: "视觉模型 (用于文件转换)",
        instructionVoice: "指令语音 (用于考试说明)",
        responseVoice: "回答语音 (用于快速应答题)"
      },
      timers: {
        multipleChoice: "选择题 (秒)",
        readAloud: "朗读题 (秒)",
        quickResponse: "快速应答 (秒)",
        translation: "翻译题 (秒)"
      },
      language: {
        title: "界面语言",
        english: "English",
        chinese: "中文",
        description: "选择您偏好的界面语言。考试期间无法切换语言。"
      },
      actions: {
        reset: "恢复默认",
        save: "保存设置",
        saving: "保存中..."
      },
      messages: {
        saved: "设置保存成功",
        connectionFailed: "连接失败"
      }
    },

    // FileConverter
    fileConverter: {
      title: "文件转换器",
      description: "上传文件，将其转换为考试题目",
      goHome: "返回首页",
      dragOver: "拖放文件到此处或点击上传",
      supportedFormats: "支持格式: .txt, .md, .docx, .pdf, .jpg, .jpeg, .png",
      selectedFiles: "已选文件",
      convert: "转换为考试",
      back: "返回",
      converting: "转换中...",
      conversionSuccess: "文件转换成功！",
      conversionFailed: "转换失败",
      questionsExtracted: "道题目已提取",
      downloadYaml: "下载YAML文件",
      renameFile: "重命名文件",
      deleteFile: "删除文件",
      startExam: "开始考试",
      clearAll: "清除所有上传文件",
      nameYourExam: "命名您的考试",
      currentName: "当前名称：",
      enterCustomName: "输入自定义名称（不带.yaml扩展名）：",
      enterExamName: "输入考试名称",
      discardExam: "删除考试",
      discardConfirm: "您确定要删除这个考试吗？",
      cannotUndone: "此操作无法撤销。",
      conversionResult: "转换结果",
      outputFile: "输出文件：",
      examPreview: "考试预览",
      answer: "答案：",
      errorDetails: "错误详情",
      filesSkipped: "某些文件被跳过。仅支持 .txt, .md, .docx, .pdf, .jpg, .jpeg, .png 文件。",
      failedToRename: "重命名文件失败：",
      failedToDiscard: "删除考试失败："
    },

    // AudioTest
    audioTest: {
      testSpeaker: "🔊 测试扬声器",
      playTestAudio: "🔊 播放测试音频",
      playing: "🔊 播放中...",
      practiceReading: "📖 试朗读",
      readingText: "Computer is an amazing machine that helps us learn, work, and connect with people around the world.",
      testMicrophone: "🎙️ 测试麦克风",
      startRecording: "🎙️ 开始录音",
      stopRecording: "⏹️ 停止录音",
      playRecording: "🔊 播放录音",
      playingRecording: "🔊 播放录音中...",
      microphoneAccess: "请允许使用麦克风以使用此功能",
      generatingAudio: "正在生成音频...请稍候",
      startExam: "开始考试"
    },

    // InstructionPage
    instruction: {
      title: "考试说明",
      listenCarefully: "请仔细听考试说明",
      playAudio: "播放音频",
      stopAudio: "停止音频",
      understand: "我明白了，开始本部分",
      playing: "播放中..."
    },

    // Questions
    questions: {
      readAloud: {
        title: "朗读题",
        instructions: "请大声朗读以下文本",
        record: "开始录音",
        stop: "停止录音",
        recording: "录音中...",
        next: "下一题",
        submit: "提交答案",
        getReady: "准备朗读...",
        stopRecording: "停止录音并立即提交"
      },
      multipleChoice: {
        title: "选择题",
        instructions: "仔细阅读题目并选择最佳答案",
        selectAnswer: "选择您的答案",
        submit: "提交答案",
        next: "下一题",
        submitAnswer: "立即提交答案",
        timeUp: "时间到！正在提交您的答案..."
      },
      quickResponse: {
        title: "快速应答",
        instructions: "仔细听并快速应答",
        record: "开始录音",
        stop: "停止录音",
        recording: "录音中...",
        next: "下一题",
        submit: "提交答案",
        listening: "Listen carefully...",
        getReady: "准备回答...",
        speakNow: "🎤 现在说出您的答案",
        stopRecording: "停止录音并立即提交",
        timeUp: "时间到！正在提交您的答案..."
      },
      translation: {
        title: "翻译题",
        instructions: "将以下文本翻译成英文",
        record: "开始录音",
        stop: "停止录音",
        recording: "录音中...",
        next: "下一题",
        submit: "提交答案",
        getReady: "准备翻译...",
        speakNow: "🎤 现在说出您的英文翻译",
        stopRecording: "停止录音并立即提交",
        timeUp: "时间到！正在提交您的答案..."
      }
    },

    // Results
    results: {
      title: "考试结果",
      examCompleted: "考试完成！",
      congratulations: "恭喜您完成考试！",
      processing: "正在处理 {0} / {1} 道题目...",
      processingAnswers: "正在处理您的答案",
      analyzingResponses: "我们正在分析您的回答并生成个性化反馈。这可能需要一些时间。",
      yourResults: "您的结果",
      finalScore: "最终得分",
      timeTaken: "用时",
      score: "得分",
      correct: "正确",
      incorrect: "错误",
      completed: "已完成",
      viewDetails: "查看详情",
      newExam: "新考试",
      goHome: "返回首页",
      noResults: "暂无结果",
      outOf: "满分",
      aiDisclaimer: "AI生成内容：",
      aiDisclaimerText: "所有反馈、解释和建议答案均由人工智能生成。虽然我们力求准确，但AI系统有时可能会产生不正确或不完整的信息（AI幻觉）。请将此反馈用作学习工具，而非确定性评估。",
      yourAnswer: "您的答案：",
      correctAnswer: "正确答案：",
      feedback: "反馈：",
      explanation: "解释：",
      suggestedAnswer: "建议答案：",
      playStudentAnswer: "播放学生答案",
      playing: "播放中...",
      loadingResults: "加载结果中...",
      finalizingResults: "正在完成您的考试结果...",
      startNewExam: "开始新考试",
      backToHome: "返回首页",
      notAnswered: "未作答"
    },

    // Common
    common: {
      loading: "加载中...",
      error: "错误",
      success: "成功",
      warning: "警告",
      confirm: "确认",
      cancel: "取消",
      ok: "确定",
      yes: "是",
      no: "否",
      retry: "重试",
      back: "返回",
      next: "下一步",
      previous: "上一步",
      finish: "完成",
      close: "关闭",
      save: "保存",
      delete: "删除",
      edit: "编辑",
      required: "必填",
      optional: "选填"
    }
  }
}