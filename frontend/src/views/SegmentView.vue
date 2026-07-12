<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, MoreFilled } from '@element-plus/icons-vue'
import { getSegmentDetail, sliceAudio, extractLyrics, separateAudio as separateAudioApi, smartSlice as smartSliceApi, updateLyrics, updateSliceLyrics, getSegmentPitches, regenerateChenzi } from '@/api/segments'
import { extractAudio } from '@/api/upload'
import { getMapping } from '@/api/chenzi'
import { playMelody, stopMelody, getIsPlaying, setOnNoteCallback } from '@/utils/audio'
import type { OperaSegment, SegmentSlice } from '@/types'

const route = useRoute()
const router = useRouter()

const segment = ref<OperaSegment | null>(null)
const slices = ref<SegmentSlice[]>([])
const loading = ref(false)
const slicing = ref(false)
const extracting = ref(false)
const fullLyrics = ref("")
const extractingLyrics = ref(false)
const separating = ref(false)


const displayMode = ref<'lyrics' | 'chenzi'>('lyrics')  // 原词/衬字切换
const chenziMapping = ref<Record<string, string>>({})  // 衬字映射表

// 歌词编辑状态
const editingFullLyrics = ref(false)
const editingLyricsText = ref('')
const savingLyrics = ref(false)

// 切片行内编辑状态
const editingSliceId = ref<number | null>(null)
const editingSliceText = ref('')
const savingSlice = ref(false)

// 音高数据
const fullPitches = ref<(number | null)[]>([])
const pitchesLoaded = ref(false)
const pitchesLoading = ref(false)
const pitchDisplayMode = ref<'lyrics' | 'chenzi'>('lyrics')  // 音高显示模式：歌词/衬字
const playingSliceId = ref<number | null>(null)  // 正在播放哼唱的切片 ID
const chenziHighlightIndex = ref<number>(-1)  // 当前高亮的衬字索引

// 音高放大弹窗
const zoomDialogVisible = ref(false)
const zoomedSlice = ref<SegmentSlice | null>(null)

// 动画状态
const animating = ref(false)
const animationProgress = ref(0)
const animationSpeed = ref(1)
const animationFrameId = ref<number | null>(null)
const animationStartTime = ref(0)
const zoomAudioRef = ref<HTMLAudioElement | null>(null)

// 切片音频播放模式
const sliceAudioMode = ref<'slice' | 'vocal' | 'accompaniment'>('slice')

// 循环播放
const isMainAudioLoop = ref(false)
const isMainVideoLoop = ref(false)
const isVocalLoop = ref(false)
const isAccompanimentLoop = ref(false)
const sliceAudioRefs = new Map<number, HTMLAudioElement>()
const playingSliceAudioId = ref<number | null>(null)
const lyricsHighlightIndex = ref<number>(-1)

const setSliceAudioRef = (sliceId: number) => (el: any) => {
  if (el) {
    sliceAudioRefs.set(sliceId, el as HTMLAudioElement)
    el.addEventListener('play', () => {
      playingSliceAudioId.value = sliceId
      lyricsHighlightIndex.value = -1
      chenziHighlightIndex.value = -1
    })
    el.addEventListener('pause', () => {
      if (playingSliceAudioId.value === sliceId) {
        playingSliceAudioId.value = null
        lyricsHighlightIndex.value = -1
        if (playingSliceId.value !== sliceId) chenziHighlightIndex.value = -1
      }
    })
    el.addEventListener('ended', () => {
      if (playingSliceAudioId.value === sliceId) {
        playingSliceAudioId.value = null
        lyricsHighlightIndex.value = -1
        if (playingSliceId.value !== sliceId) chenziHighlightIndex.value = -1
      }
    })
    el.addEventListener('timeupdate', () => {
      if (playingSliceAudioId.value === sliceId && el.duration > 0) {
        const slice = slices.value.find(s => s.id === sliceId)
        const progress = el.currentTime / el.duration
        if (slice?.lyrics) {
          const chars = [...slice.lyrics.replace(/\s+/g, '')]
          if (chars.length > 0) {
            lyricsHighlightIndex.value = Math.floor(progress * chars.length)
          }
        }
        if (slice?.chenzi_lyrics) {
          const chenzis = slice.chenzi_lyrics.split('-').filter(c => c.trim())
          if (chenzis.length > 0) {
            chenziHighlightIndex.value = Math.floor(progress * chenzis.length)
          }
        }
      }
    })
  } else {
    sliceAudioRefs.delete(sliceId)
  }
}

const toggleMainAudioLoop = () => {
  const audio = document.querySelector('.audio-element') as HTMLAudioElement
  if (audio) {
    audio.loop = !audio.loop
    isMainAudioLoop.value = audio.loop
  }
}

const toggleMainVideoLoop = () => {
  const video = document.querySelector('.video-element') as HTMLVideoElement
  if (video) {
    video.loop = !video.loop
    isMainVideoLoop.value = video.loop
  }
}

const toggleVocalLoop = () => {
  const audio = document.querySelector('.vocal-player .audio-element') as HTMLAudioElement
  if (audio) {
    audio.loop = !audio.loop
    isVocalLoop.value = audio.loop
  }
}

const toggleAccompanimentLoop = () => {
  const audio = document.querySelector('.accompaniment-player .audio-element') as HTMLAudioElement
  if (audio) {
    audio.loop = !audio.loop
    isAccompanimentLoop.value = audio.loop
  }
}

const toggleSliceLoop = (sliceId: number) => {
  const audio = sliceAudioRefs.get(sliceId)
  if (audio) {
    audio.loop = !audio.loop
  }
}

const downloadSliceAudio = (slice: SegmentSlice) => {
  if (!slice.audio_url) return
  const link = document.createElement('a')
  link.href = slice.audio_url
  link.download = `slice_${slice.slice_index}.wav`
  link.click()
}

const setSlicePlaybackSpeed = (sliceId: number, speed: number) => {
  const audio = sliceAudioRefs.get(sliceId)
  if (audio) {
    audio.playbackRate = speed
    ElMessage.success(`播放速度：${speed}x`)
  }
}

// 浮动参考面板
const showChenziPanel = ref(false)
const panelPosition = ref({ right: '20px', bottom: '20px' })
const isDragging = ref(false)
const dragOffset = ref({ x: 0, y: 0 })

const chenziGuide = [
  { char: '啊', pinyin: 'ā', desc: '练通道与打开', keywords: '宽广 通畅 宏大 垂直 敞亮' },
  { char: '哎', pinyin: 'ái', desc: '练靠前与明亮', keywords: '清脆 鲜活 靠前 积极' },
  { char: '咦', pinyin: 'yí', desc: '练高位置与面罩共鸣', keywords: '穿透 鲜亮 眉心震' },
  { char: '呦', pinyin: 'yōu', desc: '练咽腔打开与声音竖立', keywords: '圆润 立体 空间 包满' },
  { char: '呜', pinyin: 'wū', desc: '练喉头稳定与混声/掩盖', keywords: '温暖 深厚 暗 包裹感' },
  { char: '啦', pinyin: 'lā', desc: '练舌头灵活与声音弹跳', keywords: '弹跳 灵活 颗粒 轻快' },
  { char: '嘻', pinyin: 'xī', desc: '练气息下沉与轻巧高位置', keywords: '轻巧 叹气 弱声 集中' },
]

