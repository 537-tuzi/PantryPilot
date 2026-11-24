/** Decimal 字符串工具：整数千分位运算，避免 parseFloat 精度漂移。归属：A 组。 */

/** 将 Decimal 字符串转为整数千分位（scale 3）。"1.5" -> 1500。 */
export function toMilliunits(value: string): number {
  const negative = value.startsWith('-')
  const unsigned = negative ? value.slice(1) : value
  const [intPart, decPart = ''] = unsigned.split('.')
  const padded = (decPart + '000').slice(0, 3)
  const result = Number(intPart) * 1000 + Number(padded)
  return negative ? -result : result
}

/** 比较两个 Decimal 字符串（千分位精度）。返回 -1/0/1。 */
export function compareDecimal(a: string, b: string): number {
  const ma = toMilliunits(a)
  const mb = toMilliunits(b)
  return ma < mb ? -1 : ma > mb ? 1 : 0
}

/** 校验非负 Decimal 格式：最多 maxInt 整数位 + 最多 scale 小数位。 */
export function isValidDecimal(value: string, scale: number, maxInt: number): boolean {
  const re = new RegExp(`^\\d{1,${maxInt}}(\\.\\d{1,${scale}})?$`)
  return re.test(value)
}