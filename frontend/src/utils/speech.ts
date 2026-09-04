let currentUtterance: SpeechSynthesisUtterance | null = null

export function speakText(text: string, rate: number = 0.9): void {
  if (!('speechSynthesis' in window)) return

  stopSpeaking()

  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'zh-CN'
  utterance.rate = rate
  utterance.pitch = 1
  utterance.volume = 1

  const voices = speechSynthesis.getVoices()
  const zhVoice = voices.find(v => v.lang.startsWith('zh'))
  if (zhVoice) utterance.voice = zhVoice

  currentUtterance = utterance
  speechSynthesis.speak(utterance)
}

export function stopSpeaking(): void {
  speechSynthesis.cancel()
  currentUtterance = null
}
