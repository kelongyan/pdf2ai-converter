import { BrowserRouter, Routes, Route, Link } from "react-router-dom"
import { Settings, Sun, Moon } from "lucide-react"
import { useProgressWebSocket } from "@/hooks/use-websocket"
import { useTheme } from "@/hooks/use-theme"
import { Button } from "@/components/ui/button"
import Home from "@/pages/home"
import SettingsPage from "@/pages/settings"

function Layout() {
  useProgressWebSocket()
  const { theme, toggle } = useTheme()

  return (
    <div className="min-h-screen bg-[hsl(var(--background))] text-[hsl(var(--foreground))]">
      <header className="border-b border-[hsl(var(--border))]">
        <div className="mx-auto flex max-w-2xl items-center justify-between px-6 py-3">
          <Link to="/" className="text-sm font-semibold">PDF2AI</Link>
          <div className="flex items-center gap-1">
            <Button variant="ghost" size="icon" onClick={toggle} aria-label="切换主题">
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
            <Link to="/settings" className="inline-flex h-9 w-9 items-center justify-center rounded-md text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))] transition-colors">
              <Settings className="h-4 w-4" />
            </Link>
          </div>
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
