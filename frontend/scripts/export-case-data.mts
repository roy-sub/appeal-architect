// Regenerates backend/app/data.py from lib/case-data.ts so both sides share one source.
// Run: npm run export:data   (Node ≥22.6, uses --experimental-strip-types)
import { writeFileSync } from "node:fs";
import * as d from "../lib/case-data.ts";

const names: Record<string, string> = {
  claim: "CLAIM", args: "ARGS", cases: "CASES", facts: "FACTS",
  roadSteps: "ROAD_STEPS", evidence: "EVIDENCE", letterParas: "LETTER_PARAS",
};
const py = (v: unknown) =>
  JSON.stringify(v, null, 4).replace(/\btrue\b/g, "True").replace(/\bfalse\b/g, "False").replace(/\bnull\b/g, "None");

let out = '"""Demo case data. Generated from frontend/lib/case-data.ts by `npm run export:data` — do not edit."""\n\nDEMO_CLAIM = "CLM-4471902"\n\n';
for (const [k, v] of Object.entries(names)) out += `${v} = ${py((d as Record<string, unknown>)[k])}\n\n`;
writeFileSync(new URL("../../backend/app/data.py", import.meta.url), out);
console.log("wrote backend/app/data.py");
