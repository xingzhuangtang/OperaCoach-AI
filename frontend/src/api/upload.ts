import api from './index'

export const uploadVideo = (file: File) => {
  const formData = new FormData()
  formData.append('video', file)
  return api.post('/upload/video', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const uploadAudio = (file: File) => {
  const formData = new FormData()
  formData.append('audio', file)
  return api.post('/upload/audio', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export const extractAudio = (videoUrl: string) =>
  api.post('/upload/extract-audio', null, {
    params: { video_url: videoUrl },
  })
