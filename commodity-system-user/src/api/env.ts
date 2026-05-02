export function useMockApi() {
  const raw = import.meta.env.VITE_USE_MOCK
  return raw === true || raw === 'true'
}

export function getAdminAppUrl() {
  return String(import.meta.env.VITE_ADMIN_APP_URL || '')
}
