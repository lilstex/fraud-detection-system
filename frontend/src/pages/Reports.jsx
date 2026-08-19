import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import { statsApi } from '../utils/api'

export default function Reports() {
  const [stats, setStats] = useState(null)
  useEffect(() => { statsApi.get().then(setStats).catch(() => {}) }, [])

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Reports</h1>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 max-w-2xl">
        <h2 className="text-lg font-bold mb-4">System Summary</h2>
        {!stats && <div className="text-gray-500">Loading…</div>}
        {stats && (
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between border-b border-gray-100 pb-2">
              <dt className="text-gray-600">Total transactions scored</dt>
              <dd className="font-semibold">{stats.total_transactions.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between border-b border-gray-100 pb-2">
              <dt className="text-gray-600">Scored today</dt>
              <dd className="font-semibold">{stats.scored_today.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between border-b border-gray-100 pb-2">
              <dt className="text-gray-600">Flagged as fraud</dt>
              <dd className="font-semibold text-risk-high">{stats.fraud_flagged.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between border-b border-gray-100 pb-2">
              <dt className="text-gray-600">Under review</dt>
              <dd className="font-semibold text-risk-medium">{stats.under_review.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between border-b border-gray-100 pb-2">
              <dt className="text-gray-600">Total reviews recorded</dt>
              <dd className="font-semibold">{stats.total_reviews.toLocaleString()}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-gray-600">False-positive rate</dt>
              <dd className="font-semibold text-risk-low">
                {(stats.false_positive_rate * 100).toFixed(2)}%
              </dd>
            </div>
          </dl>
        )}
        <div className="mt-6 pt-4 border-t border-gray-100 text-xs text-gray-500">
          Data is computed live from the predictions and reviews tables.
        </div>
      </div>
    </Layout>
  )
}
