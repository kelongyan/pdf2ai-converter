import { useState, useCallback } from "react"
import { FileUpload } from "@/components/file-upload"
import { ConvertOptions } from "@/components/convert-options"
import { TaskList } from "@/components/task-list"
import { useTaskStore } from "@/stores/task-store"
import { startConvert } from "@/lib/api"

export default function Home() {
  const [fileId, setFileId] = useState<string | null>(null)
  const [fileName, setFileName] = useState("")
  const [outputFormat, setOutputFormat] = useState("markdown")
  const [mode, setMode] = useState("precise")
  const [resume, setResume] = useState(false)
  const addTask = useTaskStore((s) => s.addTask)

  const handleUploaded = useCallback((id: string, name: string) => {
    setFileId(id)
    setFileName(name)
  }, [])

  const handleConvert = useCallback(async () => {
    if (!fileId) return
    try {
      const task = await startConvert({ file_id: fileId, output_format: outputFormat, mode, resume })
      addTask({ ...task, progress: task.progress || { phase: "pending", current_page: 0, total_pages: 0, cached_pages: 0, failed_pages: [], message: "" } })
      setFileId(null)
      setFileName("")
    } catch (e) {
      console.error("Convert failed:", e)
    }
  }, [fileId, outputFormat, mode, resume, addTask])

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold tracking-tight">PDF2AI Converter</h1>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">上传 PDF 文件，转换为 Markdown 或 Word</p>
      </div>

      <FileUpload onUploaded={handleUploaded} />

      {fileId && (
        <p className="text-sm text-green-600">
          已选择：{fileName}
        </p>
      )}

      <ConvertOptions
        outputFormat={outputFormat}
        setOutputFormat={setOutputFormat}
        mode={mode}
        setMode={setMode}
        resume={resume}
        setResume={setResume}
        onConvert={handleConvert}
        disabled={!fileId}
      />

      <TaskList />
    </div>
  )
}
