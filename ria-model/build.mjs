/* Assembles the published page from the SAME engine and inputs the verifier runs.
   Nothing is retyped: inputs.json and engine.mjs are inlined verbatim (minus the
   ES module `export` keywords), so page and workbook cannot drift apart.       */
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
const dir = path.dirname(fileURLToPath(import.meta.url));
const read = f => fs.readFileSync(path.join(dir, f), "utf8");

const inputs = read("inputs.json");
const engine = read("engine.mjs").replace(/^export\s+/gm, "");
const parts = ["app.a.js", "app.b.js", "app.c.js", "app.d.js", "app.e.js"].map(read).join("\n");

const out = [
  read("page.head.html"),
  read("page.body.html"),
  "<script>",
  "/* ---- canonical inputs (inlined from inputs.json) ---- */",
  "const INPUTS = " + inputs.trim() + ";",
  "/* ---- engine (inlined from engine.mjs, identical to the tested module) ---- */",
  engine,
  "/* ---- page ---- */",
  parts,
  "<" + "/script>",
].join("\n");

const target = path.join(dir, "dist", "operations-capacity-model.html");
fs.mkdirSync(path.dirname(target), { recursive: true });
fs.writeFileSync(target, out);
console.log("built", target, (out.length / 1024).toFixed(0) + " KB");
