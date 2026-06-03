<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getSegmentDetail, sliceAudio, extractLyrics, separateAudio as separateAudioApi, smartSlice as smartSliceApi, updateLyrics, updateSliceLyrics } from '@/api/segments'
import { extractAudio } from '@/api/upload'
import { getMapping } from '@/api/chenzi'
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

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning',
  }).then(() => {
    localStorage.removeItem('token')
    router.push('/login')
  }).catch(() => {})
}

onMounted(() => {
  fetchDetail()
})
</script>

<template>
  <div class="segment-container">
    <div class="ink-bg"></div>
    
    <!-- 顶部导航 -->
    <header class="header dreamy-card">
      <div class="header-left">
        <span class="logo">🎭 戏曲 AI 助教</span>
      </div>
      <div class="header-right">
        <el-button class="dreamy-btn" @click="router.push(`/works/${segment?.work_id}/segments`)">唱段列表</el-button>
        <el-button class="dreamy-btn" @click="router.push('/works')">作品列表</el-button>
        <el-button class="dreamy-btn" @click="router.push('/upload')">上传</el-button>
        <el-button class="dreamy-btn" @click="handleLogout">退出</el-button>
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
          <h3>视频播放</h3>
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
          <h3>原始音频</h3>
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
          <h3>🎤 纯人声（跟着哼唱）</h3>
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
          <h3>🎵 纯伴奏</h3>
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
          <el-button v-if="fullLyrics || segment.lyrics" size="small" type="primary" text @click="startEditFullLyrics">编辑</el-button>
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
          </el-button-group>
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
          <el-table-column label="音频" width="200">
            <template #default="{ row }">
              <audio
                v-if="row.audio_url"
                :src="row.audio_url"
                controls
                style="width: 100%; height: 32px"
                class="slice-audio"
              />
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
                <div v-if="displayMode === 'lyrics'" class="slice-lyrics">{{ row.lyrics || '-' }}</div>
                <div v-else class="slice-chenzi">{{ row.chenzi_lyrics || '-' }}</div>
                <el-button v-if="displayMode === 'lyrics' && row.lyrics" size="small" text type="primary" class="slice-edit-btn" @click="startEditSlice(row)">编辑</el-button>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="commands" label="指令" />
        </el-table>
      </div>
    </main>
  </div>
</template>

<style scoped>
.segment-container {
  min-height: 100vh;
  position: relative;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 32px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  background: linear-gradient(135deg, #2b6cb0 0%, #d69e2e 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
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
  color: #718096;
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
  background: rgba(254, 243, 199, 0.3);
  border: 1px solid rgba(214, 158, 46, 0.3);
}

.vocal-player h3 {
  margin-bottom: 12px;
  color: #d69e2e;
}

.accompaniment-player {
  padding: 24px;
  background: rgba(199, 210, 254, 0.3);
  border: 1px solid rgba(43, 108, 176, 0.3);
}

.accompaniment-player h3 {
  margin-bottom: 12px;
  color: #2b6cb0;
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
  color: #4a5568;
  font-size: 15px;
  max-height: 200px;
  overflow-y: auto;
  padding: 12px;
  background: rgba(247, 250, 252, 0.5);
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
  background: rgba(254, 243, 199, 0.3);
  border: 1px solid rgba(214, 158, 46, 0.3);
}

.chenzi-hint h4 {
  margin: 0 0 12px 0;
  color: #d69e2e;
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
  color: #2b6cb0;
}

.mapping-item .chenzi {
  font-size: 20px;
  font-weight: 700;
  color: #d69e2e;
}

.slice-audio {
  border-radius: 4px;
}

.slice-lyrics {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #4a5568;
  font-size: 14px;
}

.slice-chenzi {
  white-space: pre-wrap;
  line-height: 1.5;
  color: #d69e2e;
  font-size: 14px;
  font-weight: 500;
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

.loading-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: #718096;
}
</style>
