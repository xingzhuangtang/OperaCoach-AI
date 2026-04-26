<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { uploadVideo, uploadAudio, extractAudio } from '@/api/upload'
import { listWorks, createSegment } from '@/api/segments'
import type { OperaWork } from '@/types'

const router = useRouter()
const works = ref<OperaWork[]>([])
const uploadedFiles = ref<{ name: string; url: string; type: 'video' | 'audio'; extracting?: boolean }[]>([])
const uploading = ref(false)
const segmentFormRef = ref()

// 加载已上传文件列表
const loadUploadedFiles = async () => {
  try {
    const response = await fetch('/api/v1/upload/list')
    if (response.ok) {
      const data = await response.json()
      uploadedFiles.value = data
    }
  } catch (e) {
    // 忽略错误
  }
}

const segmentForm = reactive({
  work_id: null as number | null,
  name: '',
  video_url: '',
  audio_url: '',
})
const dialogVisible = ref(false)

const segmentRules = {
  work_id: [{ required: true, message: '请选择作品', trigger: 'change' }],
  name: [{ required: true, message: '请输入唱段名称', trigger: 'blur' }],
}

const fetchWorks = async () => {
  const { data } = await listWorks()
  works.value = data
}

const handleVideoUpload = async (file: File) => {
  uploading.value = true
  try {
    const { data } = await uploadVideo(file)
    uploadedFiles.value.push({ name: file.name, url: data.video_url, type: 'video' })
    ElMessage.success('视频上传成功')
  } catch (e) {
    // 已处理
  } finally {
    uploading.value = false
  }
  return false
}

const handleAudioUpload = async (file: File) => {
  uploading.value = true
  try {
    const { data } = await uploadAudio(file)
    uploadedFiles.value.push({ name: file.name, url: data.audio_url, type: 'audio' })
    ElMessage.success('音频上传成功')
  } catch (e) {
    // 已处理
  } finally {
    uploading.value = false
  }
  return false
}

const handleExtractAudio = async (videoUrl: string, index: number) => {
  const file = uploadedFiles.value[index]
  file.extracting = true
  try {
    const { data } = await extractAudio(videoUrl)
    uploadedFiles.value.push({ name: file.name.replace(/\.[^.]+$/, '.wav'), url: data.audio_url, type: 'audio' })
    ElMessage.success('音频提取成功')
  } catch (e) {
    // 已处理
  } finally {
    file.extracting = false
  }
  // 刷新文件列表
  await loadUploadedFiles()
}

const openCreateDialog = () => {
  if (uploadedFiles.value.length === 0) {
    ElMessage.warning('请先上传文件')
    return
  }
  segmentForm.work_id = null
  segmentForm.name = ''
  segmentForm.video_url = ''
  segmentForm.audio_url = ''
  dialogVisible.value = true
}

const handleCreateSegment = async () => {
  if (!segmentFormRef.value) return
  await segmentFormRef.value.validate(async (valid: boolean) => {
    if (!valid) return
    if (!segmentForm.video_url && !segmentForm.audio_url) {
      ElMessage.warning('请至少选择一个文件')
      return
    }
    try {
      await createSegment(segmentForm)
      ElMessage.success('唱段创建成功')
      dialogVisible.value = false
      router.push('/works')
    } catch (e) {
      // 已处理
    }
  })
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
  fetchWorks()
  loadUploadedFiles()
})
</script>

<template>
  <div class="upload-container">
    <div class="ink-bg"></div>
    
    <!-- 顶部导航 -->
    <header class="header dreamy-card">
      <div class="header-left">
        <span class="logo">🎭 戏曲 AI 助教</span>
      </div>
      <div class="header-right">
        <el-button class="dreamy-btn" @click="router.push('/works')">作品列表</el-button>
        <el-button class="dreamy-btn" @click="handleLogout">退出</el-button>
      </div>
    </header>

    <!-- 主内容 -->
    <main class="main-content fade-in">
      <h2 class="dreamy-title">上传管理</h2>
      
      <!-- 流程提示 -->
      <el-alert
        title="操作流程：①上传视频/音频 → ②点击'创建唱段' → ③选择作品并填写名称"
        type="info"
        :closable="false"
        style="margin-bottom: 24px"
      />

      <!-- 上传区 -->
      <div class="upload-section">
        <el-upload
          drag
          action=""
          :auto-upload="false"
          :on-change="(file: any) => handleVideoUpload(file.raw)"
          accept=".mp4,.mov,.avi"
          :show-file-list="false"
        >
          <div class="upload-content">
            <el-icon size="48"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽视频到此处 或 <em>点击上传</em></div>
            <div class="el-upload__tip">支持 MP4/MOV/AVI</div>
          </div>
        </el-upload>

        <el-upload
          drag
          action=""
          :auto-upload="false"
          :on-change="(file: any) => handleAudioUpload(file.raw)"
          accept=".mp3,.wav,.flac"
          :show-file-list="false"
        >
          <div class="upload-content">
            <el-icon size="48"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽音频到此处 或 <em>点击上传</em></div>
            <div class="el-upload__tip">支持 MP3/WAV/FLAC</div>
          </div>
        </el-upload>
      </div>

      <!-- 已上传文件列表 -->
      <div v-if="uploadedFiles.length > 0" class="file-list">
        <h3>已上传文件</h3>
        <el-table :data="uploadedFiles" style="width: 100%">
          <el-table-column prop="name" label="文件名" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'video' ? 'success' : 'warning'">
                {{ row.type === 'video' ? '视频' : '音频' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="url" label="路径" />
          <el-table-column label="操作" width="120">
            <template #default="{ row, $index }">
              <el-button
                v-if="row.type === 'video'"
                type="primary"
                size="small"
                :loading="row.extracting"
                @click="handleExtractAudio(row.url, $index)"
              >
                提取音频
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 创建唱段按钮 -->
      <el-button
        type="primary"
        class="dreamy-btn"
        style="margin-top: 24px"
        @click="openCreateDialog"
      >
        创建唱段
      </el-button>
    </main>

    <!-- 创建唱段弹窗 -->
    <el-dialog v-model="dialogVisible" title="创建唱段" width="500px">
      <el-form ref="segmentFormRef" :model="segmentForm" :rules="segmentRules" label-width="80px">
        <el-form-item label="作品" prop="work_id" required>
          <el-select
            v-model="segmentForm.work_id"
            placeholder="请选择作品"
            style="width: 100%"
          >
            <el-option
              v-for="work in works"
              :key="work.id"
              :label="work.name"
              :value="work.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="唱段名" prop="name" required>
          <el-input v-model="segmentForm.name" placeholder="请输入唱段名称" />
        </el-form-item>
        <el-form-item label="视频">
          <el-select v-model="segmentForm.video_url" placeholder="选择视频（可选）" style="width: 100%" clearable>
            <el-option
              v-for="file in uploadedFiles.filter(f => f.type === 'video')"
              :key="file.url"
              :label="file.name"
              :value="file.url"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="音频">
          <el-select v-model="segmentForm.audio_url" placeholder="选择音频（可选）" style="width: 100%" clearable>
            <el-option
              v-for="file in uploadedFiles.filter(f => f.type === 'audio')"
              :key="file.url"
              :label="file.name"
              :value="file.url"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" class="dreamy-btn" @click="handleCreateSegment">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.upload-container {
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

.upload-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
  margin-bottom: 24px;
}

.upload-content {
  padding: 40px;
  text-align: center;
}

.file-list {
  margin-top: 24px;
}

.file-list h3 {
  margin-bottom: 12px;
}
</style>
