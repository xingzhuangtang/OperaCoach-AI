import api from './index'

export interface MusicGeneration {
  id: number
  title: string
  lyrics: string
  style: string
  duration: number
  voice_gender: string
  audio_url: string
  cover_url: string
  album_id: number | null
  created_at: string
}

export interface MusicAlbum {
  id: number
  name: string
  cover_url: string
  created_at: string
}

export const generateMusic = (data: {
  lyrics: string
  title?: string
  style?: string
  duration?: number
  voice_gender?: string
}) => api.post<MusicGeneration>('/music/generate', data, { timeout: 120000 })

export const getMusicHistory = () =>
  api.get<MusicGeneration[]>('/music/history')

export const updateMusic = (id: number, data: { title?: string; album_id?: number | null }) =>
  api.put<MusicGeneration>(`/music/${id}`, data)

export const deleteMusic = (id: number) =>
  api.delete(`/music/${id}`)

export const createAlbum = (data: { name: string }) =>
  api.post<MusicAlbum>('/music/albums', data)

export const getAlbums = () =>
  api.get<MusicAlbum[]>('/music/albums')

export const deleteAlbum = (id: number) =>
  api.delete(`/music/albums/${id}`)

export const uploadReferenceAudio = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return api.post<{ url: string; filename: string }>('/music/upload-reference', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

export interface WorkOption {
  id: number
  name: string
  category: string
}

export const getWorksForMusic = () =>
  api.get<WorkOption[]>('/music/works')

export const sendToSegment = (musicId: number, data: { work_id?: number; work_name?: string }) =>
  api.post<{ segment_id: number; work_id: number }>(`/music/${musicId}/to-segment`, data)
