import api from './index'
import type { OperaWork, OperaSegment, SegmentSlice } from '@/types'

export const listWorks = () => api.get<OperaWork[]>('/segments/works')
export const createWork = (data: { name: string; category?: string; description?: string }) =>
  api.post<OperaWork>('/segments/works', data)
export const deleteWork = (workId: number) => api.delete(`/segments/works/${workId}`)
export const getWorkDetail = (workId: number) => api.get<OperaWork>(`/segments/works/${workId}`)
export const listSegments = () => api.get<OperaSegment[]>('/segments/')
export const createSegment = (data: { work_id: number; name: string; audio_url?: string; video_url?: string }) =>
  api.post<OperaSegment>('/segments', data)
export const deleteSegment = (segmentId: number) => api.delete(`/segments/${segmentId}`)
export const getSegmentDetail = (id: number) => api.get<OperaSegment>(`/segments/${id}`)
export const getSegmentByWorkId = (workId: number) => api.get<OperaSegment>(`/segments/by-work/${workId}`)
export const listSegmentsByWork = (workId: number) => api.get<OperaSegment[]>(`/segments/works/${workId}/segments`)
export const sliceAudio = (id: number) => api.post<{ full_lyrics: string; slices: SegmentSlice[] }>(`/segments/${id}/slice`)
export const extractLyrics = (id: number) => api.post<{ full_lyrics: string }>(`/segments/${id}/extract-lyrics`)
export const separateAudio = (id: number) => api.post<{ vocal_url: string; accompaniment_url: string; message: string }>(`/segments/${id}/separate`)
export const smartSlice = (id: number) => api.post<{ full_lyrics: string; chenzi_full: string; slices: SegmentSlice[] }>(`/segments/${id}/smart-slice`)
export const generateChenzi = (id: number, notations: Record<string, string>) =>
  api.post<{ message: string; slices: SegmentSlice[] }>(`/segments/${id}/generate-chenzi`, { notations })
export const updateLyrics = (id: number, lyrics: string) =>
  api.put<{ message: string; lyrics: string }>(`/segments/${id}/lyrics`, { lyrics })
export const updateSliceLyrics = (segmentId: number, sliceId: number, lyrics: string) =>
  api.put<{ message: string; lyrics: string }>(`/segments/${segmentId}/slices/${sliceId}`, { lyrics })
export const getSegmentPitches = (id: number) =>
  api.get<{ slices: Array<{ slice_id: number; slice_index: number; pitches: (number | null)[] }> }>(`/segments/${id}/pitches`)
export const regenerateChenzi = (id: number) =>
  api.post<{ message: string; updated_count: number }>(`/segments/${id}/regenerate-chenzi`)
export const generateMusic = (id: number, data: { lyrics: string; style?: string; duration?: number }) =>
  api.post<{ audio_url: string }>(`/segments/${id}/generate-music`, data, { timeout: 120000 })
