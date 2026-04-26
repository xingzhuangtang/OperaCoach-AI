import api from './index'
import type { OperaWork, OperaSegment } from '@/types'

export const listWorks = () => api.get<OperaWork[]>('/segments/works')
export const createWork = (data: { name: string; category?: string; description?: string }) =>
  api.post<OperaWork>('/segments/works', data)
export const listSegments = () => api.get<OperaSegment[]>('/segments/')
export const createSegment = (data: { work_id: number; name: string; audio_url?: string; video_url?: string }) =>
  api.post<OperaSegment>('/segments', data)
export const getSegmentDetail = (id: number) => api.get<OperaSegment>(`/segments/${id}`)
export const sliceAudio = (id: number) => api.post(`/segments/${id}/slice`)
