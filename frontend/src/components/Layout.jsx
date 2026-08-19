import Sidebar from './Sidebar.jsx'

export default function Layout({ children }) {
  return (
    <div className="flex h-screen bg-[#F7FAFC]">
      <Sidebar />
      <main className="flex-1 overflow-auto">
        <div className="max-w-[1400px] mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  )
}
