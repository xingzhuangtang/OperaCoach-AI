import api from './index'
import type { User, LoginResponse } from '@/types'

export const login = (phone: string, password: string) =>
  api.post<LoginResponse>('/auth/login', { phone, password })

export const register = (phone: string, username: string, password: string) =>
  api.post<User>('/auth/register', { phone, username, password })
