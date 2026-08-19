export const formatNGN = (amount) => {
  if (amount == null) return '-'
  return `₦${Number(amount).toLocaleString('en-NG', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
}

export const formatDate = (isoString) => {
  if (!isoString) return '-'
  try {
    const d = new Date(isoString)
    return d.toLocaleString('en-NG', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    })
  } catch {
    return isoString
  }
}

export const timeAgo = (isoString) => {
  if (!isoString) return '-'
  const then = new Date(isoString).getTime()
  const now = Date.now()
  const diffMin = Math.floor((now - then) / 60000)
  if (diffMin < 1) return 'just now'
  if (diffMin < 60) return `${diffMin} min ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr} hr ago`
  const diffDay = Math.floor(diffHr / 24)
  return `${diffDay} day${diffDay > 1 ? 's' : ''} ago`
}

export const riskLevel = (score) => {
  if (score == null) return 'unknown'
  if (score >= 0.5) return 'high'
  if (score >= 0.3) return 'medium'
  return 'low'
}

export const riskColorClass = (score) => {
  const level = riskLevel(score)
  return {
    high: 'text-risk-high',
    medium: 'text-risk-medium',
    low: 'text-risk-low',
    unknown: 'text-gray-500',
  }[level]
}

export const statusBadgeClass = (status) => {
  const map = {
    FLAGGED: 'text-risk-high font-bold',
    REVIEW: 'text-risk-medium font-bold',
    CONFIRMED_FRAUD: 'text-risk-high font-bold',
    FALSE_ALERT: 'text-gray-500',
    OK: 'text-risk-low',
  }
  return map[status] || 'text-gray-600'
}
