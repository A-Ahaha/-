export function useMockApi() {
  const raw = import.meta.env.VITE_USE_MOCK
  return raw === true || raw === 'true'
}
