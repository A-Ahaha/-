import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore('app', () => {
  const globalLoading = ref(false)

  function setGlobalLoading(v: boolean) {
    globalLoading.value = v
  }

  return { globalLoading, setGlobalLoading }
})
