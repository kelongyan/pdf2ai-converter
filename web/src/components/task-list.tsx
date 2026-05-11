import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Download, Trash2, Loader2, CheckCircle2, XCircle, Eye } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ProgressBar } from "@/components/progress-bar"
import { MarkdownPreview } from "@/components/markdown-preview"
import { type Task, useTaskStore } from "@/stores/task-store"
import { getDownloadUrl, deleteTask } from "@/lib/api"

const statusConfig = {
  pending: { icon: Loader2, label: "等待中", color: "text-yellow-500" },
  processing: { icon: Loader2, label: "转换中", color: "text-blue-500" },
  completed: { icon: CheckCircle2, label: "完成", color: "text-green-500" },
  failed: { icon: XCircle, label: "失败", color: "text-red-500" },
  cancelled: { icon: XCircle, label: "已取消", color: "text-gray-500" },
}

export function TaskList() {
  const tasks = useTaskStore((s) => s.tasks)
  const removeTask = useTaskStore((s) => s.removeTask)

  if (tasks.length === 0) return null

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-[hsl(var(--muted-foreground))]">任务列表</h3>
      <AnimatePresence mode="popLayout">
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} onDelete={() => { deleteTask(task.id); removeTask(task.id) }} />
        ))}
      </AnimatePresence>
    </div>
  )
}

function TaskCard({ task, onDelete }: { task: Task; onDelete: () => void }) {
  const [showPreview, setShowPreview] = useState(false)
  const cfg = statusConfig[task.status] || statusConfig.pending
  const Icon = cfg.icon
  const canPreview = task.status === "completed" && task.output_format === "markdown"

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, x: -100 }}
      className="rounded-lg border border-[hsl(var(--border))] p-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3 min-w-0">
          <Icon className={`h-5 w-5 shrink-0 ${cfg.color} ${task.status === "processing" ? "animate-spin" : ""}`} />
          <div className="min-w-0">
            <p className="text-sm font-medium truncate">{task.file_name}</p>
            <p className="text-xs text-[hsl(var(--muted-foreground))]">
              {task.output_format === "word" ? `Word / ${task.mode}` : "Markdown"}
              {task.error ? ` · ${task.error}` : ""}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {canPreview && (
            <Button variant="ghost" size="icon" onClick={() => setShowPreview(!showPreview)}>
              <Eye className="h-4 w-4" />
            </Button>
          )}
          {task.status === "completed" && (
            <a href={getDownloadUrl(task.id)} download>
              <Button variant="ghost" size="icon"><Download className="h-4 w-4" /></Button>
            </a>
          )}
          <Button variant="ghost" size="icon" onClick={onDelete}><Trash2 className="h-4 w-4" /></Button>
        </div>
      </div>

      {task.status === "processing" && task.progress.total_pages > 0 && (
        <ProgressBar
          currentPage={task.progress.current_page}
          totalPages={task.progress.total_pages}
          cachedPages={task.progress.cached_pages}
          message={task.progress.message}
        />
      )}

      {canPreview && <MarkdownPreview taskId={task.id} visible={showPreview} />}
    </motion.div>
  )
}
