import { useEffect, useState } from 'react'
import Layout from '../components/Layout.jsx'
import { healthApi } from '../utils/api'
import { useAuth } from '../utils/auth.jsx'

export default function Settings() {
  const [health, setHealth] = useState(null)
  const { user } = useAuth()

  useEffect(() => { healthApi.check().then(setHealth).catch(() => {}) }, [])

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Settings</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold mb-3">Account</h2>
          <dl className="text-sm space-y-2">
            <div className="flex justify-between"><dt className="text-gray-600">Username</dt><dd className="font-medium">{user?.username}</dd></div>
            <div className="flex justify-between"><dt className="text-gray-600">Role</dt><dd className="font-medium">{user?.role}</dd></div>
          </dl>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-bold mb-3">System Health</h2>
          {!health && <div className="text-gray-500 text-sm">Checking…</div>}
          {health && (
            <dl className="text-sm space-y-2">
              <div className="flex justify-between">
                <dt className="text-gray-600">Status</dt>
                <dd className="font-medium text-risk-low">{health.status}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Model loaded</dt>
                <dd className="font-medium">{health.model_loaded ? 'Yes' : 'No'}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-gray-600">Model version</dt>
                <dd className="font-medium font-mono">{health.model_version || 'n/a'}</dd>
              </div>
            </dl>
          )}
        </div>
      </div>
    </Layout>
  )
}
