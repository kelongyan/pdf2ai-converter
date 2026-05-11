import { useEffect, useRef } from "react"
import { useTaskStore } from "@/stores/task-store"

export function useProgressWebSocket() {
  const ws = useRef<WebSocket | null>(null)
  const updateTask = useTaskStore((s) => s.updateTask)
  const reconnectDelay = useRef(1000)

  useEffect(() => {
    function connect() {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:"
      const host = window.location.host
      ws.current = new WebSocket(`${protocol}//${host}/api/ws/progress`)

      ws.current.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        const { task_id, type, data } = msg

        if (type === "progress") {
          updateTask(task_id, {
            status: "processing",
            progress: {
              phase: data.phase || "processing",
              current_page: data.current_page ?? 0,
              total_pages: data.total_pages ?? 0,
              cached_pages: data.cached_pages ?? 0,
              failed_pages: data.failed_pages ?? [],
              message: data.message || "",
            },
          })
        } else if (type === "completed") {
          updateTask(task_id, {
            status: "completed",
            progress: {
              phase: "done",
              message: data.message || "转换完成",
              current_page: 0,
              total_pages: 0,
              cached_pages: 0,
              failed_pages: [],
            },
          })
        } else if (type === "error") {
          updateTask(task_id, { status: "failed", error: data.message })
        }
      }

      ws.current.onopen = () => {
        reconnectDelay.current = 1000
      }

      ws.current.onclose = () => {
        setTimeout(connect, reconnectDelay.current)
        reconnectDelay.current = Math.min(reconnectDelay.current * 2, 30000)
      }
    }

    connect()
    return () => {
      ws.current?.close()
    }
  }, [updateTask])
}
