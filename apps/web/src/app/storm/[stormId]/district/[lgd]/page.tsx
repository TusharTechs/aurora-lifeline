import fs from "node:fs";
import path from "node:path";
import { CommandMap } from "@/components/CommandMap";
import { STORMS, storm } from "@/lib/storms";

export const dynamicParams = false;

export function generateStaticParams(): Array<{ stormId: string; lgd: string }> {
  const out: Array<{ stormId: string; lgd: string }> = [];
  for (const s of STORMS) {
    const dir = path.join(process.cwd(), "public", "runs", s.defaultRun, "districts");
    if (!fs.existsSync(dir)) continue;
    for (const f of fs.readdirSync(dir))
      if (f.endsWith(".json")) out.push({ stormId: s.stormId, lgd: f.replace(".json", "") });
  }
  return out;
}

export default async function Page({ params }: { params: Promise<{ stormId: string; lgd: string }> }) {
  const { stormId, lgd } = await params;
  const s = storm(stormId);
  if (!s) return <div className="p-8">Unknown storm.</div>;
  return <CommandMap storm={s} runId={s.defaultRun} lgd={lgd} />;
}
