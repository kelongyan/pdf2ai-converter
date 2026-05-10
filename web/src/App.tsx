import { BrowserRouter, Routes, Route, Link } from "react-router-dom"
import { Settings } from "lucide-react"
import { useProgressWebSocket } from "@/hooks/use-websocket"
import Home from "@/pages/home"
import SettingsPage from "@/pages/settings"

function Layout() {
  useProgressWebSocket()

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <header className="border-b border-[hsl(var(--border))]">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-6 py-3">
          <Link to="/" className="text-sm font-semibold">PDF2AI</Link>
          <Link to="/settings" className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] transition-colors">
            <Settings className="h-5 w-5" />
          </Link>
        </div>
      </header>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <Layout />
    </BrowserRouter>
  )
}
