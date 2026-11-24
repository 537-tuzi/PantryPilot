/** 展示层数量格式化：去尾零，绝不改动用于提交的原始字符串。归属：A 组。 */

/** "1.500"->"1.5"，"0.000"->"0"，数量与单位同屏。 */
export function formatQuantityDisplay(quantity?: string | number | null, unit?: string | null): string {
  const u = unit ?? ''
  if (quantity === undefined || quantity === null || quantity === '') {
    return u
  }
  let s = String(quantity)
  if (s.includes('.')) {
    s = s.replace(/0+$/, '').replace(/\.$/, '')
  }
  return `${s}${u}`
}