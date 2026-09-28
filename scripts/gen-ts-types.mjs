// Generates TypeScript types from schemas/*.json into apps/web/src/contracts (make schemas).
import { mkdir, readdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { compile } from "json-schema-to-typescript";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const schemasDir = path.join(root, "schemas");
const outDir = path.join(root, "apps", "web", "src", "contracts");

await mkdir(outDir, { recursive: true });
const names = (await readdir(schemasDir)).filter((f) => f.endsWith(".json")).sort();
const exports = [];
for (const file of names) {
  const name = path.basename(file, ".json");
  const schema = JSON.parse(await readFile(path.join(schemasDir, file), "utf8"));
  const ts = await compile(schema, schema.title, {
    bannerComment: `// Generated from schemas/${file} by \`make schemas\`. Do not edit.`,
    additionalProperties: false,
    unreachableDefinitions: true,
    style: { printWidth: 110 },
  });
  await writeFile(path.join(outDir, `${name}.ts`), ts);
  exports.push(`export type * from "./${name}";`);
}
await writeFile(path.join(outDir, "index.ts"), exports.join("\n") + "\n");
console.log(`generated ${names.length} TypeScript contracts into ${path.relative(root, outDir)}`);
