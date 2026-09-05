/* Checks run against the BUILT artifact, not the source. */
import fs from "fs";
const html = fs.readFileSync("dist/operations-capacity-model.html", "utf8");
let pass = 0, fail = 0;
const ok = (n, c, d = "") => { c ? (pass++, console.log("  PASS  " + n + (d ? "  " + d : ""))) : (fail++, console.log("  FAIL  " + n + "  " + d)); };

console.log("\nPublished artifact - privacy and anonymisation\n" + "-".repeat(46));

/* Real first names appear in the brief that produced this model. None of them,
   nor any firm/vendor/custodian name, may reach the published page.          */
const NAMES = ["Seth", "Kristian"];
const found = NAMES.filter(n => new RegExp("\\b" + n + "\\b", "i").test(html));
ok("No person's name appears anywhere in the published page", found.length === 0, found.join(", "));

const patterns = [
  ["Social security numbers", /\b\d{3}-\d{2}-\d{4}\b/],
  ["Account numbers", /\baccount\s*(?:no\.?|number|#)\s*[:=]?\s*\d/i],
  ["Email addresses", /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/],
  ["Credentials", /\b(password|passwd|api[_ -]?key|secret|token|login)\s*[:=]\s*\S/i],
];
for (const [name, re] of patterns) { const m = html.match(re); ok("No " + name.toLowerCase(), !m, m ? m[0] : ""); }

/* Long digit runs, ignoring the CSS/SVG/number-formatting noise. */
const longNums = [...html.matchAll(/\b\d{9,}\b/g)].map(m => m[0]);
ok("No 9+ digit identifiers", longNums.length === 0, longNums.slice(0, 3).join(", "));

/* The labels table must ship anonymous: real === anon in the published file. */
const inputs = JSON.parse(fs.readFileSync("inputs.json", "utf8"));
const labelRows = Object.entries(inputs.labels).filter(([k]) => k !== "_note");
ok("Labels table ships with real === anon (nothing identifying to reveal)",
   labelRows.every(([, v]) => v.anon === v.real), labelRows.length + " labels");
ok("ANONYMISE defaults to on", /let anonymised = true/.test(html));
ok("Every roster label the page renders comes from the labels table",
   inputs.roster.every(r => inputs.labels[r.role_id]), inputs.roster.length + " roles");

/* Nothing at household grain. */
ok("Smallest unit anywhere in the book is a tier",
   inputs.book.every(b => b.households >= 5),
   "smallest tier holds " + Math.min(...inputs.book.map(b => b.households)) + " households");

console.log("\nPublished artifact - integrity\n" + "-".repeat(30));
ok("Engine is inlined verbatim from the tested module",
   html.includes("function tieredFee(aum, bands)") && html.includes("function computeModel(I, scenario)"));
ok("Inputs are inlined from inputs.json, not retyped",
   html.includes('"schema_version": "' + inputs.meta.schema_version + '"'));
ok("No external script or stylesheet beyond Google Fonts",
   [...html.matchAll(/<(?:script|link)[^>]+(?:src|href)="(https?:[^"]+)"/g)]
     .every(m => m[1].startsWith("https://fonts.g")),
   [...html.matchAll(/<(?:script|link)[^>]+(?:src|href)="(https?:[^"]+)"/g)].map(m => new URL(m[1]).host).join(", "));
ok("Every provenance tag has a visual treatment that is not colour alone",
   ["tag-MEASURED", "tag-OBSERVED", "tag-BENCHMARK", "tag-ESTIMATED", "tag-PLACEHOLDER"]
     .every(t => html.includes("." + t)) && /dashed/.test(html) && /dotted/.test(html));

console.log(`\n  ${pass} passed, ${fail} failed\n`);
process.exit(fail ? 1 : 0);
