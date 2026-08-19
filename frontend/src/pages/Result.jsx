import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import ShapBarChart from '../components/ShapBarChart.jsx'
import { transactionsApi, reviewsApi } from '../utils/api'
import { formatNGN, formatDate, riskColorClass } from '../utils/format'
import { showSuccess, showError } from '../utils/alerts'
import { AlertCircle, CheckCircle2, XCircle, MessageSquarePlus } from 'lucide-react'

export default function Result() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [tx, setTx] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [reviewing, setReviewing] = useState(false)
  const [showNotes, setShowNotes] = useState(false)
  const [notes, setNotes] = useState('')

  const load = async () => {
    try {
      const data = await transactionsApi.get(id)
      setTx(data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { load() }, [id])

  const recordReview = async (outcome) => {
    setReviewing(true)
    try {
      await reviewsApi.create({
        prediction_id: tx.prediction_id,
        outcome,
        notes: notes || null,
      })
      await showSuccess('Review recorded', outcome)
      navigate('/alerts')
    } catch (err) {
      await showError('Review failed', err.response?.data?.detail || err.message)
    } finally {
      setReviewing(false)
    }
  }

  if (loading) {
    return <Layout><div className="text-gray-500">Loading…</div></Layout>
  }
  if (error || !tx) {
    return (
      <Layout>
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4">
          {error || 'Not found'}
        </div>
      </Layout>
    )
  }

  const isFraud = tx.classification === 'FRAUD'
  const recommendation = tx.risk_score >= 0.7 ? 'RECOMMEND HOLD'
                       : tx.risk_score >= 0.4 ? 'RECOMMEND REVIEW'
                       : 'RECOMMEND ALLOW'

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Scoring Result: TX-{tx.transaction_id}</h1>
        <div className="text-xs text-gray-500">{formatDate(tx.timestamp)}</div>
      </div>

      {/* Top row: Risk card + Model card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 mb-6">
        <div className={`lg:col-span-2 bg-white rounded-xl shadow-sm border-2 p-6 ${isFraud ? 'border-risk-high' : 'border-risk-low'}`}>
          <div className="text-xs uppercase tracking-wide text-gray-500 font-medium mb-2">
            Risk Score
          </div>
          <div className={`text-6xl font-bold ${riskColorClass(tx.risk_score)}`}>
            {tx.risk_score.toFixed(2)}
          </div>
          <div className={`text-sm font-bold mt-2 ${riskColorClass(tx.risk_score)}`}>
            {tx.classification}: {recommendation}
          </div>
          {tx.review_outcome && (
            <div className="text-xs text-gray-500 mt-2">
              Reviewed: <span className="font-semibold">{tx.review_outcome}</span>
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="text-xs uppercase tracking-wide text-gray-500 font-medium mb-2">
            Model
          </div>
          <div className="text-xl font-bold text-gray-800 mb-3">
            {tx.model_version || 'unknown'}
          </div>
          <dl className="text-sm space-y-1.5 text-gray-600">
            <div className="flex justify-between">
              <dt>Threshold</dt><dd className="font-medium">{tx.threshold?.toFixed(2) ?? '-'}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Type</dt><dd className="font-medium">{tx.type}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Amount</dt><dd className="font-medium">{formatNGN(tx.amount)}</dd>
            </div>
            <div className="flex justify-between">
              <dt>Channel</dt><dd className="font-medium">{tx.channel || 'n/a'}</dd>
            </div>
          </dl>
        </div>
      </div>

      {/* SHAP explanation */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Top Contributing Features (SHAP)</h2>
        <ShapBarChart features={tx.shap_top_features || []} />
      </div>

      {/* Notes textarea */}
      {showNotes && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-4">
          <label className="text-sm font-medium text-gray-700 block mb-2">Notes</label>
          <textarea
            value={notes}
            onChange={e => setNotes(e.target.value)}
            className="w-full border border-gray-300 rounded-lg p-2 text-sm focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
            rows={3}
            placeholder="Add any notes about this review decision…"
          />
        </div>
      )}

      {/* Action buttons */}
      {!tx.review_outcome && (
        <div className="flex gap-2">
          <button
            onClick={() => recordReview('CONFIRMED_FRAUD')}
            disabled={reviewing}
            className="bg-risk-high hover:bg-red-700 text-white font-semibold rounded-lg px-5 py-2.5 flex items-center gap-2 disabled:opacity-60"
          >
            <XCircle className="w-4 h-4" /> Confirm Fraud
          </button>
          <button
            onClick={() => recordReview('FALSE_ALERT')}
            disabled={reviewing}
            className="bg-risk-medium hover:bg-orange-700 text-white font-semibold rounded-lg px-5 py-2.5 flex items-center gap-2 disabled:opacity-60"
          >
            <CheckCircle2 className="w-4 h-4" /> Mark as False Alert
          </button>
          <button
            onClick={() => setShowNotes(v => !v)}
            className="bg-gray-500 hover:bg-gray-600 text-white font-semibold rounded-lg px-5 py-2.5 flex items-center gap-2"
          >
            <MessageSquarePlus className="w-4 h-4" /> {showNotes ? 'Hide Notes' : 'Add Notes'}
          </button>
        </div>
      )}
    </Layout>
  )
}
