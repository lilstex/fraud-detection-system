import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, PlusCircle, History, Bell, FileText, Settings, LogOut, Shield } from 'lucide-react'
import { useAuth } from '../utils/auth.jsx'

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/new', label: 'New Transaction', icon: PlusCircle },
  { to: '/history', label: 'History', icon: History },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/reports', label: 'Reports', icon: FileText },
  { to: '/settings', label: 'Settings', icon: Settings },
]

export default function Sidebar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <aside className="w-60 bg-brand-600 text-white flex flex-col shrink-0">
      {/* Brand header */}
      <div className="px-5 py-5 border-b border-white/10 flex items-center gap-2">
        <Shield className="w-6 h-6 text-white" strokeWidth={2} />
        <div>
          <div className="text-sm font-semibold leading-tight">Fraud Detection</div>
          <div className="text-[11px] text-white/60">Nigerian Mobile Money</div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-5 py-3 text-sm transition ${
                isActive
                  ? 'bg-brand-500 text-white font-semibold'
                  : 'text-white/85 hover:bg-white/10'
              }`
            }
          >
            <Icon className="w-4 h-4" strokeWidth={2} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* User footer */}
      <div className="px-5 py-4 border-t border-white/10 text-xs">
        <div className="text-white/70">Signed in as</div>
        <div className="font-semibold mb-2">{user?.username || 'unknown'} ({user?.role})</div>
        <button
          onClick={handleLogout}
          className="flex items-center gap-2 text-white/80 hover:text-white transition"
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out</span>
        </button>
      </div>
    </aside>
  )
}
