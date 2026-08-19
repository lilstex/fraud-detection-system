import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Layout from '../components/Layout.jsx'
import { predictApi } from '../utils/api'
import { AlertCircle, Sparkles } from 'lucide-react'

const INITIAL_FORM = {
  type: 'TRANSFER',
  sender_account: 'C1204583910',
  receiver_account: 'C9876543210',
  amount: '450000',
  sender_balance_before: '480000',
  sender_balance_after: '30000',
  receiver_balance_before: '15000',
  receiver_balance_after: '465000',
  channel: 'USSD',
  hours_since_sim_change: '6',
  is_new_device: true,
  impossible_travel: false,
  ussd_session_duration: '12',
  distance_from_home_km: '340',
}

const LEGIT_SAMPLE = {
  type: 'PAYMENT',
  sender_account: 'C1234567890',
  receiver_account: 'C5544332211',
  amount: '8500',
  sender_balance_before: '45000',
  sender_balance_after: '36500',
  receiver_balance_before: '120000',
  receiver_balance_after: '128500',
  channel: 'APP',
  hours_since_sim_change: '1200',
  is_new_device: false,
  impossible_travel: false,
  ussd_session_duration: '0',
  distance_from_home_km: '2',
}

const FIELDS = [
  { key: 'type', label: 'Transaction Type', type: 'select',
    options: ['TRANSFER', 'CASH-OUT', 'PAYMENT', 'CASH-IN', 'DEBIT'] },
  { key: 'sender_account', label: 'Sender Account', type: 'text' },
  { key: 'receiver_account', label: 'Receiver Account', type: 'text' },
  { key: 'amount', label: 'Amount (NGN)', type: 'number' },
  { key: 'sender_balance_before', label: 'Sender Balance Before', type: 'number' },
  { key: 'sender_balance_after', label: 'Sender Balance After', type: 'number' },
  { key: 'receiver_balance_before', label: 'Receiver Balance Before', type: 'number' },
  { key: 'receiver_balance_after', label: 'Receiver Balance After', type: 'number' },
]

const META_FIELDS = [
  { key: 'channel', label: 'Channel', type: 'select', options: ['APP', 'USSD', 'WEB'] },
  { key: 'hours_since_sim_change', label: 'Hours Since SIM Change', type: 'number' },
  { key: 'ussd_session_duration', label: 'USSD Session Duration (s)', type: 'number' },
  { key: 'distance_from_home_km', label: 'Distance from Home (km)', type: 'number' },
]

export default function NewTransaction() {
  const [form, setForm] = useState(INITIAL_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const update = (key, value) => setForm(prev => ({ ...prev, [key]: value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      const payload = {
        ...form,
        amount: parseFloat(form.amount),
        sender_balance_before: parseFloat(form.sender_balance_before),
        sender_balance_after: parseFloat(form.sender_balance_after),
        receiver_balance_before: parseFloat(form.receiver_balance_before),
        receiver_balance_after: parseFloat(form.receiver_balance_after),
        hours_since_sim_change: form.hours_since_sim_change ? parseFloat(form.hours_since_sim_change) : undefined,
        ussd_session_duration: form.ussd_session_duration ? parseInt(form.ussd_session_duration) : undefined,
        distance_from_home_km: form.distance_from_home_km ? parseFloat(form.distance_from_home_km) : undefined,
      }
      const result = await predictApi.predict(payload)
      navigate(`/result/${result.transaction_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Scoring failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Submit Transaction for Scoring</h1>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setForm(LEGIT_SAMPLE)}
            className="text-sm px-3 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1"
          >
            <Sparkles className="w-3.5 h-3.5" /> Load legitimate sample
          </button>
          <button
            type="button"
            onClick={() => setForm(INITIAL_FORM)}
            className="text-sm px-3 py-1.5 border border-gray-300 rounded-lg bg-white hover:bg-gray-50 text-gray-700 flex items-center gap-1"
          >
            <Sparkles className="w-3.5 h-3.5" /> Load fraud sample
          </button>
        </div>
      </div>

      {error && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 text-red-700 rounded-lg p-3 mb-4 text-sm">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <div>{error}</div>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 max-w-4xl">
        <div className="grid grid-cols-1 gap-4">
          {FIELDS.map(f => (
            <div key={f.key} className="grid grid-cols-[220px_1fr] items-center gap-4">
              <label className="text-sm text-gray-600">{f.label}</label>
              {f.type === 'select' ? (
                <select
                  value={form[f.key]}
                  onChange={e => update(f.key, e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  required
                >
                  {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                </select>
              ) : (
                <input
                  type={f.type}
                  value={form[f.key]}
                  onChange={e => update(f.key, e.target.value)}
                  className="border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  required
                  step={f.type === 'number' ? '0.01' : undefined}
                />
              )}
            </div>
          ))}
        </div>

        <div className="mt-8 pt-6 border-t border-gray-100">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Nigerian-Context Metadata (optional)
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {META_FIELDS.map(f => (
              <div key={f.key} className="grid grid-cols-[180px_1fr] items-center gap-3">
                <label className="text-sm text-gray-600">{f.label}</label>
                {f.type === 'select' ? (
                  <select
                    value={form[f.key]}
                    onChange={e => update(f.key, e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  >
                    {f.options.map(o => <option key={o} value={o}>{o}</option>)}
                  </select>
                ) : (
                  <input
                    type={f.type}
                    value={form[f.key]}
                    onChange={e => update(f.key, e.target.value)}
                    className="border border-gray-300 rounded-lg px-3 py-2 bg-gray-50 focus:ring-2 focus:ring-brand-500 focus:border-brand-500 outline-none"
                  />
                )}
              </div>
            ))}
            <div className="flex items-center gap-2 col-span-full">
              <input
                id="is_new_device"
                type="checkbox"
                checked={form.is_new_device}
                onChange={e => update('is_new_device', e.target.checked)}
                className="rounded"
              />
              <label htmlFor="is_new_device" className="text-sm text-gray-700">Device not seen before</label>

              <input
                id="impossible_travel"
                type="checkbox"
                checked={form.impossible_travel}
                onChange={e => update('impossible_travel', e.target.checked)}
                className="rounded ml-6"
              />
              <label htmlFor="impossible_travel" className="text-sm text-gray-700">Impossible travel</label>
            </div>
          </div>
        </div>

        <div className="mt-8 flex justify-end">
          <button
            type="submit"
            disabled={submitting}
            className="bg-brand-500 hover:bg-brand-600 text-white font-semibold rounded-lg px-6 py-2.5 transition disabled:opacity-60"
          >
            {submitting ? 'Scoring…' : 'Score Transaction'}
          </button>
        </div>
      </form>
    </Layout>
  )
}