const panelStyle = computed(() => ({
  right: panelPosition.value.right,
  bottom: panelPosition.value.bottom,
}))

const startDrag = (e: MouseEvent) => {
  isDragging.value = true
  dragOffset.value = { x: e.clientX, y: e.clientY }
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

const onDrag = (e: MouseEvent) => {
  if (!isDragging.value) return
  const dx = e.clientX - dragOffset.value.x
  const dy = e.clientY - dragOffset.value.y
  dragOffset.value = { x: e.clientX, y: e.clientY }
  const currentRight = parseInt(panelPosition.value.right) - dx
  const currentBottom = parseInt(panelPosition.value.bottom) - dy
  panelPosition.value = {
    right: Math.max(0, currentRight) + 'px',
    bottom: Math.max(0, currentBottom) + 'px',
  }
}

const stopDrag = () => {
  isDragging.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

const getSliceAudioUrl = (slice: SegmentSlice) => {
  if (sliceAudioMode.value === 'vocal' && segment.value?.vocal_url) {
    // 播放完整人声（仅当切片无音频时）
    return slice.audio_url || segment.value.vocal_url
  }
  if (sliceAudioMode.value === 'accompaniment' && segment.value?.accompaniment_url) {
    // 播放伴奏（仅当切片无音频时）
    return slice.audio_url || segment.value.accompaniment_url
  }
  return slice.audio_url
}

const loadPitches = async () => {
  if (pitchesLoaded.value || !segment.value) return
  pitchesLoading.value = true
  try {
    const { data } = await getSegmentPitches(segment.value.id)
    // 将音高数据合并到对应切片
    const pitchMap = new Map(data.slices.map((s: any) => [s.slice_id, s.pitches]))
    slices.value = slices.value.map(s => ({
      ...s,
      pitches: pitchMap.get(s.id) || s.pitches
    }))
    pitchesLoaded.value = true
  } catch (e) {
    ElMessage.error('音高提取失败')
  } finally {
    pitchesLoading.value = false
  }
}

const handleRegenerateChenzi = async () => {
  if (!segment.value) return
  try {
    const { data } = await regenerateChenzi(segment.value.id)
    ElMessage.success(data.message)
    // 刷新切片数据
    await fetchDetail()
  } catch (e) {
    ElMessage.error('重新生成衬字失败')
  }
}

// 播放衬字哼唱
const playChenziMelody = async (slice: SegmentSlice) => {
  if (!slice.numbered_notation) {
    ElMessage.warning('没有简谱数据')
    return
  }

  // 如果正在播放这个切片，停止
  if (playingSliceId.value === slice.id) {
    stopMelody()
    setOnNoteCallback(null)
    playingSliceId.value = null
    chenziHighlightIndex.value = -1
    return
  }

  // 停止其他播放
  stopMelody()
  setOnNoteCallback(null)
  playingSliceId.value = slice.id
  chenziHighlightIndex.value = -1

  const duration = slice.end_time - slice.start_time

  // 设置音符回调，用于高亮衬字
  setOnNoteCallback((index: number) => {
    chenziHighlightIndex.value = index
  })

  try {
    await playMelody(slice.numbered_notation, duration)
  } catch (e) {
    ElMessage.error('播放失败')
  } finally {
    playingSliceId.value = null
    chenziHighlightIndex.value = -1
    setOnNoteCallback(null)
  }
}

const segmentId = parseInt(route.params.id as string)

const fetchDetail = async () => {
  loading.value = true
  try {
    const { data } = await getSegmentDetail(segmentId)
    segment.value = data
    slices.value = data.slices || []
  } catch (e) {
    // 已处理
  } finally {
    loading.value = false
  }
}

const handleExtractLyrics = async () => {
  if (!segment.value?.audio_url) {
    ElMessage.warning('没有音频文件')
    return
  }
  extractingLyrics.value = true
  try {
    const { data } = await extractLyrics(segment.value!.id)
    fullLyrics.value = data.full_lyrics
    ElMessage.success('歌词提取成功')
  } catch (e) {
    // 已处理
  } finally {
    extractingLyrics.value = false
  }
}

const handleSlice = async () => {
  slicing.value = true
  try {
    const { data } = await sliceAudio(segment.value!.id)
    ElMessage.success(`切片成功，共 ${data.slices.length} 个片段`)
    fullLyrics.value = data.full_lyrics
    slices.value = data.slices
  } catch (e) {
    // 已处理
  } finally {
    slicing.value = false
  }
}

const handleSeparate = async () => {
  if (!segment.value?.audio_url) {
    ElMessage.warning('没有音频文件')
    return
  }
  separating.value = true
  try {
    const { data } = await separateAudioApi(segment.value!.id)
    ElMessage.success('音频分离成功')
    segment.value!.vocal_url = data.vocal_url
    segment.value!.accompaniment_url = data.accompaniment_url
    segment.value!.is_separated = true
  } catch (e) {
    // 已处理
  } finally {
    separating.value = false
  }
}

const handleSmartSlice = async () => {
  if (!segment.value?.audio_url) {
    ElMessage.warning('没有音频文件')
    return
  }
  slicing.value = true
  try {
    const { data } = await smartSliceApi(segment.value!.id)
    ElMessage.success(`智能切片成功，共 ${data.slices.length} 个片段`)
    fullLyrics.value = data.full_lyrics
    slices.value = data.slices
    // 加载衬字映射表
    const { data: mappingData } = await getMapping()
    chenziMapping.value = mappingData.mapping
  } catch (e) {
    // 已处理
  } finally {
    slicing.value = false
  }
}

const handleExtractAudio = async () => {
  if (!segment.value?.video_url) {
    ElMessage.warning('没有视频文件')
    return
  }
  extracting.value = true
  try {
    const { data } = await extractAudio(segment.value.video_url)
    ElMessage.success('提取成功，请刷新页面')
  } catch (e) {
    // 已处理
  } finally {
    extracting.value = false
  }
}

// 完整歌词编辑
const startEditFullLyrics = () => {
  editingLyricsText.value = fullLyrics.value || segment.value?.lyrics || ''
  editingFullLyrics.value = true
}

const cancelEditFullLyrics = () => {
  editingFullLyrics.value = false
  editingLyricsText.value = ''
}

const saveFullLyrics = async () => {
  if (!segment.value) return
  savingLyrics.value = true
  try {
    await updateLyrics(segment.value.id, editingLyricsText.value)
    fullLyrics.value = editingLyricsText.value
    segment.value.lyrics = editingLyricsText.value
    editingFullLyrics.value = false
    ElMessage.success('歌词保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingLyrics.value = false
  }
}

const useForComposition = () => {
  const lyrics = fullLyrics.value || segment.value?.lyrics || ''
  if (!lyrics.trim()) {
    ElMessage.warning('没有可用的歌词')
    return
  }
  router.push({
    path: '/music',
    query: { lyrics, style: '古风' }
  })
}

const useAudioForComposition = (audioUrl: string) => {
  if (!audioUrl) {
    ElMessage.warning('没有可用的音频')
    return
  }
  const lyrics = fullLyrics.value || segment.value?.lyrics || ''
  router.push({
    path: '/music',
    query: {
      reference_audio: audioUrl,
      lyrics: lyrics || '',
      mode: 'bgm'
    }
  })
}

// 切片歌词行内编辑
const startEditSlice = (slice: SegmentSlice) => {
  editingSliceId.value = slice.id
  editingSliceText.value = slice.lyrics || ''
}

const cancelEditSlice = () => {
  editingSliceId.value = null
  editingSliceText.value = ''
}

const saveSliceLyrics = async (slice: SegmentSlice) => {
  if (!segment.value) return
  savingSlice.value = true
  try {
    await updateSliceLyrics(segment.value.id, slice.id, editingSliceText.value)
    slice.lyrics = editingSliceText.value
    editingSliceId.value = null
    editingSliceText.value = ''
    ElMessage.success('保存成功')
  } catch (e) {
    ElMessage.error('保存失败')
  } finally {
    savingSlice.value = false
  }
}

// 计算切片对应的音高索引范围（使用切片自己的 pitches）
const getSlicePitchRange = (slice: SegmentSlice) => {
  return slice.pitches || []
}

// 获取完整音高序列（所有切片拼接）
const getFullPitches = () => {
  if (!pitchesLoaded.value || slices.value.length === 0) return []
  return slices.value.flatMap(s => s.pitches || [])
}

// 获取带高亮状态的衬字字符（用于哼唱和音频播放动画）
const getChenziCharsWithHighlight = (slice: SegmentSlice) => {
  if (!slice.chenzi_lyrics) return []
  const chenzis = slice.chenzi_lyrics.split('-').filter(c => c.trim())
  const isActive =
    (playingSliceId.value === slice.id) ||
    (playingSliceAudioId.value === slice.id)
  return chenzis.map((chenzi, i) => ({
    chenzi,
    highlighted: isActive && i <= chenziHighlightIndex.value,
  }))
}

// 获取带高亮状态的歌词字符（用于切片音频播放动画）
const getLyricsCharsWithHighlight = (slice: SegmentSlice) => {
  if (!slice.lyrics) return []
  const chars = [...slice.lyrics.replace(/\s+/g, '')]
  return chars.map((char, i) => ({
    char,
    highlighted: playingSliceAudioId.value === slice.id && i <= lyricsHighlightIndex.value,
  }))
}

// 解析简谱和衬字，按音符分组
const parseNotationGroups = (notation: string, chenzi: string) => {
  if (!notation || !chenzi) return []
  const notes = notation.split(' ').filter(n => n.trim())
  const chenzis = chenzi.split('-').filter(c => c.trim())
  
  // 按节奏分组（每 4 个音符一组，模拟小节）
  const groups: Array<{ notes: string[], chenzis: string[] }> = []
  let currentGroup: { notes: string[], chenzis: string[] } = { notes: [], chenzis: [] }
  
  for (let i = 0; i < notes.length; i++) {
    currentGroup.notes.push(notes[i])
    if (i < chenzis.length) {
      currentGroup.chenzis.push(chenzis[i])
    }
    
    // 每 4 个音符分一组
    if (currentGroup.notes.length === 4 || i === notes.length - 1) {
      groups.push({ ...currentGroup })
      currentGroup = { notes: [], chenzis: [] }
    }
  }
  
  return groups
}

// 渲染音高火花线 SVG
const renderPitchSparkline = (pitches: (number | null)[], width = 120, height = 30) => {
  const validPitches = pitches.filter((p): p is number => p !== null)
  if (validPitches.length === 0) return ''

  const minFreq = Math.min(...validPitches)
  const maxFreq = Math.max(...validPitches)
  const range = maxFreq - minFreq || 1

  const padding = 2
  const drawWidth = width - padding * 2
  const drawHeight = height - padding * 2

  const points: string[] = []
  let x = padding
  const stepX = drawWidth / (pitches.length - 1 || 1)

  for (let i = 0; i < pitches.length; i++) {
    const p = pitches[i]
    if (p !== null) {
      const y = padding + drawHeight - ((p - minFreq) / range) * drawHeight
      points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
    }
    x += stepX
  }

  if (points.length < 2) return ''

  return `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    <polyline points="${points.join(' ')}" fill="none" stroke="#b8860b" stroke-width="1.5" stroke-linejoin="round"/>
  </svg>`
}

// 计算字符在图表中的 x 坐标位置
const getCharPositions = (lyrics: string, pitchCount: number, chartWidth: number, padding: number) => {
  const chars = [...lyrics.replace(/\s+/g, '')]
  if (chars.length === 0 || pitchCount <= 1) return []
  const drawWidth = chartWidth - padding * 2
  return chars.map((char, i) => ({
    char,
    x: padding + (i / (chars.length - 1 || 1)) * drawWidth,
  }))
}

// 获取衬字字符列表（从 numbered_notation 和 chenzi_lyrics）
const getChenziChars = (slice: SegmentSlice) => {
  if (!slice.numbered_notation || !slice.chenzi_lyrics) return []
  const notes = slice.numbered_notation.split(' ').filter(n => n.trim())
  const chenzis = slice.chenzi_lyrics.split('-').filter(c => c.trim())
  return notes.map((note, i) => ({
    note,
    chenzi: i < chenzis.length ? chenzis[i] : '?',
  }))
}

// 获取带高亮状态的衬字字符（用于下方显示）
const animatedChenziChars = computed(() => {
  const slice = zoomedSlice.value
  if (!slice) return []
  const chars = getChenziChars(slice)
  const progress = animationProgress.value
  const total = chars.length
  if (total === 0) return []

  return chars.map((c, i) => {
    const charProgress = i / (total - 1 || 1)
    const highlighted = progress > 0 && charProgress <= progress
    return {
      ...c,
      highlighted,
    }
  })
})

// 获取带高亮状态的歌词字符（用于下方显示）
const animatedLyricsChars = computed(() => {
  const slice = zoomedSlice.value
  if (!slice) return []
  const lyrics = slice.lyrics || ''
  const chars = [...lyrics.replace(/\s+/g, '')]
  const progress = animationProgress.value
  const total = chars.length
  if (total === 0) return []

  return chars.map((char, i) => {
    const charProgress = i / (total - 1 || 1)
    const highlighted = progress > 0 && charProgress <= progress
    return {
      char,
      highlighted,
    }
  })
})

// 渲染放大版音高图（含字符标注和动画进度线）
const zoomedPitchChart = computed(() => {
  const slice = zoomedSlice.value
  if (!slice) return ''
  const pitches = slice.pitches || []
  const width = 800
  const height = 200
  const padding = 40
  const charAreaHeight = 40

  const validPitches = pitches.filter((p): p is number => p !== null)
  if (validPitches.length === 0) return ''

  const minFreq = Math.min(...validPitches)
  const maxFreq = Math.max(...validPitches)
  const range = maxFreq - minFreq || 1

  const drawWidth = width - padding * 2
  const drawHeight = height - padding * 2 - charAreaHeight

  const points: string[] = []
  let x = padding
  const stepX = drawWidth / (pitches.length - 1 || 1)

  for (let i = 0; i < pitches.length; i++) {
    const p = pitches[i]
    if (p !== null) {
      const y = padding + drawHeight - ((p - minFreq) / range) * drawHeight
      points.push(`${x.toFixed(1)},${y.toFixed(1)}`)
    }
    x += stepX
  }

  if (points.length < 2) return ''

  // 根据模式获取字符
  const isChenziMode = pitchDisplayMode.value === 'chenzi'
  let chars: Array<{ char: string; x: number }> = []

  if (isChenziMode) {
    // 衬字模式：显示简谱+衬字
    const chenziChars = getChenziChars(slice)
    if (chenziChars.length === 0) return ''
    const chenziDrawWidth = width - padding * 2
    chars = chenziChars.map((c, i) => ({
      char: `${c.note}\n${c.chenzi}`,
      x: padding + (i / (chenziChars.length - 1 || 1)) * chenziDrawWidth,
    }))
  } else {
    // 歌词模式
    const lyrics = slice.lyrics || ''
    chars = getCharPositions(lyrics, pitches.length, width, padding)
  }

  const progress = animationProgress.value
  const progressX = padding + progress * drawWidth

  let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg" style="user-select:none">`

  // 网格线
  for (let i = 0; i <= 4; i++) {
    const gy = padding + (drawHeight / 4) * i
    const freq = maxFreq - (range / 4) * i
    svg += `<line x1="${padding}" y1="${gy}" x2="${width - padding}" y2="${gy}" stroke="rgba(58,90,120,0.1)" stroke-width="0.5"/>`
    svg += `<text x="${padding - 5}" y="${gy + 4}" text-anchor="end" font-size="10" fill="#999">${Math.round(freq)}Hz</text>`
  }

  // 音高曲线
  svg += `<polyline points="${points.join(' ')}" fill="none" stroke="#b8860b" stroke-width="2" stroke-linejoin="round"/>`

  // 字符标注
  const charY = height - padding + 15
  chars.forEach((c) => {
    const highlighted = progress > 0 && c.x <= progressX
    const color = highlighted ? '#b8860b' : '#aaa'
    const weight = highlighted ? '700' : '400'
    const size = highlighted ? '13' : '11'

    if (isChenziMode && c.char.includes('\n')) {
      // 衬字模式：两行显示（简谱+衬字）
      const [note, chenzi] = c.char.split('\n')
      svg += `<text x="${c.x}" y="${charY - 8}" text-anchor="middle" font-size="${size}" font-weight="${weight}" fill="${color}">${note}</text>`
      svg += `<text x="${c.x}" y="${charY + 8}" text-anchor="middle" font-size="${size}" font-weight="${weight}" fill="${color}">${chenzi}</text>`
    } else {
      svg += `<text x="${c.x}" y="${charY}" text-anchor="middle" font-size="${size}" font-weight="${weight}" fill="${color}">${c.char}</text>`
    }
  })

  // 进度线
  if (progress > 0 && progress < 1) {
    svg += `<line x1="${progressX}" y1="${padding}" x2="${progressX}" y2="${height - padding}" stroke="#b8860b" stroke-width="2" opacity="0.8"/>`
    svg += `<circle cx="${progressX}" cy="${padding}" r="4" fill="#b8860b"/>`
  }

  svg += `</svg>`
  return svg
})

// 打开放大弹窗
const openPitchZoom = (slice: SegmentSlice) => {
  zoomedSlice.value = slice
  animationProgress.value = 0
  animating.value = false
  if (animationFrameId.value) {
    cancelAnimationFrame(animationFrameId.value)
    animationFrameId.value = null
  }
  // 重置音频
  nextTick(() => {
    const audio = zoomAudioRef.value
    if (audio) {
      audio.pause()
      audio.currentTime = 0
      audio.playbackRate = animationSpeed.value
    }
  })
  zoomDialogVisible.value = true
}

// 音频驱动动画
const updateProgressFromAudio = () => {
  const audio = zoomAudioRef.value
  const slice = zoomedSlice.value
  if (!audio || !slice) return
  const duration = slice.end_time - slice.start_time
  if (duration <= 0) return
  const progress = Math.min(audio.currentTime / duration, 1)
  animationProgress.value = progress
  if (progress >= 1) {
    animating.value = false
  }
}

// 开始动画（播放音频）
const startAnimation = () => {
  const audio = zoomAudioRef.value
  const slice = zoomedSlice.value
  if (!audio || !slice) return
  audio.playbackRate = animationSpeed.value
  audio.currentTime = 0
  audio.play()
  animating.value = true
  animationProgress.value = 0
}

// 停止动画（暂停音频）
const stopAnimation = () => {
  const audio = zoomAudioRef.value
  if (audio) audio.pause()
  animating.value = false
}

// 重置动画
const resetAnimation = () => {
  const audio = zoomAudioRef.value
  if (audio) {
    audio.pause()
    audio.currentTime = 0
  }
  animating.value = false
  animationProgress.value = 0
}

// 速度变化
const onSpeedChange = () => {
  const audio = zoomAudioRef.value
  if (audio) {
    audio.playbackRate = animationSpeed.value
  }
}

// 音频播放结束
const onAudioEnded = () => {
  animating.value = false
  animationProgress.value = 1
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="segment-container">
    <!-- 顶部导航 -->
    <header class="header">
      <div class="header-left">
        <button class="back-nav" @click="segment?.work_id ? router.push(`/works/${segment.work_id}/segments`) : router.push('/hub')">← 返回</button>
        <span class="logo">影子戏</span>
        <span class="logo-sub">唱段详情</span>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- 主内容 -->
    <main v-else-if="segment" class="main-content fade-in">
      <!-- 基本信息 -->
      <div class="info-card dreamy-card">
        <h2 class="dreamy-title">{{ segment.name }}</h2>
        <p class="meta">唱段详情</p>
      </div>

      <!-- 播放器 -->
      <div v-if="segment.audio_url || segment.video_url" class="player-section">
        <div v-if="segment.video_url" class="video-player dreamy-card">
          <div class="player-card-header">
            <h3>视频播放</h3>
            <div class="player-header-actions">
              <el-button size="small" type="warning" @click="useAudioForComposition(segment.video_url)">用于AI作曲</el-button>
              <el-dropdown trigger="click">
                <el-button :icon="MoreFilled" circle size="small" text />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="toggleMainVideoLoop">
                      {{ isMainVideoLoop ? '取消循环' : '循环播放' }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <video
            :src="segment.video_url"
            controls
            preload="metadata"
            class="video-element"
          >
            您的浏览器不支持视频播放
          </video>
        </div>
        <div v-if="segment.audio_url" class="audio-player dreamy-card">
          <div class="player-card-header">
            <h3>原始音频</h3>
            <div class="player-header-actions">
              <el-button size="small" type="warning" @click="useAudioForComposition(segment.audio_url)">用于AI作曲</el-button>
              <el-dropdown trigger="click">
                <el-button :icon="MoreFilled" circle size="small" text />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="toggleMainAudioLoop">
                      {{ isMainAudioLoop ? '取消循环' : '循环播放' }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <audio
            :src="segment.audio_url"
            controls
            preload="metadata"
            class="audio-element"
          >
            您的浏览器不支持音频播放
          </audio>
        </div>
        <!-- 分离后的人声和伴奏 -->
        <div v-if="segment.is_separated && segment.vocal_url" class="vocal-player dreamy-card">
          <div class="player-card-header">
            <h3>🎤 纯人声（跟着哼唱）</h3>
            <div class="player-header-actions">
              <el-button size="small" type="warning" @click="useAudioForComposition(segment.vocal_url)">用于AI作曲</el-button>
              <el-dropdown trigger="click">
                <el-button :icon="MoreFilled" circle size="small" text />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="toggleVocalLoop">
                      {{ isVocalLoop ? '取消循环' : '循环播放' }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <audio
            :src="segment.vocal_url"
            controls
            preload="metadata"
            class="audio-element"
          >
            您的浏览器不支持音频播放
          </audio>
        </div>
        <div v-if="segment.is_separated && segment.accompaniment_url" class="accompaniment-player dreamy-card">
          <div class="player-card-header">
            <h3>🎵 纯伴奏</h3>
            <div class="player-header-actions">
              <el-button size="small" type="warning" @click="useAudioForComposition(segment.accompaniment_url)">用于AI作曲</el-button>
              <el-dropdown trigger="click">
                <el-button :icon="MoreFilled" circle size="small" text />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item @click="toggleAccompanimentLoop">
                      {{ isAccompanimentLoop ? '取消循环' : '循环播放' }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
          <audio
            :src="segment.accompaniment_url"
            controls
            preload="metadata"
            class="audio-element"
          >
            您的浏览器不支持音频播放
          </audio>
        </div>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button
          v-if="segment.video_url && !segment.audio_url"
          type="warning"
          class="dreamy-btn"
          :loading="extracting"
          @click="handleExtractAudio"
        >
          从视频提取音频
        </el-button>
        <el-button
          v-if="segment.audio_url"
          type="info"
          class="dreamy-btn"
          :loading="separating"
          :disabled="segment.is_separated"
          @click="handleSeparate"
        >
          {{ segment.is_separated ? '已分离' : '音频分离' }}
        </el-button>
        <el-button
          v-if="segment.audio_url"
          type="success"
          class="dreamy-btn"
          :loading="extractingLyrics"
          @click="handleExtractLyrics"
        >
          提取歌词
        </el-button>
        <el-button
          type="primary"
          class="dreamy-btn"
          :loading="slicing"
          :disabled="!segment.audio_url"
          @click="handleSmartSlice"
        >
          智能切片
        </el-button>
      </div>

      <!-- 完整歌词 -->
      <div v-if="segment.audio_url" class="lyrics-section dreamy-card">
        <div class="lyrics-header">
          <h3>完整歌词</h3>
          <div class="lyrics-header-actions">
            <el-button v-if="fullLyrics || segment.lyrics" size="small" type="warning" @click="useForComposition">用于AI作曲</el-button>
            <el-button v-if="fullLyrics || segment.lyrics" size="small" type="primary" text @click="startEditFullLyrics">编辑</el-button>
          </div>
        </div>
        <!-- 编辑模式 -->
        <div v-if="editingFullLyrics" class="lyrics-edit">
          <el-input
            v-model="editingLyricsText"
            type="textarea"
            :rows="8"
            placeholder="编辑歌词..."
            class="lyrics-textarea"
          />
          <div class="edit-actions">
            <el-button size="small" @click="cancelEditFullLyrics">取消</el-button>
            <el-button size="small" type="primary" :loading="savingLyrics" @click="saveFullLyrics">保存</el-button>
          </div>
        </div>
        <!-- 只读模式 -->
        <div v-else-if="fullLyrics" class="lyrics-content">{{ fullLyrics }}</div>
        <el-empty v-else-if="segment.lyrics" description="已保存歌词" :image-size="60">
          <template #description>
            <div class="lyrics-content preview-lyrics">{{ segment.lyrics }}</div>
          </template>
        </el-empty>
        <el-empty v-else description="点击'提取歌词'按钮识别音频中的歌词" :image-size="80" />
      </div>

      <!-- 切片列表 -->
      <div class="slices-section">
        <div class="slices-header">
          <h3>切片列表 ({{ slices.length }})</h3>
          <el-button-group v-if="slices.length > 0">
            <el-button
              :type="displayMode === 'lyrics' ? 'primary' : 'default'"
              @click="displayMode = 'lyrics'"
            >
              原词模式
            </el-button>
            <el-button
              :type="displayMode === 'chenzi' ? 'warning' : 'default'"
              @click="displayMode = 'chenzi'"
            >
              衬字哼唱
            </el-button>
            <el-button
              :type="pitchesLoaded ? 'success' : 'default'"
              :loading="pitchesLoading"
              @click="loadPitches"
            >
              {{ pitchesLoaded ? '音高曲线' : '加载音高' }}
            </el-button>
            <el-button
              v-if="pitchesLoaded"
              type="warning"
              @click="handleRegenerateChenzi"
            >
              重新生成衬字
            </el-button>
            <el-button
              v-if="pitchesLoaded"
              :type="pitchDisplayMode === 'lyrics' ? 'primary' : 'default'"
              size="small"
              @click="pitchDisplayMode = 'lyrics'"
            >
              音高+歌词
            </el-button>
            <el-button
              v-if="pitchesLoaded"
              :type="pitchDisplayMode === 'chenzi' ? 'warning' : 'default'"
              size="small"
              @click="pitchDisplayMode = 'chenzi'"
            >
              音高+衬字
            </el-button>
          </el-button-group>
        </div>

        <!-- 音频播放模式 -->
        <div v-if="slices.length > 0 && segment?.is_separated" class="audio-mode-bar">
          <span class="audio-mode-label">播放模式：</span>
          <el-radio-group v-model="sliceAudioMode" size="small">
            <el-radio-button value="slice">切片音频</el-radio-button>
            <el-radio-button value="vocal">纯人声</el-radio-button>
            <el-radio-button value="accompaniment">纯伴奏</el-radio-button>
          </el-radio-group>
        </div>

        <!-- 完整音高曲线 -->
        <div v-if="pitchesLoaded && getFullPitches().length > 0" class="pitch-overview dreamy-card">
          <h4>音高曲线</h4>
          <div class="pitch-chart" v-html="renderPitchSparkline(getFullPitches(), 1100, 80)"></div>
        </div>

        <!-- 衬字映射提示 -->
        <div v-if="displayMode === 'chenzi' && Object.keys(chenziMapping).length > 0" class="chenzi-hint dreamy-card">
          <h4>衬字映射（跟着哼唱）</h4>
          <div class="chenzi-mapping">
            <span v-for="(val, key) in chenziMapping" :key="key" class="mapping-item">
              <span class="digit">{{ key }}</span>
              <span class="chenzi">{{ val }}</span>
            </span>
          </div>
        </div>
        
        <el-empty v-if="slices.length === 0" description="暂无切片，请点击'智能切片'" />
        
        <el-table v-else :data="slices" style="width: 100%" class="dreamy-table">
          <el-table-column prop="slice_index" label="序号" width="80" />
          <el-table-column label="开始时间" width="100">
            <template #default="{ row }">
              {{ formatTime(row.start_time) }}
            </template>
          </el-table-column>
          <el-table-column label="结束时间" width="100">
            <template #default="{ row }">
              {{ formatTime(row.end_time) }}
            </template>
          </el-table-column>
          <el-table-column label="时长" width="80">
            <template #default="{ row }">
              {{ (row.end_time - row.start_time).toFixed(1) }}s
            </template>
          </el-table-column>
          <el-table-column label="音频" width="240">
            <template #default="{ row }">
              <div v-if="row.audio_url" class="slice-audio-wrapper">
                <audio
                  :ref="setSliceAudioRef(row.id)"
                  :src="row.audio_url"
                  controls
                  style="width: 100%; height: 32px"
                  class="slice-audio"
                />
                <el-dropdown trigger="click">
                  <el-button :icon="MoreFilled" circle size="small" text class="slice-menu-btn" />
                  <template #dropdown>
                    <el-dropdown-menu>
                      <el-dropdown-item @click="toggleSliceLoop(row.id)">
                        循环播放
                      </el-dropdown-item>
                      <el-dropdown-item @click="downloadSliceAudio(row)">
                        下载音频
                      </el-dropdown-item>
                      <el-dropdown-item @click="useAudioForComposition(row.audio_url)">
                        用于AI作曲
                      </el-dropdown-item>
                      <el-dropdown-item divided @click="setSlicePlaybackSpeed(row.id, 0.5)">
                        0.5x 速度
                      </el-dropdown-item>
                      <el-dropdown-item @click="setSlicePlaybackSpeed(row.id, 0.7)">
                        0.7x 速度
                      </el-dropdown-item>
                      <el-dropdown-item @click="setSlicePlaybackSpeed(row.id, 0.9)">
                        0.9x 速度
                      </el-dropdown-item>
                      <el-dropdown-item @click="setSlicePlaybackSpeed(row.id, 1.0)">
                        1.0x 正常
                      </el-dropdown-item>
                    </el-dropdown-menu>
                  </template>
                </el-dropdown>
              </div>
              <span v-else style="color: #999">-</span>
            </template>
          </el-table-column>
          <el-table-column :label="displayMode === 'lyrics' ? '原词' : '衬字谱'" min-width="250">
            <template #default="{ row }">
              <!-- 编辑模式 -->
              <div v-if="editingSliceId === row.id && displayMode === 'lyrics'">
                <el-input
                  v-model="editingSliceText"
                  type="textarea"
                  :rows="2"
                  size="small"
                  class="slice-edit-input"
                />
                <div class="slice-edit-actions">
                  <el-button size="small" text @click="cancelEditSlice">取消</el-button>
                  <el-button size="small" type="primary" :loading="savingSlice" @click="saveSliceLyrics(row)">保存</el-button>
                </div>
              </div>
              <!-- 只读模式 -->
              <div v-else>
                <div v-if="displayMode === 'lyrics'">
                  <div v-if="row.lyrics" class="slice-lyrics-animated">
                    <span v-for="(c, i) in getLyricsCharsWithHighlight(row)" :key="i" :class="{ 'lyrics-highlighted': c.highlighted }">
                      {{ c.char }}
                    </span>
                  </div>
                  <div v-else class="slice-lyrics">-</div>
                </div>
                <div v-else class="slice-chenzi-row">
                  <div class="slice-chenzi-animated">
                    <span v-for="(c, i) in getChenziCharsWithHighlight(row)" :key="i" :class="{ 'chenzi-highlighted': c.highlighted }">
                      {{ c.chenzi }}
                    </span>
                  </div>
                  <el-button
                    v-if="row.numbered_notation"
                    size="small"
                    :type="playingSliceId === row.id ? 'danger' : 'primary'"
                    text
                    class="play-chenzi-btn"
                    @click="playChenziMelody(row)"
                  >
                    {{ playingSliceId === row.id ? '停止' : '哼唱' }}
                  </el-button>
                </div>
                <el-button v-if="displayMode === 'lyrics' && row.lyrics" size="small" text type="primary" class="slice-edit-btn" @click="startEditSlice(row)">编辑</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column v-if="pitchesLoaded" label="音高" min-width="200">
            <template #default="{ row }">
              <div class="pitch-display">
                <!-- 音高曲线 -->
                <div v-if="getSlicePitchRange(row).filter(p => p !== null).length >= 2"
                     class="pitch-sparkline pitch-sparkline-clickable"
                     v-html="renderPitchSparkline(getSlicePitchRange(row))"
                     @click="openPitchZoom(row)"
                     title="点击放大查看"
                ></div>
                <div v-else class="pitch-sparkline-empty">-</div>
                
                <!-- 歌词/衬字显示 -->
                <div v-if="pitchDisplayMode === 'lyrics'" class="pitch-lyrics">
                  {{ row.lyrics || '-' }}
                </div>
                <div v-else class="pitch-chenzi-groups">
                  <template v-if="row.numbered_notation && row.chenzi_lyrics">
                    <div v-for="(group, idx) in parseNotationGroups(row.numbered_notation, row.chenzi_lyrics)" 
                         :key="idx" 
                         class="chenzi-group">
                      <div class="group-notes">{{ group.notes.join(' ') }}</div>
                      <div class="group-chenzis">{{ group.chenzis.join('-') }}</div>
                    </div>
                  </template>
                  <span v-else style="color: #ccc">-</span>
                </div>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="commands" label="指令" />
        </el-table>
      </div>
    </main>

    <!-- 音高放大弹窗 -->
    <el-dialog
      v-model="zoomDialogVisible"
      :title="zoomedSlice ? `音高曲线 - 第${zoomedSlice.slice_index}句` : ''"
      width="860px"
      class="zoom-dialog"
      @close="stopAnimation"
    >
      <div v-if="zoomedSlice" class="zoom-content">
        <!-- 隐藏音频元素 -->
        <audio
          v-if="zoomedSlice.audio_url"
          ref="zoomAudioRef"
          :src="zoomedSlice.audio_url"
          @timeupdate="updateProgressFromAudio"
          @ended="onAudioEnded"
          style="display:none"
        />

        <!-- 信息栏 -->
        <div class="zoom-info">
          <span class="zoom-time">{{ formatTime(zoomedSlice.start_time) }} → {{ formatTime(zoomedSlice.end_time) }}</span>
          <span class="zoom-duration">时长 {{ (zoomedSlice.end_time - zoomedSlice.start_time).toFixed(1) }}s</span>
          <span v-if="animating || animationProgress > 0" class="zoom-progress-time">
            {{ formatTime(zoomedSlice.start_time + animationProgress * (zoomedSlice.end_time - zoomedSlice.start_time)) }}
          </span>
        </div>

        <!-- 音高图 -->
        <div class="zoom-chart" v-html="zoomedPitchChart"></div>

        <!-- 歌词/衬字显示 -->
        <div v-if="pitchDisplayMode === 'lyrics'" class="zoom-lyrics-animated">
          <span v-for="(c, i) in animatedLyricsChars" :key="i" :class="{ 'char-highlighted': c.highlighted }">
            {{ c.char }}
          </span>
        </div>
        <div v-else class="zoom-chenzi-animated">
          <div class="zoom-notation-row">
            <span v-for="(c, i) in animatedChenziChars" :key="i" :class="{ 'char-highlighted': c.highlighted }" class="notation-char">
              {{ c.note }}
            </span>
          </div>
          <div class="zoom-chenzi-row">
            <span v-for="(c, i) in animatedChenziChars" :key="i" :class="{ 'char-highlighted': c.highlighted }" class="chenzi-char">
              {{ c.chenzi }}
            </span>
          </div>
        </div>

        <!-- 动画控制栏 -->
        <div class="zoom-controls">
          <el-button
            :type="animating ? 'danger' : 'primary'"
            size="small"
            @click="animating ? stopAnimation() : (animationProgress >= 1 ? resetAnimation() : startAnimation())"
          >
            {{ animating ? '停止' : (animationProgress >= 1 ? '重播' : '播放') }}
          </el-button>
          <el-button size="small" @click="resetAnimation" :disabled="animationProgress === 0 && !animating">
            重置
          </el-button>
          <span class="speed-label">速度：</span>
          <el-radio-group v-model="animationSpeed" size="small" @change="onSpeedChange">
            <el-radio-button :value="0.5">0.5x</el-radio-button>
            <el-radio-button :value="0.7">0.7x</el-radio-button>
            <el-radio-button :value="0.9">0.9x</el-radio-button>
            <el-radio-button :value="1">1x</el-radio-button>
          </el-radio-group>
        </div>
      </div>
    </el-dialog>


    <!-- 浮动衬字参考面板 -->
    <div class="chenzi-panel-wrapper" :style="panelStyle">
      <transition name="panel-fade">
        <div v-if="showChenziPanel" class="chenzi-floating-panel">
          <div class="panel-header" @mousedown="startDrag">
            <span class="panel-title">衬字发声指南</span>
            <el-button size="small" text @click="showChenziPanel = false">✕</el-button>
          </div>
          <div class="panel-body">
            <div v-for="item in chenziGuide" :key="item.char" class="guide-item">
              <div class="guide-char-row">
                <span class="guide-char">{{ item.char }}</span>
                <span class="guide-pinyin">({{ item.pinyin }})</span>
              </div>
              <div class="guide-desc">{{ item.desc }}</div>
              <div class="guide-keywords">{{ item.keywords }}</div>
            </div>
          </div>
        </div>
      </transition>
      <el-button
        class="chenzi-panel-toggle"
        :type="showChenziPanel ? 'warning' : 'primary'"
        circle
        @click="showChenziPanel = !showChenziPanel"
      >
        {{ showChenziPanel ? '✕' : '参' }}
      </el-button>
    </div>
  </div>
</template>

<style scoped>
.segment-container {
  min-height: 100vh;
  position: relative;
  z-index: 1;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(26, 26, 46, 0.9);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(184, 134, 11, 0.15);
}

.header-left {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.back-nav {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  letter-spacing: 1px;
  padding: 4px 10px;
  border-radius: 4px;
  transition: all 0.3s ease;
}

.back-nav:hover {
  color: #b8860b;
  background: rgba(184, 134, 11, 0.08);
}

.logo {
  font-size: 22px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 3px;
}

.logo-sub {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 2px;
}

.main-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.info-card {
  padding: 24px;
  margin-bottom: 24px;
}

.meta {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.4);
}

.player-section {
  display: grid;
  gap: 24px;
  margin-bottom: 24px;
}

.audio-player, .video-player {
  padding: 24px;
}

.vocal-player {
  padding: 24px;
  background: rgba(184, 134, 11, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
}

.vocal-player h3 {
  margin-bottom: 12px;
  color: #b8860b;
}

.accompaniment-player {
  padding: 24px;
  background: rgba(58, 90, 120, 0.05);
  border: 1px solid rgba(58, 90, 120, 0.2);
}

.accompaniment-player h3 {
  margin-bottom: 12px;
  color: #7a9ab8;
}

.audio-player h3, .video-player h3 {
  margin-bottom: 12px;
}

.video-element {
  width: 100%;
  max-height: 480px;
  margin-top: 12px;
  border-radius: 8px;
  background: #000;
}

.audio-element {
  width: 100%;
  margin-top: 12px;
}

.actions {
  margin-bottom: 24px;
}

.lyrics-section {
  padding: 24px;
  margin-bottom: 24px;
}

.lyrics-section h3 {
  margin-bottom: 16px;
}

.lyrics-content {
  white-space: pre-wrap;
  line-height: 1.8;
  color: rgba(255, 255, 255, 0.7);
  font-size: 15px;
  max-height: 200px;
  overflow-y: auto;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
}

.slices-section h3 {
  margin-bottom: 16px;
}

.slices-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.slices-header h3 {
  margin: 0;
}

.chenzi-hint {
  padding: 16px 24px;
  margin-bottom: 16px;
  background: rgba(184, 134, 11, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
}

.chenzi-hint h4 {
  margin: 0 0 12px 0;
  color: #b8860b;
  font-size: 14px;
}

.chenzi-mapping {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.mapping-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.mapping-item .digit {
  font-size: 16px;
  font-weight: 600;
  color: #7a9ab8;
}

.mapping-item .chenzi {
  font-size: 20px;
  font-weight: 700;
  color: #b8860b;
}

.slice-audio {
  border-radius: 4px;
}

.slice-lyrics {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #2c3e50;
  font-size: 14px;
}

.slice-lyrics-animated {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  align-items: center;
}

.slice-lyrics-animated span {
  color: #999;
  font-size: 14px;
  transition: all 0.2s;
}

.slice-lyrics-animated .lyrics-highlighted {
  color: #2c3e50;
  font-weight: 700;
  font-size: 16px;
}

.slice-chenzi {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #b8860b;
  font-size: 14px;
  font-weight: 500;
}

.slice-chenzi-animated {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}

.slice-chenzi-animated span {
  color: #999;
  font-size: 14px;
  transition: all 0.2s;
}

.slice-chenzi-animated .chenzi-highlighted {
  color: #b8860b;
  font-weight: 700;
  font-size: 16px;
}

.slice-chenzi-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.play-chenzi-btn {
  flex-shrink: 0;
  padding: 2px 8px;
}

/* 歌词编辑 */
.lyrics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.lyrics-header h3 {
  margin: 0;
}

.lyrics-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.lyrics-edit {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.preview-lyrics {
  max-height: 150px;
  overflow-y: auto;
}

/* 切片行内编辑 */
.slice-edit-btn {
  padding: 0;
  margin-top: 4px;
}

.slice-edit-input {
  margin-bottom: 4px;
}

.slice-edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 4px;
}

/* 音高可视化 */
.pitch-overview {
  padding: 16px 24px;
  margin-bottom: 16px;
}

.pitch-overview h4 {
  margin: 0 0 12px 0;
  color: #b8860b;
  font-size: 14px;
}

.pitch-chart {
  overflow-x: auto;
  overflow-y: hidden;
}

.pitch-sparkline {
  line-height: 1;
}

.pitch-sparkline-empty {
  color: #ccc;
  text-align: center;
  padding: 8px 0;
}

.pitch-display {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.pitch-lyrics {
  font-size: 12px;
  color: #2c3e50;
  line-height: 1.4;
  padding: 4px 0;
}

.pitch-chenzi-groups {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.chenzi-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 4px;
  border: 1px solid rgba(184, 134, 11, 0.1);
}

.group-notes {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  font-family: monospace;
  letter-spacing: 2px;
}

.group-chenzis {
  font-size: 13px;
  color: #b8860b;
  font-weight: 500;
  letter-spacing: 1px;
}

.audio-mode-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border: 1px solid rgba(184, 134, 11, 0.1);
}

.audio-mode-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: rgba(255, 255, 255, 0.4);
}

/* 播放器卡片头部 */
.player-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.player-card-header h3 {
  margin: 0;
}

.player-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 切片音频容器 */
.slice-audio-wrapper {
  display: flex;
  align-items: center;
  gap: 4px;
}

.slice-menu-btn {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
}

/* 浮动衬字参考面板 */
.chenzi-panel-wrapper {
  position: fixed;
  z-index: 1000;
}

.chenzi-panel-toggle {
  width: 48px;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.chenzi-floating-panel {
  position: absolute;
  bottom: 60px;
  right: 0;
  width: 280px;
  max-height: 500px;
  background: rgba(26, 26, 46, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(184, 134, 11, 0.3);
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, rgba(184, 134, 11, 0.1), rgba(58, 90, 120, 0.1));
  border-bottom: 1px solid rgba(184, 134, 11, 0.2);
  cursor: move;
  user-select: none;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #b8860b;
  letter-spacing: 2px;
}

.panel-body {
  padding: 12px;
  max-height: 420px;
  overflow-y: auto;
}

.guide-item {
  padding: 10px 12px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  border-left: 3px solid #b8860b;
}

.guide-item:last-child {
  margin-bottom: 0;
}

.guide-char-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-bottom: 4px;
}

.guide-char {
  font-size: 20px;
  font-weight: 700;
  color: #b8860b;
}

.guide-pinyin {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.4);
}

.guide-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 2px;
}

.guide-keywords {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.4;
}

/* 面板动画 */
.panel-fade-enter-active,
.panel-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.panel-fade-enter-from,
.panel-fade-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 音高火花线可点击 */
.pitch-sparkline-clickable {
  cursor: pointer;
  transition: opacity 0.2s;
}

.pitch-sparkline-clickable:hover {
  opacity: 0.7;
}

/* 音高放大弹窗 */
.zoom-dialog :deep(.el-dialog) {
  background: rgba(26, 26, 46, 0.97);
  border: 1px solid rgba(184, 134, 11, 0.3);
}

.zoom-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(184, 134, 11, 0.2);
}

.zoom-dialog :deep(.el-dialog__title) {
  color: #b8860b;
  letter-spacing: 2px;
}

.zoom-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.zoom-info {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.zoom-time {
  color: #b8860b;
  font-weight: 600;
}

.zoom-progress-time {
  color: #b8860b;
  font-weight: 700;
  font-size: 14px;
}

.zoom-chart {
  overflow-x: auto;
  border: 1px solid rgba(184, 134, 11, 0.15);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
  padding: 8px;
}

.zoom-lyrics-animated {
  font-size: 18px;
  color: #999;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px 16px;
  border-radius: 6px;
  letter-spacing: 3px;
  line-height: 1.6;
  text-align: center;
}

.zoom-lyrics-animated .char-highlighted {
  color: #b8860b;
  font-weight: 600;
}

.zoom-chenzi-animated {
  background: rgba(255, 255, 255, 0.9);
  padding: 12px 16px;
  border-radius: 6px;
  text-align: center;
}

.zoom-notation-row {
  margin-bottom: 8px;
  letter-spacing: 3px;
}

.zoom-notation-row .notation-char {
  display: inline-block;
  font-size: 14px;
  color: #999;
  margin: 0 4px;
  transition: all 0.2s;
}

.zoom-notation-row .char-highlighted {
  color: #3a5a78;
  font-weight: 600;
}

.zoom-chenzi-row {
  letter-spacing: 4px;
}

.zoom-chenzi-row .chenzi-char {
  display: inline-block;
  font-size: 18px;
  color: #999;
  margin: 0 4px;
  transition: all 0.2s;
}

.zoom-chenzi-row .char-highlighted {
  color: #b8860b;
  font-weight: 700;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 8px;
  border-top: 1px solid rgba(184, 134, 11, 0.15);
}

.speed-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-left: 8px;
}

</style>
