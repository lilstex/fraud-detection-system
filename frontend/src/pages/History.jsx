import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import Layout from '../components/Layout.jsx'
import { transactionsApi } from '../utils/api'
import { formatNGN, formatDate, statusBadgeClass } from '../utils/format'

const PAGE_SIZE = 20

export default function History() {
  const [txs, setTxs] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    setLoading(true)
    const offset = (page - 1) * PAGE_SIZE
    transactionsApi.list({ limit: PAGE_SIZE + 1, offset }).then(data => {
      setHasNext(data.length > PAGE_SIZE)
      setTxs(data.slice(0, PAGE_SIZE))
      setLoading(false)
    }).catch(() => setLoading(false))
  }, [page])

  const filtered = txs.filter(tx => {
    if (!filter) return true
    return (
      tx.sender_account.includes(filter) ||
      tx.receiver_account.includes(filter) ||
      String(tx.transaction_id).includes(filter) ||
      (tx.classification || '').includes(filter.toUpperCase())
    )
  })

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-4">Transaction History</h1>
      <input
        value={filter}
        onChange={e => setFilter(e.target.value)}
        placeholder="Filter by account, transaction ID, or classification (current page)…"
        className="w-full max-w-md border border-gray-300 rounded-lg px-3 py-2 mb-6 focus:ring-2 focus:ring-brand-500 outline-none"
      />
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr className="text-left text-xs uppercase tracking-wide text-gray-600">
                <th className="px-5 py-3 font-semibold">TX ID</th>
                <th className="px-5 py-3 font-semibold">Timestamp</th>
                <th className="px-5 py-3 font-semibold">Type</th>
                <th className="px-5 py-3 font-semibold">Sender → Receiver</th>
                <th className="px-5 py-3 font-semibold">Amount</th>
                <th className="px-5 py-3 font-semibold">Risk</th>
                <th className="px-5 py-3 font-semibold">Status</th>
              </tr>
            </thead>
            <tbody>
              {loading && <tr><td colSpan={7} className="px-5 py-6 text-center text-gray-500">Loading…</td></tr>}
              {!loading && filtered.length === 0 && (
                <tr><td colSpan={7} className="px-5 py-6 text-center text-gray-500">No transactions.</td></tr>
              )}
              {filtered.map(tx => (
                <tr
                  key={tx.transaction_id}
                  className="border-b border-gray-50 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/result/${tx.transaction_id}`)}
                >
                  <td className="px-5 py-3 font-medium text-gray-800">TX-{tx.transaction_id}</td>
                  <td className="px-5 py-3 text-gray-600 text-xs">{formatDate(tx.timestamp)}</td>
                  <td className="px-5 py-3">
                    <span className="text-xs font-medium bg-gray-100 rounded px-2 py-0.5">{tx.type}</span>
                  </td>
                  <td className="px-5 py-3 font-mono text-xs text-gray-700">
                    {tx.sender_account} → {tx.receiver_account}
                  </td>
                  <td className="px-5 py-3 font-medium text-gray-800">{formatNGN(tx.amount)}</td>
                  <td className="px-5 py-3 font-semibold">
                    {tx.risk_score != null ? tx.risk_score.toFixed(2) : '-'}
                  </td>
                  <td className={`px-5 py-3 text-xs ${statusBadgeClass(tx.classification === 'FRAUD' ? 'FLAGGED' : 'OK')}`}>
                    {tx.reviewed ? 'REVIEWED' : (tx.classification === 'FRAUD' ? 'FLAGGED' : (tx.classification || '-'))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <div className="text-xs text-gray-500">Page {page}</div>
        <div className="flex gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page <= 1 || loading}
            className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            <ChevronLeft className="w-4 h-4" /> Prev
          </button>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={!hasNext || loading}
            className="flex items-center gap-1 text-sm px-3 py-1.5 rounded-lg border border-gray-300 text-gray-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </Layout>
  )
}
