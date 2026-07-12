/**
 * 简谱旋律播放工具
 * 使用 Web Audio API 生成电子哼唱
 */

// C 大调音阶频率（第 4 八度）
const NOTE_FREQUENCIES: Record<string, number> = {
  '1': 261.63,
  '2': 293.66,
  '3': 329.63,
  '4': 349.23,
  '5': 392.00,
  '6': 440.00,
  '7': 493.88,
}

// 高音（第 5 八度）
const HIGH_NOTE_FREQUENCIES: Record<string, number> = {
  '1': 523.25,
  '2': 587.33,
  '3': 659.25,
  '4': 698.46,
  '5': 783.99,
  '6': 880.00,
  '7': 987.77,
}

let audioContext: AudioContext | null = null
let isPlaying = false
let stopFlag = false
let onNoteCallback: ((index: number) => void) | null = null
let noteTimers: number[] = []

function getAudioContext(): AudioContext {
  if (!audioContext) {
    audioContext = new AudioContext()
  }
  return audioContext
}

export function getIsPlaying(): boolean {
  return isPlaying
}

export function setOnNoteCallback(cb: ((index: number) => void) | null): void {
  onNoteCallback = cb
}

export function stopMelody(): void {
  stopFlag = true
  noteTimers.forEach(t => clearTimeout(t))
  noteTimers = []
  isPlaying = false
  if (audioContext && audioContext.state === 'running') {
    audioContext.suspend()
  }
}

export async function playMelody(notation: string, totalDuration: number): Promise<void> {
  if (!notation || totalDuration <= 0) return

  stopFlag = false
  noteTimers.forEach(t => clearTimeout(t))
  noteTimers = []

  const ctx = getAudioContext()
  if (ctx.state === 'suspended') {
    await ctx.resume()
  }

  const notes = notation.split(' ').filter(n => n.trim())
  if (notes.length === 0) return

  const noteDuration = totalDuration / notes.length
  isPlaying = true

  for (let i = 0; i < notes.length; i++) {
    if (stopFlag) break

    const note = notes[i]
    const isHigh = note.includes("'")
    const digit = note.replace("'", "").replace(".", "")
    const isDotted = note.includes(".")

    const freq = isHigh
      ? HIGH_NOTE_FREQUENCIES[digit] || 440
      : NOTE_FREQUENCIES[digit] || 440

    const duration = isDotted ? noteDuration * 1.5 : noteDuration
    const delay = i * noteDuration * 1000

    const timer = window.setTimeout(() => {
      if (stopFlag) return

      onNoteCallback?.(i)

      const oscillator = ctx.createOscillator()
      oscillator.type = 'triangle'
      oscillator.frequency.setValueAtTime(freq, ctx.currentTime)

      const gain = ctx.createGain()
      const attack = 0.02
      const release = 0.05
      const sustain = 0.3

      gain.gain.setValueAtTime(0, ctx.currentTime)
      gain.gain.linearRampToValueAtTime(sustain, ctx.currentTime + attack)
      gain.gain.setValueAtTime(sustain, ctx.currentTime + duration - release)
      gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duration)

      oscillator.connect(gain)
      gain.connect(ctx.destination)

      oscillator.start(ctx.currentTime)
      oscillator.stop(ctx.currentTime + duration)
    }, delay)

    noteTimers.push(timer)
  }

  const totalWithDots = notes.reduce((sum, n) => sum + (n.includes('.') ? 1.5 : 1), 0)
  const waitTime = (totalWithDots / notes.length) * totalDuration * 1000

  await new Promise<void>(resolve => {
    const timer = window.setTimeout(() => {
      isPlaying = false
      resolve()
    }, waitTime)
    noteTimers.push(timer)
  })
}
