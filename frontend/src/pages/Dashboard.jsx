import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import StatCard from '../components/StatCard.jsx'
import { statsApi } from '../utils/api'
import { formatNGN, statusBadgeClass } from '../utils/format'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      try {
        const [s, a] = await Promise.all([
          statsApi.get(),
          statsApi.recentAlerts(8),
        ])
        setStats(s)
        setAlerts(a)
      } catch (err) {
        setError(err.response?.data?.detail || err.message)
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Overview</h1>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-4">
          {error}
        </div>
      )}

      {/* Stat cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard
          label="Scored Today"
          value={loading ? '…' : (stats?.scored_today ?? 0).toLocaleString()}
          accentColor="#3182CE"
        />
        <StatCard
          label="Fraud Flagged"
          value={loading ? '…' : (stats?.fraud_flagged ?? 0).toLocaleString()}
          accentColor="#E53E3E"
        />
        <StatCard
          label="Under Review"
          value={loading ? '…' : (stats?.under_review ?? 0).toLocaleString()}
          accentColor="#DD6B20"
        />
        <StatCard
          label="False-Positive Rate"
          value={loading ? '…' : `${((stats?.false_positive_rate ?? 0) * 100).toFixed(1)}%`}
          accentColor="#38A169"
        />
      </div>

      {/* Recent alerts table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900">Recent Alerts</h2>
          <Link to="/alerts" className="text-sm text-brand-500 hover:text-brand-600 font-medium">
            View all →
          </Link>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr className="text-left text-xs uppercase tracking-wide text-gray-600">
                <th className="px-5 py-3 font-semibold">TX ID</th>
                <th className="px-5 py-3 font-semibold">Amount</th>
                <th className="px-5 py-3 font-semibold">Type</th>
                <th className="px-5 py-3 font-semibold">Risk Score</th>
                <th className="px-5 py-3 font-semibold">Top Feature</th>
                <th className="px-5 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading && (
                <tr><td colSpan={6} className="px-5 py-6 text-center text-gray-500">Loading…</td></tr>
              )}
              {!loading && alerts.length === 0 && (
                <tr><td colSpan={6} className="px-5 py-6 text-center text-gray-500">
                  No alerts yet. Submit a transaction from “New Transaction”.
                </td></tr>
              )}
              {alerts.map((a) => (
                <tr
                  key={a.transaction_id}
                  className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
                  onClick={() => window.location.href = `/result/${a.transaction_id}`}
                >
                  <td className="px-5 py-3 font-medium text-gray-800">TX-{a.transaction_id}</td>
                  <td className="px-5 py-3 text-gray-800">{formatNGN(a.amount)}</td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-medium text-gray-700 bg-gray-100 rounded px-2 py-0.5">
                      {a.type}
                    </span>
                  </td>
                  <td className="px-5 py-3 font-semibold text-gray-800">{a.risk_score.toFixed(2)}</td>
                  <td className="px-5 py-3 font-mono text-xs text-gray-700">{a.top_feature}</td>
                  <td className={`px-5 py-3 text-xs ${statusBadgeClass(a.status)}`}>{a.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  )
}
