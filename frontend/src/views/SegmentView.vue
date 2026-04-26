<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import { getSegmentDetail, sliceAudio } from '@/api/segments'
import { extractAudio } from '@/api/upload'
import type { OperaSegment, SegmentSlice } from '@/types'

const route = useRoute()
const router = useRouter()

const segment = ref<OperaSegment | null>(null)
const slices = ref<SegmentSlice[]>([])
const loading = ref(false)
const slicing = ref(false)
const extracting = ref(false)

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

const handleSlice = async () => {
  slicing.value = true
  try {
    const { data } = await sliceAudio(segmentId)
    ElMessage.success(`切片成功，共 ${data.length} 个片段`)
    // 刷新详情获取切片列表
    await fetchDetail()
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
          <h3>音频播放</h3>
          <audio
            :src="segment.audio_url"
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
          type="primary"
          class="dreamy-btn"
          :loading="slicing"
          @click="handleSlice"
        >
          执行切片
        </el-button>
      </div>

      <!-- 切片列表 -->
      <div class="slices-section">
        <h3>切片列表 ({{ slices.length }})</h3>
        
        <el-empty v-if="slices.length === 0" description="暂无切片，请点击'执行切片'" />
        
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
          <el-table-column prop="lyrics" label="歌词" />
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

.slices-section h3 {
  margin-bottom: 16px;
}

.slice-audio {
  border-radius: 4px;
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
