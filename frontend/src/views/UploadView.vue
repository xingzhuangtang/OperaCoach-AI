<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { uploadVideo, uploadAudio, extractAudio } from '@/api/upload'
import { listWorks, createWork, createSegment } from '@/api/segments'
import type { OperaWork } from '@/types'

const router = useRouter()
const works = ref<OperaWork[]>([])

const videoFile = ref<{ name: string; url: string; extracting?: boolean } | null>(null)
const audioFile = ref<{ name: string; url: string } | null>(null)

const workName = ref('')
const segmentName = ref('')
const selectedWorkId = ref<number | null>(null)
const creating = ref(false)

const fetchWorks = async () => {
  const { data } = await listWorks()
  works.value = data
}

const handleVideoUpload = async (file: File) => {
  try {
    const { data } = await uploadVideo(file)
    videoFile.value = { name: file.name, url: data.video_url }
    if (!segmentName.value) {
      segmentName.value = file.name.replace(/\.[^.]+$/, '')
    }
    ElMessage.success('视频上传成功')
  } catch (e) {
    // handled
  }
  return false
}

const handleAudioUpload = async (file: File) => {
  try {
    const { data } = await uploadAudio(file)
    audioFile.value = { name: file.name, url: data.audio_url }
    if (!segmentName.value) {
      segmentName.value = file.name.replace(/\.[^.]+$/, '')
    }
    ElMessage.success('音频上传成功')
  } catch (e) {
    // handled
  }
  return false
}

const handleExtractAudio = async () => {
  if (!videoFile.value) return
  videoFile.value.extracting = true
  try {
    const { data } = await extractAudio(videoFile.value.url)
    audioFile.value = {
      name: videoFile.value.name.replace(/\.[^.]+$/, '.wav'),
      url: data.audio_url,
    }
    ElMessage.success('音频提取成功，已自动填充到音频栏')
  } catch (e) {
    // handled
  } finally {
    videoFile.value.extracting = false
  }
}

const removeVideo = () => {
  videoFile.value = null
}

const removeAudio = () => {
  audioFile.value = null
}

const handleCreateSegment = async () => {
  if (!videoFile.value && !audioFile.value) {
    ElMessage.warning('请先上传视频或音频')
    return
  }

  if (!workName.value.trim() && !selectedWorkId.value) {
    ElMessage.warning('请输入作品名称或选择已有作品')
    return
  }

  if (!segmentName.value.trim()) {
    ElMessage.warning('请输入唱段名称')
    return
  }

  creating.value = true
  try {
    let workId = selectedWorkId.value

    if (!workId && workName.value.trim()) {
      const { data: newWork } = await createWork({ name: workName.value.trim() })
      workId = newWork.id
      ElMessage.success('作品创建成功')
    }

    await createSegment({
      work_id: workId!,
      name: segmentName.value.trim(),
      video_url: videoFile.value?.url || '',
      audio_url: audioFile.value?.url || '',
    })
    ElMessage.success('唱段创建成功')
    router.push('/works')
  } catch (e) {
    // handled
  } finally {
    creating.value = false
  }
}

onMounted(() => {
  fetchWorks()
})
</script>

<template>
  <div class="upload-container">
    <header class="header">
      <div class="header-left">
        <button class="back-nav" @click="router.push('/hub')">← 返回</button>
        <span class="logo">影子戏</span>
        <span class="logo-sub">上传管理</span>
      </div>
    </header>

    <main class="main-content fade-in">
      <div class="page-header">
        <h2 class="dreamy-title">上传管理</h2>
        <div class="title-underline"></div>
      </div>

      <!-- 作品和唱段信息 -->
      <div class="info-section">
        <div class="info-row">
          <div class="info-item">
            <label class="info-label">作品名称</label>
            <div class="info-input-group">
              <el-input
                v-model="workName"
                placeholder="输入新作品名称（或选择已有作品）"
                clearable
                @input="selectedWorkId = null"
              />
              <span class="or-text">或</span>
              <el-select
                v-model="selectedWorkId"
                placeholder="选择已有作品"
                clearable
                @change="workName = ''"
              >
                <el-option v-for="work in works" :key="work.id" :label="work.name" :value="work.id" />
              </el-select>
            </div>
          </div>
          <div class="info-item">
            <label class="info-label">唱段名称</label>
            <el-input v-model="segmentName" placeholder="输入唱段名称" clearable />
          </div>
        </div>
      </div>

      <!-- 左右分栏上传区 -->
      <div class="upload-columns">
        <!-- 视频栏 -->
        <div class="upload-column">
          <div class="column-label">
            <span class="label-char">影</span>
            <span class="label-text">视频</span>
          </div>

          <div v-if="!videoFile" class="upload-slot">
            <el-upload
              drag
              action=""
              :auto-upload="false"
              :on-change="(file: any) => handleVideoUpload(file.raw)"
              accept=".mp4,.mov,.avi"
              :show-file-list="false"
              class="upload-box"
            >
              <div class="upload-content">
                <div class="upload-icon">+</div>
                <div class="upload-desc">拖拽视频到此处 或 点击上传</div>
                <div class="upload-formats">MP4 / MOV / AVI</div>
              </div>
            </el-upload>
          </div>

          <div v-else class="file-preview">
            <div class="preview-info">
              <div class="file-name">{{ videoFile.name }}</div>
              <video :src="videoFile.url" class="preview-video" preload="metadata" />
            </div>
            <div class="preview-actions">
              <el-button
                type="warning"
                size="small"
                class="dreamy-btn extract-btn"
                :loading="videoFile.extracting"
                @click="handleExtractAudio"
              >
                提取音频 →
              </el-button>
              <el-button size="small" text class="remove-btn" @click="removeVideo">移除</el-button>
            </div>
          </div>
        </div>

        <!-- 中间箭头 -->
        <div class="column-arrow">
          <div class="arrow-line"></div>
        </div>

        <!-- 音频栏 -->
        <div class="upload-column">
          <div class="column-label">
            <span class="label-char">音</span>
            <span class="label-text">音频</span>
          </div>

          <div v-if="!audioFile" class="upload-slot">
            <el-upload
              drag
              action=""
              :auto-upload="false"
              :on-change="(file: any) => handleAudioUpload(file.raw)"
              accept=".mp3,.wav,.flac"
              :show-file-list="false"
              class="upload-box"
            >
              <div class="upload-content">
                <div class="upload-icon">+</div>
                <div class="upload-desc">拖拽音频到此处 或 点击上传</div>
                <div class="upload-formats">MP3 / WAV / FLAC</div>
              </div>
            </el-upload>
          </div>

          <div v-else class="file-preview">
            <div class="preview-info">
              <div class="file-name">{{ audioFile.name }}</div>
              <audio :src="audioFile.url" controls class="preview-audio" />
            </div>
            <div class="preview-actions">
              <el-button size="small" text class="remove-btn" @click="removeAudio">移除</el-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 创建按钮 -->
      <div class="create-section">
        <el-button
          type="primary"
          class="dreamy-btn create-btn"
          :loading="creating"
          @click="handleCreateSegment"
        >
          创建唱段
        </el-button>
      </div>
    </main>
  </div>
