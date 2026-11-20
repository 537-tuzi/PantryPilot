/** 展示层格式化工具。归属：A 组。 */

/** 数量与单位必须同时展示（文档/03 §4）。 */
export function formatQuantity(quantity?: string | number | null, unit?: string | null): string {
  if (quantity === undefined || quantity === null || quantity === '') {
    return unit ?? ''
  }
  return unit ? `${quantity}${unit}` : String(quantity)
}

/** 距离今天的天数（按自然日计算）。 */
export function daysUntil(target: string | Date, today: string | Date): number {
  const targetDate = new Date(target)
  const base = new Date(today)
  const start = Date.UTC(base.getFullYear(), base.getMonth(), base.getDate())
  const end = Date.UTC(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate())
  return Math.round((end - start) / 86400000)
}

/** 临期状态。规则见 文档/02 §7：到期日早于今天为过期；今天至今天+3 天（含）为临期。 */
export function expiryStatus(
  expiryDate: string | null | undefined,
  today: string | Date,
  thresholdDays = 3,
): { status: 'normal' | 'expiring' | 'expired'; label: string; daysLeft: number | null } {
  if (!expiryDate) {
    return { status: 'normal', label: '未设置到期日', daysLeft: null }
  }
  const daysLeft = daysUntil(expiryDate, today)
  if (daysLeft < 0) {
    return { status: 'expired', label: `已过期 ${Math.abs(daysLeft)} 天`, daysLeft }
  }
  if (daysLeft === 0) {
    return { status: 'expiring', label: '今天到期', daysLeft }
  }
  if (daysLeft <= thresholdDays) {
    return { status: 'expiring', label: `${daysLeft} 天后到期`, daysLeft }
  }
  return { status: 'normal', label: `${daysLeft} 天后到期`, daysLeft }
}
