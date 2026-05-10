import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { getProfiles, createProfile, deleteProfile } from "@/lib/api"
import { Trash2 } from "lucide-react"

interface Profile {
  name: string
  api_url: string
  model: string
  dpi: number
  chunk_size: number
}

export default function Settings() {
  const [profiles, setProfiles] = useState<Profile[]>([])
  const [form, setForm] = useState({ name: "", api_url: "https://api.openai.com/v1", api_key: "", model: "gpt-4o", dpi: 150, chunk_size: 10 })

  const load = async () => {
    const data = await getProfiles()
    setProfiles(data)
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.name || !form.api_key) return
    await createProfile(form)
    setForm({ name: "", api_url: "https://api.openai.com/v1", api_key: "", model: "gpt-4o", dpi: 150, chunk_size: 10 })
    load()
  }

  const handleDelete = async (name: string) => {
    await deleteProfile(name)
    load()
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold tracking-tight">设置</h1>

      <Card>
        <CardHeader><CardTitle>已保存的配置</CardTitle></CardHeader>
        <CardContent>
          {profiles.length === 0 ? (
            <p className="text-sm text-[hsl(var(--muted-foreground))]">暂无配置，请创建一个</p>
          ) : (
            <div className="space-y-2">
              {profiles.map((p) => (
                <div key={p.name} className="flex items-center justify-between rounded-md border border-[hsl(var(--border))] p-3">
                  <div>
                    <p className="text-sm font-medium">{p.name}</p>
                    <p className="text-xs text-[hsl(var(--muted-foreground))]">{p.model} · DPI {p.dpi}</p>
                  </div>
                  <Button variant="ghost" size="icon" onClick={() => handleDelete(p.name)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>创建新配置</CardTitle></CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="配置名称" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
            <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="API URL" value={form.api_url} onChange={(e) => setForm({ ...form, api_url: e.target.value })} />
            <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="API Key" type="password" value={form.api_key} onChange={(e) => setForm({ ...form, api_key: e.target.value })} />
            <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="模型 ID" value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
            <div className="grid grid-cols-2 gap-4">
              <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="DPI" type="number" value={form.dpi} onChange={(e) => setForm({ ...form, dpi: Number(e.target.value) })} />
              <input className="rounded-md border border-[hsl(var(--input))] bg-transparent px-3 py-2 text-sm" placeholder="分段大小" type="number" value={form.chunk_size} onChange={(e) => setForm({ ...form, chunk_size: Number(e.target.value) })} />
            </div>
            <Button onClick={handleCreate}>保存配置</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
