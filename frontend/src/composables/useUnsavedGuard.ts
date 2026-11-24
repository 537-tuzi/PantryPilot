/** 脏表单离开确认（preferences/ingredient-form 共用）。归属：A 组。 */
import type { Ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { useConfirm } from './useConfirm'

export function useUnsavedGuard(dirty: Ref<boolean>): void {
  onBeforeRouteLeave(async () => {
    if (!dirty.value) {
      return true
    }
    return await useConfirm({
      title: '放弃修改？',
      message: '有未保存的修改，确定离开？',
      type: 'warning',
    })
  })
}