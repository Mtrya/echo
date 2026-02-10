declare module 'lamejsfix' {
  export class Mp3Encoder {
    constructor(channels: number, sampleRate: number, bitRate: number)
    encodeBuffer(samples: Int16Array): Int8Array
    flush(): Int8Array
  }
}
