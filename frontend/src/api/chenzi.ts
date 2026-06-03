import api from './index'

export const convertNotation = (notation: string, separator: string = '-') =>
  api.post<{ notation: string; chenzi: string; parsed: any[] }>('/chenzi/convert', { notation, separator })

export const batchConvertNotation = (notations: string[], separator: string = '-') =>
  api.post<{ results: Array<{ notation: string; chenzi: string }>; count: number }>('/chenzi/batch-convert', { notations, separator })

export const getMapping = () => api.get<{ mapping: Record<string, string>; description: string }>('/chenzi/mapping')
