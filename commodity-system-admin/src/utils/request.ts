import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios'
import { ElMessage } from 'element-plus'
import { STORAGE_SESSION_USER_ID_KEY, STORAGE_TOKEN_KEY, STORAGE_USER_KEY } from '@/constants/storage'
import { getStorage, removeStorage } from '@/utils/storage'

type ApiResult<T> = {
  code: number
  message: string
  data: T
}

const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
})

service.interceptors.request.use((config) => {
  const token = getStorage(STORAGE_TOKEN_KEY)
  if (token) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error) => {
    const status: number | undefined = error?.response?.status
    const message: string = error?.response?.data?.message || error?.message || '网络异常，请稍后重试'

    if (status === 401) {
      removeStorage(STORAGE_TOKEN_KEY)
      removeStorage(STORAGE_USER_KEY)
      removeStorage(STORAGE_SESSION_USER_ID_KEY)
      window.location.replace('/login')
    }

    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export async function request<T = unknown>(config: AxiosRequestConfig): Promise<T> {
  const res = await service.request<ApiResult<T>>(config)
  const body: unknown = res.data

  if (
    body &&
    typeof body === 'object' &&
    'code' in (body as Record<string, unknown>) &&
    'data' in (body as Record<string, unknown>)
  ) {
    const result = body as ApiResult<T>
    if (result.code !== 0) {
      ElMessage.error(result.message || '请求失败')
      throw new Error(result.message || '请求失败')
    }
    return result.data
  }

  return res.data as T
}
