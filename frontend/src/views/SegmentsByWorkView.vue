<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading, Plus } from '@element-plus/icons-vue'
import { listSegmentsByWork, createSegment, deleteSegment, getWorkDetail } from '@/api/segments'
import type { OperaWork, OperaSegment } from '@/types'

const route = useRoute()
const router = useRouter()

const work = ref<OperaWork | null>(null)
const segments = ref<OperaSegment[]>([])
const loading = ref(false)
const creating = ref(false)

const workId = parseInt(route.params.workId as string)

const fetchSegments = async () => {
  loading.value = true
  try {
    const [workRes, segmentsRes] = await Promise.all([
      getWorkDetail(workId),
      listSegmentsByWork(workId),
    ])
    work.value = workRes.data
    segments.value = segmentsRes.data
  } catch (e) {
    ElMessage.error('加载失败')
  } finally {
    loading.value = false
  }
}

const handleCreateSegment = async () => {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入唱段名称', '创建唱段', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
    if (!name) return
    creating.value = true
    await createSegment({ work_id: workId, name })
    ElMessage.success('创建成功')
    await fetchSegments()
  } catch (e) {
    // 用户取消
  } finally {
    creating.value = false
  }
}

const handleDeleteSegment = async (segment: OperaSegment) => {
  try {
    await ElMessageBox.confirm(`确定要删除唱段"${segment.name}"吗？`, '删除唱段', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await deleteSegment(segment.id)
    ElMessage.success('删除成功')
    await fetchSegments()
  } catch (e) {
    // 用户取消
  }
}

const handleSegmentClick = (segment: OperaSegment) => {
  router.push(`/segment/${segment.id}`)
}

const formatDuration = (seconds: number | null) => {
  if (!seconds) return '-'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

onMounted(() => {
  fetchSegments()
})
</script>

<template>
  <div class="segments-list-container">
    <div class="ink-bg"></div>

    <!-- 顶部导航 -->
    <header class="header dreamy-card">
      <div class="header-left">
        <span class="logo">&#x1f3ad; 戏曲 AI 助教</span>
      </div>
      <div class="header-right">
        <el-button class="dreamy-btn" @click="router.push('/works')">作品列表</el-button>
        <el-button class="dreamy-btn" @click="router.push('/upload')">上传</el-button>
      </div>
    </header>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>加载中...</span>
    </div>

    <!-- 主内容 -->
    <main v-else-if="work" class="main-content fade-in">
      <!-- 作品信息 -->
      <div class="info-card dreamy-card">
        <div class="info-header">
          <el-button text @click="router.push('/works')" class="back-btn">&#x2190; 返回</el-button>
          <h2 class="dreamy-title">{{ work.name }}</h2>
        </div>
        <p v-if="work.category" class="meta">类别：{{ work.category }}</p>
        <p v-if="work.description" class="meta">简介：{{ work.description }}</p>
        <p class="meta">唱段数量：{{ segments.length }}</p>
      </div>

      <!-- 操作按钮 -->
      <div class="actions">
        <el-button
          type="primary"
          class="dreamy-btn"
          :icon="Plus"
          :loading="creating"
          @click="handleCreateSegment"
        >
          创建新唱段
        </el-button>
      </div>

      <!-- 唱段列表 -->
      <div class="segments-grid">
        <el-empty v-if="segments.length === 0" description="暂无唱段，请点击'创建新唱段'添加" />

        <div
          v-for="segment in segments"
          :key="segment.id"
          class="segment-card dreamy-card"
          @click="handleSegmentClick(segment)"
        >
          <div class="segment-info">
            <h3 class="segment-name">{{ segment.name }}</h3>
            <div class="segment-meta">
              <span v-if="segment.audio_url" class="tag tag-audio">&#x1f3b5; 有音频</span>
              <span v-if="segment.video_url" class="tag tag-video">&#x1f3ac; 有视频</span>
              <span v-if="segment.is_separated" class="tag tag-separated">&#x1f3a4; 已分离</span>
              <span v-if="segment.slices?.length" class="tag tag-slices">{{ segment.slices.length }} 个切片</span>
            </div>
          </div>
          <div class="segment-actions">
            <el-button
              type="danger"
              text
              size="small"
              @click.stop="handleDeleteSegment(segment)"
            >
              删除
            </el-button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.segments-list-container {
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

.info-header {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  font-size: 14px;
  color: #4a5568;
}

.dreamy-title {
  margin: 0;
  font-size: 24px;
}

.meta {
  margin-top: 8px;
  color: #718096;
}

.actions {
  margin-bottom: 24px;
}

.segments-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.segment-card {
  padding: 20px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.segment-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.segment-info {
  flex: 1;
}

.segment-name {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.segment-meta {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 4px;
  background: rgba(247, 250, 252, 0.8);
  color: #4a5568;
}

.tag-audio {
  background: rgba(254, 243, 199, 0.5);
  color: #d69e2e;
}

.tag-video {
  background: rgba(199, 210, 254, 0.5);
  color: #2b6cb0;
}

.tag-separated {
  background: rgba(198, 246, 213, 0.5);
  color: #276749;
}

.tag-slices {
  background: rgba(237, 201, 255, 0.5);
  color: #6b46c1;
}

.segment-actions {
  margin-left: 16px;
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