</template>

<style scoped>
.upload-container {
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
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px;
}

.page-header {
  margin-bottom: 24px;
}

.dreamy-title {
  font-size: 28px;
  font-weight: 700;
  background: linear-gradient(135deg, #b8860b 0%, #daa520 50%, #b8860b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: 4px;
  margin-bottom: 8px;
}

.title-underline {
  width: 60px;
  height: 2px;
  background: linear-gradient(90deg, #b8860b, transparent);
}

/* 作品信息区 */
.info-section {
  margin-bottom: 28px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(184, 134, 11, 0.1);
  border-radius: 8px;
}

.info-row {
  display: flex;
  gap: 24px;
}

.info-item {
  flex: 1;
}

.info-label {
  display: block;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.info-input-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-input-group .el-input {
  flex: 1;
}

.info-input-group .el-select {
  flex: 1;
}

.or-text {
  color: rgba(255, 255, 255, 0.3);
  font-size: 12px;
}

.info-section :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(184, 134, 11, 0.2);
}

.info-section :deep(.el-input__inner) {
  color: #e0e0e0;
}

.info-section :deep(.el-input__inner::placeholder) {
  color: rgba(255, 255, 255, 0.3);
}

.info-section :deep(.el-select .el-input__wrapper) {
  background: rgba(255, 255, 255, 0.05);
}

/* 左右分栏 */
.upload-columns {
  display: flex;
  gap: 0;
  align-items: stretch;
}

.upload-column {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.column-arrow {
  width: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.arrow-line {
  width: 2px;
  height: 60%;
  min-height: 80px;
  background: linear-gradient(180deg, transparent 0%, rgba(184, 134, 11, 0.3) 50%, transparent 100%);
  position: relative;
}

.arrow-line::after {
  content: '→';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: rgba(184, 134, 11, 0.4);
  font-size: 16px;
  background: rgba(26, 26, 46, 1);
  padding: 4px;
}

.column-label {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.label-char {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(58, 90, 120, 0.2) 0%, rgba(184, 134, 11, 0.1) 100%);
  border: 1px solid rgba(184, 134, 11, 0.3);
  border-radius: 50%;
  font-size: 18px;
  color: #b8860b;
  font-weight: 700;
}

.label-text {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  letter-spacing: 2px;
}

/* 上传区域 */
.upload-slot {
  flex: 1;
}

.upload-box {
  width: 100%;
}

.upload-box :deep(.el-upload) {
  width: 100%;
}

.upload-box :deep(.el-upload-dragger) {
  width: 100%;
  padding: 0;
  background: rgba(255, 255, 255, 0.02);
  border: 2px dashed rgba(184, 134, 11, 0.2);
  border-radius: 8px;
  transition: all 0.3s ease;
  min-height: 200px;
  display: flex;
  align-items: center;
}

.upload-box :deep(.el-upload-dragger:hover) {
  border-color: rgba(184, 134, 11, 0.5);
  background: rgba(255, 255, 255, 0.04);
}

.upload-content {
  padding: 40px 24px;
  text-align: center;
  width: 100%;
}

.upload-icon {
  width: 48px;
  height: 48px;
  margin: 0 auto 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid rgba(184, 134, 11, 0.3);
  border-radius: 50%;
  font-size: 24px;
  color: rgba(184, 134, 11, 0.6);
  font-weight: 300;
}

.upload-desc {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 8px;
}

.upload-formats {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.2);
  letter-spacing: 1px;
}

/* 文件预览 */
.file-preview {
  flex: 1;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(184, 134, 11, 0.15);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.file-name {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  word-break: break-all;
}

.preview-video {
  width: 100%;
  max-height: 240px;
  border-radius: 6px;
  background: #000;
}

.preview-audio {
  width: 100%;
}

.preview-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.extract-btn {
  letter-spacing: 1px;
}

.remove-btn {
  color: rgba(255, 255, 255, 0.3);
}

.remove-btn:hover {
  color: #8b0000;
}

/* 创建按钮 */
.create-section {
  margin-top: 32px;
  text-align: center;
}

.create-btn {
  padding: 14px 48px;
  font-size: 16px;
  letter-spacing: 4px;
}
</style>
