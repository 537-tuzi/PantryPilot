/** 应用时区（Asia/Shanghai）今天与纯日期部件运算。ADR-0001。归属：A 组。 */

/** 应用时区的今天（YYYY-MM-DD），非浏览器本地。 */
export function appToday(): string {
  return new Intl.DateTimeFormat('en-CA', {
    timeZone: 'Asia/Shanghai',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).format(new Date())
}

/** 纯日期部件差值（天），避免负时区浏览器 off-by-one。 */
export function daysUntilDatePart(target: string, today: string): number {
  const [ty, tm, td] = target.split('-').map(Number)
  const [by, bm, bd] = today.split('-').map(Number)
  const start = Date.UTC(by, bm - 1, bd)
  const end = Date.UTC(ty, tm - 1, td)
  return Math.round((end - start) / 86400000)
}

/** 剩余天数文案（Home/Expiry 共用，避免复制漂移）。today 为空时抑制文案。 */
export function expiryDayLabel(expiryDate: string | null | undefined, today: string): string {
  if (!expiryDate) {
    return '未设置到期日'
  }
  if (!today) {
    return ''
  }
  const d = daysUntilDatePart(expiryDate, today)
  if (d < 0) {
    return `已过期 ${-d} 天`
  }
  return d === 0 ? '今天到期' : `${d} 天后到期`
}