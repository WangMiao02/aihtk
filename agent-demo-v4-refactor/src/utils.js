export function sleep(ms) { return new Promise(r => setTimeout(r, ms)) }

export function nowTime() {
  const d = new Date()
  return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`
}
