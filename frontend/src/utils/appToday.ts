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