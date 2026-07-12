<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import {
  generateMusic, getMusicHistory, deleteMusic, updateMusic,
  getAlbums, createAlbum, deleteAlbum, uploadReferenceAudio,
  getWorksForMusic, sendToSegment,
} from '@/api/music'
import type { MusicGeneration, MusicAlbum, WorkOption } from '@/api/music'
import MusicPlayer from '@/components/MusicPlayer.vue'

const router = useRouter()
const route = useRoute()

type Mode = 'simple' | 'advanced' | 'bgm'
type SidebarTab = 'workspace' | 'albums'

const mode = ref<Mode>('simple')
const sidebarTab = ref<SidebarTab>('workspace')

const generating = ref(false)
const tracks = ref<MusicGeneration[]>([])
const albums = ref<MusicAlbum[]>([])
const currentTrack = ref<MusicGeneration | null>(null)

const simpleForm = reactive({
  lyrics: '',
  style: '流行',
})

const advancedForm = reactive({
  title: '',
  lyrics: '',
  style: '流行',
  voiceGender: '',
  duration: 30,
})

const bgmForm = reactive({
  referenceUrl: '',
  referenceName: '',
  duration: 30,
  style: '流行',
})

const styles = ['流行', '古风', '戏曲', '民谣', '摇滚', '电子', 'R&B', '自定义']
const genderOptions = ['男声', '女声']

const showNewAlbum = ref(false)
const newAlbumName = ref('')
const uploadingRef = ref(false)

const showSendDialog = ref(false)
const sendMode = ref<'new' | 'existing'>('new')
const newWorkName = ref('')
const selectedWorkId = ref<number | null>(null)
const works = ref<WorkOption[]>([])
const sending = ref(false)

const inspirationKeywords = [
  '春风', '月夜', '思乡', '离别', '山水', '江湖',
  '花开', '烟雨', '归途', '故人', '长亭', '孤舟',
]

const hasPlayer = computed(() => !!currentTrack.value)

const fetchTracks = async () => {
  try {
    const { data } = await getMusicHistory()
    tracks.value = data
  } catch (e) {
    console.error('获取曲目失败', e)
  }
}

const fetchAlbums = async () => {
  try {
    const { data } = await getAlbums()
    albums.value = data
  } catch (e) {
    console.error('获取专辑失败', e)
  }
}

const handleGenerate = async () => {
  const lyrics = mode.value === 'simple' ? simpleForm.lyrics : advancedForm.lyrics
  if (!lyrics.trim()) {
    ElMessage.warning('请输入歌词')
    return
  }

  generating.value = true
  try {
    const payload: any = {
      lyrics,
      style: mode.value === 'simple' ? simpleForm.style : advancedForm.style,
    }

    if (mode.value === 'advanced') {
      if (advancedForm.title) payload.title = advancedForm.title
      if (advancedForm.voiceGender) payload.voice_gender = advancedForm.voiceGender
      payload.duration = advancedForm.duration
    }

    if (mode.value === 'bgm') {
      payload.lyrics = bgmForm.style || '纯音乐'
      payload.duration = bgmForm.duration
      if (bgmForm.referenceUrl) {
        payload.reference_audio_url = bgmForm.referenceUrl
      }
    }

    const { data } = await generateMusic(payload)
    currentTrack.value = data
    ElMessage.success('音乐生成成功')
    await fetchTracks()
  } catch (e: any) {
    const msg = e?.response?.data?.detail || '生成失败'
    if (msg.includes('illegal') || msg.includes('内容')) {
      ElMessage.error('歌词内容不符合规范，请修改后重试')
    } else {
      ElMessage.error(msg)
    }
  } finally {
    generating.value = false
  }
}

const playTrack = (track: MusicGeneration) => {
  currentTrack.value = track
}

const handleDeleteTrack = async (track: MusicGeneration) => {
  try {
    await ElMessageBox.confirm('确定要删除这首曲目吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteMusic(track.id)
    ElMessage.success('删除成功')
    if (currentTrack.value?.id === track.id) {
      currentTrack.value = null
    }
    await fetchTracks()
  } catch (e) {}
}

const handleRenameTrack = async (track: MusicGeneration) => {
  try {
    const { value } = await ElMessageBox.prompt('请输入曲目名称', '重命名', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputValue: track.title || '',
    })
    await updateMusic(track.id, { title: value })
    track.title = value
    if (currentTrack.value?.id === track.id) {
      currentTrack.value = { ...track }
    }
  } catch (e) {}
}

