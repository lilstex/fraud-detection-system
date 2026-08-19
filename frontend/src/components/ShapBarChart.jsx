/**
 * Horizontal bar chart of SHAP contributions matching the mockup in the report.
 * Positive contributions (pushing toward fraud) are shown in red/orange;
 * negative contributions (pushing toward legitimate) are shown in green.
 */
export default function ShapBarChart({ features = [] }) {
  if (!features.length) {
    return <div className="text-sm text-gray-500">No SHAP contributions available.</div>
  }

  const maxAbs = Math.max(...features.map(f => Math.abs(f.contribution)))

  const barColor = (contrib) => {
    if (contrib > 0.3 * maxAbs) return '#C53030'      // strong positive - red
    if (contrib > 0) return '#DD6B20'                  // positive - orange
    return '#38A169'                                    // negative - green
  }

  return (
    <div className="space-y-3">
      {features.map((f, i) => {
        const width = Math.max(4, (Math.abs(f.contribution) / maxAbs) * 100)
        return (
          <div key={i} className="grid grid-cols-[300px_1fr_60px] gap-3 items-center">
            <div className="text-sm text-gray-800 truncate" title={`${f.feature} = ${f.value}`}>
              <span className="font-mono">{f.feature}</span>
              <span className="text-gray-500 ml-2">= {typeof f.value === 'number' ? f.value.toFixed(2) : f.value}</span>
            </div>
            <div className="relative h-6 bg-gray-100 rounded">
              <div
                className="absolute top-0 left-0 h-6 rounded transition-all"
                style={{ width: `${width}%`, backgroundColor: barColor(f.contribution) }}
              />
            </div>
            <div className={`text-sm font-semibold text-right ${f.contribution >= 0 ? 'text-gray-800' : 'text-risk-low'}`}>
              {f.contribution >= 0 ? '+' : ''}{f.contribution.toFixed(2)}
            </div>
          </div>
        )
      })}
    </div>
  )
}
