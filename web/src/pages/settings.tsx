import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { getProfiles, createProfile, deleteProfile, testConnection } from "@/lib/api"
import { Trash2, CheckCircle2, XCircle, Loader2 } from "lucide-react"

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
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms: number } | null>(null)
  const [testing, setTesting] = useState(false)

  const load = async () => {
    const data = await getProfiles()
    setProfiles(data)
  }

  useEffect(() => { load() }, [])

  const handleCreate = async () => {
    if (!form.name || !form.api_key) return
    await createProfile(form)
    setForm({ name: "", api_url: "https://api.openai.com/v1", api_key: "", model: "gpt-4o", dpi: 150, chunk_size: 10 })
    setTestResult(null)
    load()
  }

  const handleDelete = async (name: string) => {
    await deleteProfile(name)
    load()
  }

  const handleTest = async () => {
    if (!form.api_url || !form.api_key || !form.model) return
    setTesting(true)
    setTestResult(null)
    try {
      const result = await testConnection({ api_url: form.api_url, api_key: form.api_key, model: form.model })
      setTestResult(result)
    } catch {
      setTestResult({ success: false, message: "请求失败", latency_ms: 0 })
    } finally {
      setTesting(false)
    }
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

            <div className="flex gap-3">
              <Button onClick={handleCreate} className="flex-1">保存配置</Button>
              <Button variant="outline" onClick={handleTest} disabled={testing || !form.api_key}>
                {testing ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : null}
                测试连接
              </Button>
            </div>

            {testResult && (
              <div className={`flex items-center gap-2 rounded-md p-3 text-sm ${testResult.success ? "bg-green-500/10 text-green-600" : "bg-red-500/10 text-red-600"}`}>
                {testResult.success ? <CheckCircle2 className="h-4 w-4" /> : <XCircle className="h-4 w-4" />}
                <span>{testResult.message}</span>
                {testResult.success && <span className="text-xs opacity-70">({testResult.latency_ms}ms)</span>}
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}