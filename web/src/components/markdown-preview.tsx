import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeKatex from "rehype-katex"
import rehypeHighlight from "rehype-highlight"
import { getPreview } from "@/lib/api"
import "katex/dist/katex.min.css"

interface MarkdownPreviewProps {
  taskId: string
  visible: boolean
}

export function MarkdownPreview({ taskId, visible }: MarkdownPreviewProps) {
  const [content, setContent] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (visible && content === null) {
      setLoading(true)
      getPreview(taskId)
        .then((res) => setContent(res.content))
        .catch(() => setContent("预览加载失败"))
        .finally(() => setLoading(false))
    }
  }, [visible, taskId, content])

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: "auto", opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="overflow-hidden"
        >
          <div className="mt-3 max-h-96 overflow-y-auto rounded-md border border-[hsl(var(--border))] bg-[hsl(var(--muted))] p-4">
            {loading ? (
              <p className="text-sm text-[hsl(var(--muted-foreground))]">加载中...</p>
            ) : (
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]} rehypePlugins={[rehypeKatex, rehypeHighlight]}>
                  {content || ""}
                </ReactMarkdown>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
