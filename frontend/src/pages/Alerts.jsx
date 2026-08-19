import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import { statsApi } from '../utils/api'
import { formatNGN, timeAgo, riskColorClass } from '../utils/format'

const FILTERS = [
  { id: 'all', label: 'All' },
  { id: 'high', label: 'High Risk' },
  { id: 'medium', label: 'Medium Risk' },
  { id: 'today', label: 'Today' },
]

export default function Alerts() {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all')
  const navigate = useNavigate()

  useEffect(() => {
    statsApi.recentAlerts(30).then(data => {
      setAlerts(data)
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [])

  const filtered = alerts.filter(a => {
    if (filter === 'high') return a.risk_score >= 0.5
    if (filter === 'medium') return a.risk_score >= 0.3 && a.risk_score < 0.5
    if (filter === 'today') {
      const today = new Date().toDateString()
      return new Date(a.timestamp).toDateString() === today
    }
    return true
  })

  const borderColor = (score) => {
    if (score >= 0.5) return '#E53E3E'
    if (score >= 0.3) return '#DD6B20'
    return '#38A169'
  }

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">
        Alerts — {loading ? '…' : filtered.length} record{filtered.length === 1 ? '' : 's'}
      </h1>
      <p className="text-sm text-gray-500 mb-6">Filter and review scored transactions</p>

      {/* Filter chips */}
      <div className="flex gap-2 mb-6">
        {FILTERS.map(f => (
          <button
            key={f.id}
            onClick={() => setFilter(f.id)}
            className={`text-sm px-4 py-1.5 rounded-full font-medium transition ${
              filter === f.id
                ? 'bg-brand-500 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {f.label}
          </button>
        ))}
      </div>

      {/* Alert cards */}
      <div className="space-y-3">
        {loading && (
          <div className="text-gray-500">Loading…</div>
        )}
        {!loading && filtered.length === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 text-center text-gray-500">
            No alerts match this filter.
          </div>
        )}
        {filtered.map((a) => (
          <div
            key={a.transaction_id}
            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden flex"
          >
            <div style={{ backgroundColor: borderColor(a.risk_score), width: '6px' }} />
            <div className="flex-1 grid grid-cols-1 md:grid-cols-[1fr_1fr_2fr_auto] gap-4 items-center p-4">
              <div>
                <div className="font-bold text-gray-800">TX-{a.transaction_id}</div>
                <div className="text-lg text-gray-800 mt-1">{formatNGN(a.amount)}</div>
                <div className="text-xs text-gray-500 mt-1">{timeAgo(a.timestamp)}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">Risk Score</div>
                <div className={`text-3xl font-bold ${riskColorClass(a.risk_score)}`}>
                  {a.risk_score.toFixed(2)}
                </div>
                <div className="text-xs text-gray-500 mt-1">{a.type}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-wide text-gray-500 mb-1">
                  Top Driver (SHAP)
                </div>
                <div className="font-mono text-sm text-gray-800">{a.top_feature}</div>
                <div className="text-xs text-gray-500 mt-1">Status: {a.status}</div>
              </div>
              <button
                onClick={() => navigate(`/result/${a.transaction_id}`)}
                className="bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm rounded-lg px-4 py-2 whitespace-nowrap"
              >
                Review
              </button>
            </div>
          </div>
        ))}
      </div>
    </Layout>
  )
}
