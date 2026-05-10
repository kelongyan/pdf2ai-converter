import { useCallback, useState } from "react"
import { Upload } from "lucide-react"
import { motion } from "framer-motion"
import { uploadFile } from "@/lib/api"

interface FileUploadProps {
  onUploaded: (fileId: string, fileName: string) => void
}

export function FileUpload({ onUploaded }: FileUploadProps) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)

  const handleFiles = useCallback(async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]
    if (!file.name.toLowerCase().endsWith(".pdf")) return

    setUploading(true)
    try {
      const result = await uploadFile(file)
      onUploaded(result.file_id, file.name)
    } catch (e) {
      console.error("Upload failed:", e)
    } finally {
      setUploading(false)
    }
  }, [onUploaded])

  return (
    <motion.div
      className={`relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors cursor-pointer ${
        dragging
          ? "border-blue-500 bg-blue-500/5"
          : "border-[hsl(var(--border))] hover:border-[hsl(var(--muted-foreground))]"
      }`}
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => { e.preventDefault(); setDragging(false); handleFiles(e.dataTransfer.files) }}
      onClick={() => {
        const input = document.createElement("input")
        input.type = "file"
        input.accept = ".pdf"
        input.onchange = () => handleFiles(input.files)
        input.click()
      }}
      animate={{ scale: dragging ? 1.02 : 1 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Upload className="h-10 w-10 text-[hsl(var(--muted-foreground))] mb-4" />
      <p className="text-sm text-[hsl(var(--muted-foreground))]">
        {uploading ? "上传中..." : "拖拽 PDF 文件到此处，或点击选择文件"}
      </p>
    </motion.div>
  )
}
