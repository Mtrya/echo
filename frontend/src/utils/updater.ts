import type { Ref } from 'vue'

export interface UpdateState {
  status: 'idle' | 'checking' | 'available' | 'downloading' | 'installing' | 'error'
  version?: string
  currentVersion?: string
  notes?: string
  install?: () => Promise<void>
}

export async function checkForUpdates(state: Ref<UpdateState>): Promise<void> {
  try {
    const { check } = await import('@tauri-apps/plugin-updater')
    const { relaunch } = await import('@tauri-apps/plugin-process')

    state.value = { status: 'checking' }
    const update = await check()

    if (update) {
      state.value = {
        status: 'available',
        version: update.version,
        currentVersion: update.currentVersion,
        notes: update.body ?? undefined,
        install: async () => {
          try {
            state.value = { ...state.value, status: 'downloading' }
            await update.downloadAndInstall()
            state.value = { ...state.value, status: 'installing' }
            await relaunch()
          } catch (e) {
            console.error('Update install failed:', e)
            state.value = { status: 'error' }
          }
        }
      }
    } else {
      state.value = { status: 'idle' }
    }
  } catch (e) {
    console.error('Update check failed:', e)
    state.value = { status: 'idle' }
  }
}
