export default function StatCard({ label, value, accentColor = '#3182CE' }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
      <div className="text-xs uppercase tracking-wide text-gray-500 font-medium mb-2">
        {label}
      </div>
      <div className="text-4xl font-bold" style={{ color: accentColor }}>
        {value}
      </div>
    </div>
  )
}
