import { useEffect, useRef } from "react"
import { motion } from "framer-motion"

interface ProgressBarProps {
  currentPage: number
  totalPages: number
  cachedPages: number
  message: string
}

export function ProgressBar({ currentPage, totalPages, cachedPages, message }: ProgressBarProps) {
  const percent = totalPages > 0 ? (currentPage / totalPages) * 100 : 0
  const timestamps = useRef<number[]>([])

  useEffect(() => {
    if (currentPage > 0) {
      timestamps.current.push(Date.now())
    }
  }, [currentPage])

  const eta = (() => {
    const ts = timestamps.current
    if (ts.length < 2 || currentPage >= totalPages) return null
    const recent = ts.slice(-6)
    if (recent.length < 2) return null
    const avgMs = (recent[recent.length - 1] - recent[0]) / (recent.length - 1)
    const remaining = totalPages - currentPage
    const etaSeconds = Math.round((avgMs * remaining) / 1000)
    if (etaSeconds < 60) return `${etaSeconds}s`
    return `${Math.floor(etaSeconds / 60)}m ${etaSeconds % 60}s`
  })()

  return (
    <div className="mt-3 space-y-1.5">
      <div className="h-2 w-full overflow-hidden rounded-full bg-[hsl(var(--muted))]">
        <motion.div
          className="h-full rounded-full bg-blue-500"
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
        />
      </div>
      <p className="text-xs text-[hsl(var(--muted-foreground))]">
        {message}
        {cachedPages > 0 && ` · 缓存命中 ${cachedPages} 页`}
        {eta && ` · 预计剩余 ${eta}`}
      </p>
    </div>
  )
}