const handleCreateAlbum = async () => {
  if (!newAlbumName.value.trim()) return
  try {
    await createAlbum({ name: newAlbumName.value })
    newAlbumName.value = ''
    showNewAlbum.value = false
    ElMessage.success('专辑创建成功')
    await fetchAlbums()
  } catch (e) {
    ElMessage.error('创建失败')
  }
}

const handleDeleteAlbum = async (album: MusicAlbum) => {
  try {
    await ElMessageBox.confirm(`确定要删除专辑"${album.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteAlbum(album.id)
    ElMessage.success('删除成功')
    await fetchAlbums()
  } catch (e) {}
}

const handleUploadReference = async (e: Event) => {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  uploadingRef.value = true
  try {
    const { data } = await uploadReferenceAudio(file)
    bgmForm.referenceUrl = data.url
    bgmForm.referenceName = file.name
    ElMessage.success('参考音频上传成功')
  } catch (e) {
    ElMessage.error('上传失败')
  } finally {
    uploadingRef.value = false
  }
}

const handleRemix = (track: MusicGeneration) => {
  mode.value = 'advanced'
  advancedForm.lyrics = track.lyrics
  advancedForm.style = track.style
  advancedForm.title = track.title
  advancedForm.voiceGender = track.voice_gender
  advancedForm.duration = track.duration
}

const useInspiration = (keyword: string) => {
  if (mode.value === 'simple') {
    simpleForm.lyrics += (simpleForm.lyrics ? '\n' : '') + keyword
  } else {
    advancedForm.lyrics += (advancedForm.lyrics ? '\n' : '') + keyword
  }
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

const sendToAnalysis = async () => {
  sendMode.value = 'new'
  newWorkName.value = currentTrack.value?.title || ''
  selectedWorkId.value = null
  try {
    const { data } = await getWorksForMusic()
    works.value = data
  } catch (e) {
    works.value = []
  }
  showSendDialog.value = true
}

const confirmSend = async () => {
  if (!currentTrack.value) return
  const payload: { work_id?: number; work_name?: string } = {}
  if (sendMode.value === 'new') {
    if (!newWorkName.value.trim()) {
      ElMessage.warning('请输入作品名称')
      return
    }
    payload.work_name = newWorkName.value.trim()
  } else {
    if (!selectedWorkId.value) {
      ElMessage.warning('请选择一个作品')
      return
    }
    payload.work_id = selectedWorkId.value
  }

  sending.value = true
  try {
    const { data } = await sendToSegment(currentTrack.value.id, payload)
    ElMessage.success('已发送到音乐拆解')
    showSendDialog.value = false
    router.push(`/works/${data.work_id}/segments/${data.segment_id}`)
  } catch (e: any) {
    ElMessage.error(e?.response?.data?.detail || '发送失败')
  } finally {
    sending.value = false
  }
}

onMounted(() => {
  fetchTracks()
  fetchAlbums()

  const lyrics = route.query.lyrics as string
  const style = route.query.style as string
  const refAudio = route.query.reference_audio as string
  const queryMode = route.query.mode as string

  if (lyrics) {
    simpleForm.lyrics = lyrics
    advancedForm.lyrics = lyrics
  }
  if (style) {
    simpleForm.style = style
    advancedForm.style = style
  }
  if (refAudio) {
    bgmForm.referenceUrl = refAudio
    bgmForm.referenceName = '来自音乐拆解'
    mode.value = 'bgm'
  }
  if (queryMode === 'bgm') {
    mode.value = 'bgm'
  }
})
</script>

<template>
  <div class="music-page">
    <!-- 顶栏 -->
    <header class="top-bar">
      <div class="top-left">
        <span class="logo" @click="router.push('/')">影子戏</span>
        <span class="logo-sub">音乐生成</span>
      </div>
      <div class="mode-tabs">
        <button :class="['mode-tab', { active: mode === 'simple' }]" @click="mode = 'simple'">简易</button>
        <button :class="['mode-tab', { active: mode === 'advanced' }]" @click="mode = 'advanced'">自定义</button>
        <button :class="['mode-tab', { active: mode === 'bgm' }]" @click="mode = 'bgm'">配乐</button>
      </div>
      <div class="top-right">
        <button class="back-btn" @click="router.push('/')">← 返回</button>
      </div>
    </header>

    <div class="content-area">
      <!-- 左侧边栏 -->
      <aside class="sidebar">
        <div class="sidebar-tabs">
          <button :class="['sidebar-tab', { active: sidebarTab === 'workspace' }]" @click="sidebarTab = 'workspace'">
            工作区
          </button>
          <button :class="['sidebar-tab', { active: sidebarTab === 'albums' }]" @click="sidebarTab = 'albums'">
            专辑
          </button>
        </div>

        <div class="sidebar-content">
          <div v-if="sidebarTab === 'workspace'" class="track-list">
            <div v-if="tracks.length === 0" class="sidebar-empty">
              还没有曲目，快去创作吧
            </div>
            <div
              v-for="track in tracks"
              :key="track.id"
              :class="['track-item', { active: currentTrack?.id === track.id }]"
              @click="playTrack(track)"
            >
              <div class="track-item-cover">
                <img v-if="track.cover_url" :src="track.cover_url" alt="" />
                <span v-else>♪</span>
              </div>
              <div class="track-item-info">
                <div class="track-item-title">{{ track.title || '未命名' }}</div>
                <div class="track-item-meta">{{ track.style }} · {{ formatDate(track.created_at) }}</div>
              </div>
              <div class="track-item-actions" @click.stop>
                <button class="icon-btn" title="重命名" @click="handleRenameTrack(track)">✎</button>
                <button class="icon-btn delete" title="删除" @click="handleDeleteTrack(track)">×</button>
              </div>
            </div>
          </div>

          <div v-if="sidebarTab === 'albums'" class="album-list">
            <button class="new-album-btn" @click="showNewAlbum = !showNewAlbum">+ 新建专辑</button>
            <div v-if="showNewAlbum" class="new-album-form">
              <input v-model="newAlbumName" placeholder="专辑名称" @keyup.enter="handleCreateAlbum" />
              <button @click="handleCreateAlbum">创建</button>
            </div>
            <div v-if="albums.length === 0 && !showNewAlbum" class="sidebar-empty">
              还没有专辑
            </div>
            <div v-for="album in albums" :key="album.id" class="album-item">
              <div class="album-item-cover">
                <img v-if="album.cover_url" :src="album.cover_url" alt="" />
                <span v-else>♫</span>
              </div>
              <div class="album-item-info">
                <div class="album-item-name">{{ album.name }}</div>
                <div class="album-item-date">{{ formatDate(album.created_at) }}</div>
              </div>
              <button class="icon-btn delete" @click="handleDeleteAlbum(album)">×</button>
            </div>
          </div>
        </div>
      </aside>

      <!-- 中间创作区 -->
      <main class="creation-area">
        <!-- 简易模式 -->
        <div v-if="mode === 'simple'" class="creation-panel">
          <div class="panel-header">
            <h2>简易创作</h2>
            <p class="panel-desc">输入歌词，选择风格，一键生成</p>
          </div>
          <div class="form-group">
            <label>歌词</label>
            <textarea
              v-model="simpleForm.lyrics"
              placeholder="在这里输入你的歌词..."
              class="lyrics-input"
              rows="8"
            ></textarea>
          </div>
          <div class="form-group">
            <label>风格</label>
            <div class="style-tags">
              <button
                v-for="s in styles"
                :key="s"
                :class="['style-tag', { active: simpleForm.style === s }]"
                @click="simpleForm.style = s"
              >{{ s }}</button>
            </div>
          </div>
          <button class="generate-btn" :disabled="generating" @click="handleGenerate">
            <span v-if="generating" class="loading-icon">◌</span>
            {{ generating ? '生成中...' : '生成音乐' }}
          </button>
        </div>

        <!-- 自定义模式 -->
        <div v-if="mode === 'advanced'" class="creation-panel">
          <div class="panel-header">
            <h2>自定义创作</h2>
            <p class="panel-desc">精细控制每个参数</p>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label>曲目名称</label>
              <input v-model="advancedForm.title" placeholder="给你的作品取个名字" class="text-input" />
            </div>
            <div class="form-group">
              <label>声音性别</label>
              <div class="gender-select">
                <button
                  v-for="g in genderOptions"
                  :key="g"
                  :class="['gender-btn', { active: advancedForm.voiceGender === g }]"
                  @click="advancedForm.voiceGender = advancedForm.voiceGender === g ? '' : g"
                >{{ g }}</button>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>歌词</label>
            <textarea
              v-model="advancedForm.lyrics"
              placeholder="在这里输入你的歌词..."
              class="lyrics-input"
              rows="6"
            ></textarea>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label>风格</label>
              <div class="style-tags">
                <button
                  v-for="s in styles"
                  :key="s"
                  :class="['style-tag', { active: advancedForm.style === s }]"
                  @click="advancedForm.style = s"
                >{{ s }}</button>
              </div>
            </div>
            <div class="form-group" style="width: 120px">
              <label>时长 (秒)</label>
              <input v-model.number="advancedForm.duration" type="number" min="10" max="120" class="text-input" />
            </div>
          </div>
          <button class="generate-btn" :disabled="generating" @click="handleGenerate">
            <span v-if="generating" class="loading-icon">◌</span>
            {{ generating ? '生成中...' : '生成音乐' }}
          </button>
        </div>

        <!-- 配乐模式 -->
        <div v-if="mode === 'bgm'" class="creation-panel">
          <div class="panel-header">
            <h2>配乐模式</h2>
            <p class="panel-desc">上传参考音频，生成配套背景音乐</p>
          </div>
          <div class="form-group">
            <label>参考音频</label>
            <div class="upload-area">
              <input type="file" accept="audio/*" @change="handleUploadReference" id="ref-upload" style="display: none" />
              <label for="ref-upload" class="upload-btn">
                <span v-if="uploadingRef">上传中...</span>
                <span v-else-if="bgmForm.referenceName">{{ bgmForm.referenceName }}</span>
                <span v-else>点击上传参考音频</span>
              </label>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group flex-1">
              <label>风格描述</label>
              <div class="style-tags">
                <button
                  v-for="s in styles"
                  :key="s"
                  :class="['style-tag', { active: bgmForm.style === s }]"
                  @click="bgmForm.style = s"
                >{{ s }}</button>
              </div>
            </div>
            <div class="form-group" style="width: 120px">
              <label>时长 (秒)</label>
              <input v-model.number="bgmForm.duration" type="number" min="10" max="120" class="text-input" />
            </div>
          </div>
          <button class="generate-btn" :disabled="generating" @click="handleGenerate">
            <span v-if="generating" class="loading-icon">◌</span>
            {{ generating ? '生成中...' : '生成配乐' }}
          </button>
        </div>

        <!-- 生成结果 -->
        <div v-if="currentTrack" class="result-panel">
          <div class="result-cover">
            <img v-if="currentTrack.cover_url" :src="currentTrack.cover_url" alt="" />
            <div v-else class="result-cover-placeholder">
              <span>♪</span>
            </div>
          </div>
          <div class="result-info">
            <h3>{{ currentTrack.title || '未命名曲目' }}</h3>
            <div class="result-meta">
              <span class="result-style">{{ currentTrack.style }}</span>
              <span class="result-time">{{ formatDate(currentTrack.created_at) }}</span>
            </div>
            <div class="result-lyrics">
              <div class="lyrics-label">歌词</div>
              <div class="lyrics-text">{{ currentTrack.lyrics }}</div>
            </div>
            <div class="result-actions">
              <button class="send-btn" @click="sendToAnalysis">发送到音乐拆解</button>
            </div>
          </div>
        </div>
      </main>

      <!-- 右侧灵感面板 -->
      <aside class="inspiration-panel">
        <h3 class="insp-title">灵感</h3>
        <div class="insp-keywords">
          <button
            v-for="kw in inspirationKeywords"
            :key="kw"
            class="insp-keyword"
            @click="useInspiration(kw)"
          >{{ kw }}</button>
        </div>
        <div class="insp-divider"></div>
        <h3 class="insp-title">推荐风格</h3>
        <div class="insp-styles">
          <div v-for="s in ['古风戏韵', '电子国潮', '民谣叙事', '摇滚燃曲']" :key="s" class="insp-style-card">
            <div class="insp-style-name">{{ s }}</div>
            <button class="insp-use-btn" @click="mode === 'simple' ? simpleForm.style = s.slice(0, 2) : advancedForm.style = s.slice(0, 2)">使用</button>
          </div>
        </div>
      </aside>
    </div>

    <!-- 发送到音乐拆解弹窗 -->
    <div v-if="showSendDialog" class="send-dialog-overlay" @click.self="showSendDialog = false">
      <div class="send-dialog">
        <h3>发送到音乐拆解</h3>
        <div class="send-mode-tabs">
          <button :class="['send-mode-tab', { active: sendMode === 'new' }]" @click="sendMode = 'new'">创建新作品</button>
          <button :class="['send-mode-tab', { active: sendMode === 'existing' }]" @click="sendMode = 'existing'">选择已有作品</button>
        </div>
        <div v-if="sendMode === 'new'" class="send-form">
          <label>作品名称</label>
          <input v-model="newWorkName" placeholder="输入作品名称" class="send-input" />
        </div>
        <div v-else class="send-form">
          <label>选择作品</label>
          <select v-model="selectedWorkId" class="send-select">
            <option :value="null" disabled>请选择作品</option>
            <option v-for="w in works" :key="w.id" :value="w.id">{{ w.name }} ({{ w.category || '未分类' }})</option>
          </select>
        </div>
        <div class="send-dialog-footer">
          <button class="send-cancel" @click="showSendDialog = false">取消</button>
          <button class="send-confirm" :disabled="sending" @click="confirmSend">
            {{ sending ? '发送中...' : '确认发送' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 底部播放器 -->
    <MusicPlayer :track="currentTrack" @remix="handleRemix" />
  </div>
</template>

<style scoped>
.music-page {
  height: 100vh;
  background: rgba(10, 10, 10, 0.7);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #fff;
  position: relative;
  z-index: 1;
}

/* 顶栏 */
.top-bar {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  background: rgba(15, 15, 15, 0.6);
  border-bottom: 1px solid rgba(26, 26, 26, 0.5);
  flex-shrink: 0;
}

.top-left {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.logo {
  font-size: 16px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b, #daa520);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  cursor: pointer;
  letter-spacing: 2px;
}

.logo-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  letter-spacing: 1px;
}

.mode-tabs {
  display: flex;
  gap: 2px;
  background: #1a1a1a;
  border-radius: 6px;
  padding: 2px;
}

.mode-tab {
  padding: 6px 20px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
}

.mode-tab.active {
  background: #b8860b;
  color: #000;
  font-weight: 600;
}

.mode-tab:hover:not(.active) {
  color: #fff;
}

.back-btn {
  padding: 4px 12px;
  border: 1px solid #333;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.back-btn:hover {
  border-color: #b8860b;
  color: #b8860b;
}

/* 内容区域 */
.content-area {
  flex: 1;
  display: flex;
  overflow: hidden;
}

/* 左侧边栏 */
.sidebar {
  width: 240px;
  background: rgba(15, 15, 15, 0.6);
  border-right: 1px solid rgba(26, 26, 26, 0.5);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.sidebar-tabs {
  display: flex;
  border-bottom: 1px solid #1a1a1a;
}

.sidebar-tab {
  flex: 1;
  padding: 10px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}

.sidebar-tab.active {
  color: #b8860b;
  border-bottom-color: #b8860b;
}

.sidebar-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.sidebar-content::-webkit-scrollbar {
  width: 4px;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

.sidebar-empty {
  text-align: center;
  padding: 40px 16px;
  color: rgba(255, 255, 255, 0.2);
  font-size: 13px;
}

.track-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 2px;
}

.track-item:hover {
  background: #1a1a1a;
}

.track-item.active {
  background: rgba(184, 134, 11, 0.1);
  border: 1px solid rgba(184, 134, 11, 0.2);
}

.track-item-cover {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  overflow: hidden;
  font-size: 16px;
  color: #b8860b;
}

.track-item-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-item-info {
  flex: 1;
  min-width: 0;
}

.track-item-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.track-item-meta {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 2px;
}

.track-item-actions {
  display: flex;
  gap: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.track-item:hover .track-item-actions {
  opacity: 1;
}

.icon-btn {
  width: 24px;
  height: 24px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: #333;
  color: #fff;
}

.icon-btn.delete:hover {
  color: #e74c3c;
}

.new-album-btn {
  width: 100%;
  padding: 8px;
  border: 1px dashed #333;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  cursor: pointer;
  margin-bottom: 8px;
  transition: all 0.2s;
}

.new-album-btn:hover {
  border-color: #b8860b;
  color: #b8860b;
}

.new-album-form {
  display: flex;
  gap: 6px;
  margin-bottom: 8px;
}

.new-album-form input {
  flex: 1;
  padding: 6px 10px;
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
  outline: none;
}

.new-album-form input:focus {
  border-color: #b8860b;
}

.new-album-form button {
  padding: 6px 12px;
  background: #b8860b;
  border: none;
  border-radius: 4px;
  color: #000;
  font-size: 12px;
  cursor: pointer;
  font-weight: 600;
}

.album-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border-radius: 6px;
  margin-bottom: 2px;
  transition: all 0.2s;
}

.album-item:hover {
  background: #1a1a1a;
}

.album-item-cover {
  width: 36px;
  height: 36px;
  border-radius: 4px;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 16px;
  color: #b8860b;
  overflow: hidden;
}

.album-item-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.album-item-info {
  flex: 1;
  min-width: 0;
}

.album-item-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.8);
}

.album-item-date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 2px;
}

/* 中间创作区 */
.creation-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px;
  padding-bottom: 96px;
}

.creation-area::-webkit-scrollbar {
  width: 6px;
}

.creation-area::-webkit-scrollbar-thumb {
  background: #222;
  border-radius: 3px;
}

.creation-panel {
  max-width: 640px;
  margin: 0 auto 32px;
}

.panel-header {
  margin-bottom: 24px;
}

.panel-header h2 {
  font-size: 22px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 1px;
}

.panel-desc {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.3);
  margin-top: 4px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
  font-weight: 500;
}

.form-row {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.flex-1 {
  flex: 1;
}

.lyrics-input,
.text-input {
  width: 100%;
  padding: 12px 16px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 8px;
  color: #fff;
  font-size: 14px;
  line-height: 1.6;
  resize: vertical;
  outline: none;
  font-family: inherit;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.lyrics-input:focus,
.text-input:focus {
  border-color: #b8860b;
}

.lyrics-input::placeholder,
.text-input::placeholder {
  color: rgba(255, 255, 255, 0.2);
}

.style-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.style-tag {
  padding: 6px 16px;
  border: 1px solid #333;
  border-radius: 20px;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.style-tag:hover {
  border-color: rgba(184, 134, 11, 0.5);
  color: rgba(255, 255, 255, 0.8);
}

.style-tag.active {
  background: rgba(184, 134, 11, 0.15);
  border-color: #b8860b;
  color: #b8860b;
}

.gender-select {
  display: flex;
  gap: 8px;
}

.gender-btn {
  padding: 6px 20px;
  border: 1px solid #333;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.gender-btn:hover {
  border-color: rgba(184, 134, 11, 0.5);
}

.gender-btn.active {
  background: rgba(184, 134, 11, 0.15);
  border-color: #b8860b;
  color: #b8860b;
}

.generate-btn {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #b8860b, #daa520);
  border: none;
  border-radius: 8px;
  color: #000;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: 2px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(184, 134, 11, 0.3);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-icon {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.upload-area {
  margin-top: 4px;
}

.upload-btn {
  display: block;
  padding: 24px;
  border: 1px dashed #333;
  border-radius: 8px;
  text-align: center;
  color: rgba(255, 255, 255, 0.4);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-btn:hover {
  border-color: #b8860b;
  color: #b8860b;
}

/* 结果面板 */
.result-panel {
  max-width: 640px;
  margin: 0 auto;
  display: flex;
  gap: 24px;
  padding: 24px;
  background: #111;
  border: 1px solid #222;
  border-radius: 12px;
}

.result-cover {
  width: 120px;
  height: 120px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
}

.result-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-cover-placeholder {
  width: 100%;
  height: 100%;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: #b8860b;
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-info h3 {
  font-size: 18px;
  color: #fff;
  margin-bottom: 8px;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.result-style {
  padding: 2px 10px;
  background: rgba(184, 134, 11, 0.15);
  border: 1px solid rgba(184, 134, 11, 0.3);
  border-radius: 4px;
  color: #b8860b;
  font-size: 12px;
}

.result-time {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
}

.result-lyrics {
  padding: 12px;
  background: rgba(10, 10, 10, 0.6);
  border-radius: 6px;
  max-height: 200px;
  overflow-y: auto;
}

.result-lyrics .lyrics-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  margin-bottom: 6px;
}

.result-lyrics .lyrics-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.8;
  white-space: pre-wrap;
}

.result-lyrics::-webkit-scrollbar {
  width: 4px;
}

.result-lyrics::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

/* 右侧灵感面板 */
.inspiration-panel {
  width: 220px;
  background: rgba(15, 15, 15, 0.6);
  border-left: 1px solid rgba(26, 26, 26, 0.5);
  padding: 20px 16px;
  flex-shrink: 0;
  overflow-y: auto;
}

.insp-title {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 500;
  margin-bottom: 12px;
  letter-spacing: 1px;
}

.insp-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.insp-keyword {
  padding: 4px 12px;
  border: 1px solid #2a2a2a;
  border-radius: 14px;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.insp-keyword:hover {
  border-color: #b8860b;
  color: #b8860b;
  background: rgba(184, 134, 11, 0.08);
}

.insp-divider {
  height: 1px;
  background: #1a1a1a;
  margin: 20px 0;
}

.insp-styles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.insp-style-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  background: #1a1a1a;
  border-radius: 6px;
  transition: all 0.2s;
}

.insp-style-card:hover {
  background: #222;
}

.insp-style-name {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
}

.insp-use-btn {
  padding: 2px 10px;
  border: 1px solid #333;
  border-radius: 4px;
  background: transparent;
  color: rgba(255, 255, 255, 0.4);
  font-size: 11px;
  cursor: pointer;
  transition: all 0.2s;
}

.insp-use-btn:hover {
  border-color: #b8860b;
  color: #b8860b;
}

.result-actions {
  margin-top: 12px;
}

.send-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #b8860b, #daa520);
  border: none;
  border-radius: 6px;
  color: #000;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.send-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 12px rgba(184, 134, 11, 0.3);
}

.send-dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.send-dialog {
  background: #1a1a1a;
  border: 1px solid #333;
  border-radius: 12px;
  padding: 24px;
  width: 400px;
  max-width: 90vw;
}

.send-dialog h3 {
  font-size: 16px;
  color: #fff;
  margin-bottom: 16px;
}

.send-mode-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 20px;
  border: 1px solid #333;
  border-radius: 6px;
  overflow: hidden;
}

.send-mode-tab {
  flex: 1;
  padding: 8px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s;
}

.send-mode-tab.active {
  background: rgba(184, 134, 11, 0.15);
  color: #b8860b;
}

.send-form label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
}

.send-input {
  width: 100%;
  padding: 10px 12px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.send-input:focus {
  border-color: #b8860b;
}

.send-select {
  width: 100%;
  padding: 10px 12px;
  background: #111;
  border: 1px solid #333;
  border-radius: 6px;
  color: #fff;
  font-size: 14px;
  outline: none;
  box-sizing: border-box;
}

.send-select:focus {
  border-color: #b8860b;
}

.send-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 20px;
}

.send-cancel {
  padding: 8px 16px;
  border: 1px solid #333;
  border-radius: 6px;
  background: transparent;
  color: rgba(255, 255, 255, 0.5);
  font-size: 13px;
  cursor: pointer;
}

.send-cancel:hover {
  border-color: #555;
  color: #fff;
}

.send-confirm {
  padding: 8px 20px;
  background: linear-gradient(135deg, #b8860b, #daa520);
  border: none;
  border-radius: 6px;
  color: #000;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}

.send-confirm:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>