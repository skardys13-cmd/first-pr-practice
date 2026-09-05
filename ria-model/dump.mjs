import fs from "fs";
import * as E from "./engine.mjs";
const I = JSON.parse(fs.readFileSync("inputs.json", "utf8"));
const out = { presets: {} };
for (const [k, p] of Object.entries(E.PRESETS)) {
  out.presets[k] = E.computeModel(I, { consultantPresent: p.consultantPresent, response: p.response });
}
out.today = out.presets.today;
out.fee = [145000, 520000, 5100000].map(a => E.tieredFee(a, I.fee_schedule.bands));
fs.writeFileSync("dist/engine-dump.json", JSON.stringify(out, null, 1));
console.log("dumped");
