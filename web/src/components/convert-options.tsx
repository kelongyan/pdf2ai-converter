import { motion, AnimatePresence } from "framer-motion"
import { Button } from "@/components/ui/button"

interface ConvertOptionsProps {
  outputFormat: string
  setOutputFormat: (v: string) => void
  mode: string
  setMode: (v: string) => void
  resume: boolean
  setResume: (v: boolean) => void
  onConvert: () => void
  disabled: boolean
}

export function ConvertOptions({
  outputFormat, setOutputFormat,
  mode, setMode,
  resume, setResume,
  onConvert, disabled,
}: ConvertOptionsProps) {
  return (
    <div className="space-y-4 rounded-lg border border-[hsl(var(--border))] p-6">
      <div className="flex items-center gap-6">
        <span className="text-sm font-medium">输出格式</span>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="radio" name="format" checked={outputFormat === "markdown"} onChange={() => setOutputFormat("markdown")} className="accent-blue-500" />
          Markdown
        </label>
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="radio" name="format" checked={outputFormat === "word"} onChange={() => setOutputFormat("word")} className="accent-blue-500" />
          Word
        </label>
      </div>

      <AnimatePresence>
        {outputFormat === "word" && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="overflow-hidden"
          >
            <div className="flex items-center gap-6">
              <span className="text-sm font-medium">转换模式</span>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="mode" checked={mode === "fast"} onChange={() => setMode("fast")} className="accent-blue-500" />
                快速（仅内容）
              </label>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="radio" name="mode" checked={mode === "precise"} onChange={() => setMode("precise")} className="accent-blue-500" />
                精确（保留样式）
              </label>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex items-center gap-6">
        <label className="flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={resume} onChange={(e) => setResume(e.target.checked)} className="accent-blue-500" />
          恢复模式（仅补处理失败页）
        </label>
      </div>

      <Button onClick={onConvert} disabled={disabled} className="w-full">
        开始转换
      </Button>
    </div>
  )
}
