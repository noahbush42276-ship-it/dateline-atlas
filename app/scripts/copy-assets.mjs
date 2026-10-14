// Copies the parts of the website the app needs next to www/index.html: the d3 library and the relief images.
// www/index.html itself is built by store/build_store.py (in the Atlas mobile build folder) and committed here.
import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const site = dirname(app);
mkdirSync(join(app, "www", "lib"), { recursive: true });
for (const f of ["lib/d3.min.js", "lib/d3-LICENSE.txt", "earth-relief-2k.jpg", "earth-relief-4k.jpg"]) {
  copyFileSync(join(site, f), join(app, "www", f));
  console.log("copied", f);
}
