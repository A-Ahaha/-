export function setStorage(key: string, value: string) {
  localStorage.setItem(key, value)
}

export function getStorage(key: string): string | null {
  return localStorage.getItem(key)
}

export function removeStorage(key: string) {
  localStorage.removeItem(key)
}

export function setStorageJSON<T>(key: string, value: T) {
  localStorage.setItem(key, JSON.stringify(value))
}

export function getStorageJSON<T>(key: string): T | null {
  const raw = localStorage.getItem(key)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}
