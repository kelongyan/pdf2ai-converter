import { create } from "zustand"

export interface Task {
  id: string
  file_name: string
  output_format: string
  mode?: string
  status: "pending" | "processing" | "completed" | "failed" | "cancelled"
  progress: {
    phase: string
    current_page: number
    total_pages: number
    cached_pages: number
    failed_pages: number[]
    message: string
  }
  created_at: string
  completed_at?: string
  error?: string
}

interface TaskStore {
  tasks: Task[]
  setTasks: (tasks: Task[]) => void
  addTask: (task: Task) => void
  updateTask: (taskId: string, updates: Partial<Task>) => void
  removeTask: (taskId: string) => void
}

export const useTaskStore = create<TaskStore>((set) => ({
  tasks: [],
  setTasks: (tasks) => set({ tasks }),
  addTask: (task) => set((s) => ({ tasks: [task, ...s.tasks] })),
  updateTask: (taskId, updates) =>
    set((s) => ({
      tasks: s.tasks.map((t) => (t.id === taskId ? { ...t, ...updates } : t)),
    })),
  removeTask: (taskId) =>
    set((s) => ({ tasks: s.tasks.filter((t) => t.id !== taskId) })),
}))
