export interface User {
  id: number
  phone: string
  username: string
  role: string
}

export interface OperaWork {
  id: number
  name: string
  category: string | null
  description?: string
}

export interface OperaSegment {
  id: number
  work_id: number
  name: string
  video_url: string | null
  audio_url: string | null
}

export interface SegmentSlice {
  id: number
  slice_index: number
  start_time: number
  end_time: number
  lyrics: string | null
  commands: string | null
  pitches: any[] | null
  audio_url: string | null
}

export interface LoginResponse {
  access_token: string
  token_type: string
}
