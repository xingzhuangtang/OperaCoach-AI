import api from '@/api/index'

let currentAudio: HTMLAudioElement | null = null

export async function synthesizeSpeech(text: string, voice: string = 'longxiaochun'): Promise<string> {
  const { data } = await api.post<{ audio_url: string; cached: boolean }>('/tts/synthesize', {
    text,
    voice,
  })
  return data.audio_url
}

export function playAudio(url: string): Promise<void> {
  stopAudio()
  return new Promise((resolve, reject) => {
    currentAudio = new Audio(url)
    currentAudio.onended = () => {
      currentAudio = null
      resolve()
    }
    currentAudio.onerror = () => {
      currentAudio = null
      reject(new Error('音频播放失败'))
    }
    currentAudio.play().catch(reject)
  })
}

export function stopAudio(): void {
  if (currentAudio) {
    currentAudio.pause()
    currentAudio.currentTime = 0
    currentAudio = null
  }
}

export function getAudioUrl(path: string): string {
  return path.startsWith('http') ? path : path
}
