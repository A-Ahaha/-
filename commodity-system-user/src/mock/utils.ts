export function delay(ms = 400) {
  return new Promise<void>((resolve) => setTimeout(resolve, ms))
}

export function nowISO() {
  return new Date().toISOString()
}

export function makeId(prefix: string) {
  return `${prefix}_${Math.random().toString(16).slice(2)}_${Date.now().toString(16)}`
}
