/**
 * MP3 Recorder Utility
 * Records audio from microphone and encodes to MP3 format using lamejs
 */

import { Mp3Encoder } from 'lamejsfix'

// Extend Window interface for webkitAudioContext
declare global {
  interface Window {
    webkitAudioContext?: typeof AudioContext
  }
}

export class Mp3Recorder {
  private mediaStream: MediaStream | null = null
  private audioContext: AudioContext | null = null
  private processor: ScriptProcessorNode | null = null
  private mp3Encoder: Mp3Encoder | null = null
  private mp3Data: BlobPart[] = []
  private isRecording = false
  private readonly sampleRate = 44100
  private readonly bitRate = 128

  /**
   * Initialize the MP3 recorder and request microphone access
   */
  async start(): Promise<void> {
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
      this.mp3Encoder = new Mp3Encoder(1, this.sampleRate, this.bitRate)
      this.mp3Data = []

      // Process audio chunks
      this.processor.onaudioprocess = (event: AudioProcessingEvent) => {
        const inputBuffer = event.inputBuffer
        const samples = this.floatToInt16(inputBuffer.getChannelData(0))

        // Encode audio chunk to MP3
        const mp3buf = this.mp3Encoder!.encodeBuffer(samples)
        if (mp3buf.length > 0) {
          // Cast Int8Array to BlobPart
          this.mp3Data.push(mp3buf as unknown as BlobPart)
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
   */
  async stop(): Promise<Blob> {
    if (!this.isRecording) {
      throw new Error('No recording in progress')
    }

    try {
      // Finalize MP3 encoding
      const mp3buf = this.mp3Encoder!.flush()
      if (mp3buf.length > 0) {
        // Cast Int8Array to BlobPart
        this.mp3Data.push(mp3buf as unknown as BlobPart)
      }

      // Create MP3 blob from encoded data
      const mp3Blob = new Blob(this.mp3Data, { type: 'audio/mp3' })

      // Cleanup resources
      this.cleanup()

      console.log('MP3 recording stopped, blob size:', mp3Blob.size, 'bytes')
      return mp3Blob

    } catch (error) {
      console.error('Failed to stop MP3 recording:', error)
      this.cleanup()
      throw error
    }
  }

  /**
   * Clean up audio resources
   */
  cleanup(): void {
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
   */
  private floatToInt16(floatArray: Float32Array): Int16Array {
    const int16Array = new Int16Array(floatArray.length)
    for (let i = 0; i < floatArray.length; i++) {
      // Convert float (-1 to 1) to 16-bit integer (-32768 to 32767)
      const sample = floatArray[i] ?? 0
      let s = Math.max(-1, Math.min(1, sample))
      s = s < 0 ? s * 32768 : s * 32767
      int16Array[i] = s
    }
    return int16Array
  }

  /**
   * Check if browser supports required features
   */
  static isSupported(): boolean {
    if (!navigator.mediaDevices?.getUserMedia) {
      return false
    }
    // Check for AudioContext support (using bracket notation to avoid TS always-true error)
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = window as any
    return !!(win.AudioContext || win.webkitAudioContext)
  }
}

/**
 * Convert blob to base64 string
 */
export function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onloadend = () => {
      // Extract base64 data from the result (remove data URL prefix)
      const result = reader.result as string | null
      if (result === null) {
        reject(new Error('Failed to read blob as data URL'))
        return
      }
      const base64 = result.split(',')[1]
      if (base64 === undefined) {
        reject(new Error('Failed to extract base64 data'))
        return
      }
      resolve(base64)
    }
    reader.onerror = reject
    reader.readAsDataURL(blob)
  })
}

export default Mp3Recorder
