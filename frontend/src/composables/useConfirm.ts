/** 二次确认（删除/扣减）。取消 resolve false 不 throw。归属：A 组。 */
import { ElMessageBox } from 'element-plus'
import type { VNode } from 'vue'

export interface ConfirmOptions {
  title: string
  message: string | VNode
  confirmText?: string
  cancelText?: string
  type?: 'warning' | 'success' | 'info' | 'error'
}

export async function useConfirm(opts: ConfirmOptions): Promise<boolean> {
  try {
    await ElMessageBox.confirm(opts.message, opts.title, {
      confirmButtonText: opts.confirmText ?? '确认',
      cancelButtonText: opts.cancelText ?? '取消',
      type: opts.type ?? 'warning',
      distinguishCancelAndClose: true,
    })
    return true
  } catch {
    return false
  }
}