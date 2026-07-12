<script setup lang="ts">
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import type { MusicGeneration } from '@/api/music'

const props = defineProps<{
  track: MusicGeneration | null
}>()

const emit = defineEmits<{
  (e: 'remix', track: MusicGeneration): void
}>()

const audioRef = ref<HTMLAudioElement | null>(null)
const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const showLyrics = ref(false)
const playbackRate = ref(1.0)
const speedOptions = [0.5, 0.7, 0.9, 1.0]

const cycleSpeed = () => {
  const currentIndex = speedOptions.indexOf(playbackRate.value)
  const nextIndex = (currentIndex + 1) % speedOptions.length
  playbackRate.value = speedOptions[nextIndex]
  if (audioRef.value) {
    audioRef.value.playbackRate = playbackRate.value
  }
}

const downloadTrack = () => {
  if (!props.track?.audio_url) return
  const a = document.createElement('a')
  a.href = props.track.audio_url
  a.download = `${props.track.title || '未命名'}.mp3`
  a.target = '_blank'
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
}

const formatTime = (s: number) => {
  if (!s || isNaN(s)) return '00:00'
  const m = Math.floor(s / 60)
  const sec = Math.floor(s % 60)
  return `${m.toString().padStart(2, '0')}:${sec.toString().padStart(2, '0')}`
}

const progress = computed(() => {
  if (!duration.value) return 0
  return (currentTime.value / duration.value) * 100
})

const togglePlay = () => {
  if (!audioRef.value || !props.track) return
  if (isPlaying.value) {
    audioRef.value.pause()
  } else {
    audioRef.value.play()
  }
}

const seek = (e: MouseEvent) => {
  if (!audioRef.value || !duration.value) return
  const target = e.currentTarget as HTMLElement
  const rect = target.getBoundingClientRect()
  const ratio = (e.clientX - rect.left) / rect.width
  audioRef.value.currentTime = ratio * duration.value
}

watch(() => props.track?.audio_url, (url) => {
  if (url && audioRef.value) {
    audioRef.value.load()
    audioRef.value.playbackRate = 1.0
    playbackRate.value = 1.0
    isPlaying.value = false
    currentTime.value = 0
  }
})

const onTimeUpdate = () => {
  if (audioRef.value) {
    currentTime.value = audioRef.value.currentTime
  }
}

const onLoadedMetadata = () => {
  if (audioRef.value) {
    duration.value = audioRef.value.duration
  }
}

const onEnded = () => {
  isPlaying.value = false
  currentTime.value = 0
}

const trackTitle = computed(() => props.track?.title || '未命名曲目')
const trackLyrics = computed(() => props.track?.lyrics || '暂无歌词')
const trackCover = computed(() => props.track?.cover_url || '')
</script>

<template>
  <div class="player-bar" v-if="track">
    <audio
      ref="audioRef"
      :src="track.audio_url"
      @timeupdate="onTimeUpdate"
      @loadedmetadata="onLoadedMetadata"
      @ended="onEnded"
      @play="isPlaying = true"
      @pause="isPlaying = false"
    />

    <div class="player-left">
      <div class="player-cover" v-if="trackCover">
        <img :src="trackCover" alt="cover" />
      </div>
      <div class="player-cover player-cover-placeholder" v-else>
        <span>♪</span>
      </div>
      <div class="player-info">
        <div class="player-title">{{ trackTitle }}</div>
        <div class="player-artist">{{ track.style || 'AI 作曲' }}</div>
      </div>
    </div>

    <div class="player-center">
      <div class="player-controls">
        <button class="ctrl-btn" @click="togglePlay">
          <span v-if="isPlaying">⏸</span>
          <span v-else>▶</span>
        </button>
      </div>
      <div class="player-progress">
        <span class="time">{{ formatTime(currentTime) }}</span>
        <div class="progress-bar" @click="seek">
          <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          <div class="progress-dot" :style="{ left: progress + '%' }"></div>
        </div>
        <span class="time">{{ formatTime(duration) }}</span>
      </div>
    </div>

    <div class="player-right">
      <button class="action-btn" @click="downloadTrack" title="下载">
        ↓
      </button>
      <button class="action-btn speed-btn" @click="cycleSpeed" :title="`倍速 ${playbackRate}x`">
        {{ playbackRate }}x
      </button>
      <button class="action-btn" @click="showLyrics = !showLyrics">
        词
      </button>
      <button class="action-btn remix-btn" @click="emit('remix', track!)">
        Remix
      </button>
    </div>

    <Transition name="lyrics-slide">
      <div class="lyrics-panel" v-if="showLyrics">
        <div class="lyrics-header">
          <span>歌词</span>
          <button class="close-btn" @click="showLyrics = false">×</button>
        </div>
        <div class="lyrics-body">{{ trackLyrics }}</div>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.player-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  height: 72px;
  background: #111;
  border-top: 1px solid #222;
  display: flex;
  align-items: center;
  padding: 0 20px;
  z-index: 1000;
  gap: 20px;
}

.player-left {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 220px;
  flex-shrink: 0;
}

.player-cover {
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  flex-shrink: 0;
}

.player-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.player-cover-placeholder {
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: #b8860b;
}

.player-info {
  min-width: 0;
}

.player-title {
  font-size: 14px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.player-artist {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.4);
  margin-top: 2px;
}

.player-center {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.player-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.ctrl-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #b8860b;
  border: none;
  color: #000;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.ctrl-btn:hover {
  background: #daa520;
  transform: scale(1.05);
}

.player-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  max-width: 500px;
}

.time {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  min-width: 36px;
  text-align: center;
}

.progress-bar {
  flex: 1;
  height: 4px;
  background: #333;
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: #b8860b;
  border-radius: 2px;
  transition: width 0.1s linear;
}

.progress-dot {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 10px;
  height: 10px;
  background: #fff;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.2s;
}

.progress-bar:hover .progress-dot {
  opacity: 1;
}

.player-right {
  display: flex;
  align-items: center;
  gap: 6px;
  width: 240px;
  justify-content: flex-end;
  flex-shrink: 0;
}

.action-btn {
  padding: 4px 12px;
  border: 1px solid #333;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.action-btn:hover {
  border-color: #b8860b;
  color: #b8860b;
}

.remix-btn:hover {
  border-color: #daa520;
  color: #daa520;
}

.speed-btn {
  min-width: 40px;
  font-variant-numeric: tabular-nums;
}

.speed-btn:hover {
  border-color: #daa520;
  color: #daa520;
}

.lyrics-panel {
  position: fixed;
  bottom: 72px;
  right: 20px;
  width: 320px;
  max-height: 400px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px 12px 0 0;
  overflow: hidden;
  z-index: 999;
}

.lyrics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #222;
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
}

.close-btn {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 18px;
  cursor: pointer;
}

.close-btn:hover {
  color: #fff;
}

.lyrics-body {
  padding: 16px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
  max-height: 340px;
  overflow-y: auto;
}

.lyrics-body::-webkit-scrollbar {
  width: 4px;
}

.lyrics-body::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

.lyrics-slide-enter-active,
.lyrics-slide-leave-active {
  transition: all 0.3s ease;
}

.lyrics-slide-enter-from,
.lyrics-slide-leave-to {
  transform: translateY(20px);
  opacity: 0;
}
</style>
