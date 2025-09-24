/**
 * MP3 Recorder Utility
 * Records audio from microphone and encodes to MP3 format using lamejs
 */

import lamejs from 'lamejsfix'

class Mp3Recorder {
  constructor() {
    this.mediaStream = null
    this.audioContext = null
    this.processor = null
    this.mp3Encoder = null
    this.mp3Data = []
    this.isRecording = false
    this.sampleRate = 44100
    this.bitRate = 128
  }

  /**
   * Initialize the MP3 recorder and request microphone access
   */
  async start() {
    if (this.isRecording) {
      throw new Error('Recording is already in progress')
    }

    try {
      // Get microphone access
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        }
      })

      // Create Web Audio context
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)()
      const source = this.audioContext.createMediaStreamSource(this.mediaStream)

      // Create audio processor for real-time encoding
      this.processor = this.audioContext.createScriptProcessor(4096, 1, 1)

      // Initialize MP3 encoder
      this.mp3Encoder = new lamejs.Mp3Encoder(1, this.sampleRate, this.bitRate)
      this.mp3Data = []

      // Process audio chunks
      this.processor.onaudioprocess = (event) => {
        const inputBuffer = event.inputBuffer
        const samples = this._floatToInt16(inputBuffer.getChannelData(0))

        // Encode audio chunk to MP3
        const mp3buf = this.mp3Encoder.encodeBuffer(samples)
        if (mp3buf.length > 0) {
          this.mp3Data.push(mp3buf)
        }
      }

      // Connect the audio graph
      source.connect(this.processor)
      this.processor.connect(this.audioContext.destination)

      this.isRecording = true
      console.log('MP3 recording started')

    } catch (error) {
      console.error('Failed to start MP3 recording:', error)
      throw error
    }
  }

  /**
   * Stop recording and return MP3 blob
   * @returns {Promise<Blob>} MP3 audio blob
   */
  async stop() {
    if (!this.isRecording) {
      throw new Error('No recording in progress')
    }

    try {
      // Finalize MP3 encoding
      const mp3buf = this.mp3Encoder.flush()
      if (mp3buf.length > 0) {
        this.mp3Data.push(mp3buf)
      }

      // Create MP3 blob from encoded data
      const mp3Blob = new Blob(this.mp3Data, { type: 'audio/mp3' })

      // Cleanup resources
      this._cleanup()

      console.log('MP3 recording stopped, blob size:', mp3Blob.size, 'bytes')
      return mp3Blob

    } catch (error) {
      console.error('Failed to stop MP3 recording:', error)
      this._cleanup()
      throw error
    }
  }

  /**
   * Clean up audio resources
   */
  _cleanup() {
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop())
      this.mediaStream = null
    }

    if (this.processor) {
      this.processor.disconnect()
      this.processor = null
    }

    if (this.audioContext) {
      this.audioContext.close()
      this.audioContext = null
    }

    this.mp3Encoder = null
    this.mp3Data = []
    this.isRecording = false
  }

  /**
   * Convert Float32Array to Int16Array for MP3 encoding
   * @param {Float32Array} floatArray
   * @returns {Int16Array}
   */
  _floatToInt16(floatArray) {
    const int16Array = new Int16Array(floatArray.length)
    for (let i = 0; i < floatArray.length; i++) {
      // Convert float (-1 to 1) to 16-bit integer (-32768 to 32767)
      let s = Math.max(-1, Math.min(1, floatArray[i]))
      s = s < 0 ? s * 32768 : s * 32767
      int16Array[i] = s
    }
    return int16Array
  }

  /**
   * Check if browser supports required features
   * @returns {boolean}
   */
  static isSupported() {
    return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia &&
             (window.AudioContext || window.webkitAudioContext))
  }
}

/**
 * Convert blob to base64 string
 * @param {Blob} blob
 * @returns {Promise<string>}
 */
function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      // Extract base64 data from the result (remove data URL prefix)
      const base64 = reader.result.split(',')[1]
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export { Mp3Recorder, blobToBase64 }
export default Mp3Recorder