// Fills in the native projects that `npx cap add android|ios` generates, from store-config.json:
// the AdMob app ID, the location / tracking / billing permissions and their explanations, the version, and
// (Android) release signing from environment variables the workflow sets from repository secrets.
//
// node scripts/configure-native.mjs www          writes www/store-config.js (the page's settings)
// node scripts/configure-native.mjs android      patches android/ (run after `npx cap add android`)
// node scripts/configure-native.mjs ios          patches ios/ (run after `npx cap add ios`)
import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const app = dirname(dirname(fileURLToPath(import.meta.url)));
const cfg = JSON.parse(readFileSync(join(app, "store-config.json"), "utf8"));
const target = process.argv[2];
const read = (p) => readFileSync(join(app, p), "utf8");
const write = (p, s) => { writeFileSync(join(app, p), s); console.log("patched", p); };
function once(text, needle, insert, where = "before") {
  if (text.includes(insert.trim())) return text;                 // already there (re-runs are safe)
  const i = text.indexOf(needle);
  if (i < 0) throw new Error("could not find " + JSON.stringify(needle.slice(0, 60)));
  return where === "before" ? text.slice(0, i) + insert + text.slice(i) : text.slice(0, i + needle.length) + insert + text.slice(i + needle.length);
}
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const LOCATION_WHY = "Dateline Atlas shows the weather where you are. Your location stays on your phone and is only sent to the US National Weather Service to look up the forecast. You can say no: everything else works the same.";
const TRACKING_WHY = "The free version shows one banner ad. Allowing tracking lets that ad be more relevant to you. Premium removes the ad.";

if (target === "www") {
  const page = Object.fromEntries(["premium", "freeStories", "prices", "adsTesting", "admob", "privacyUrl", "supportUrl", "termsUrl", "appleTermsUrl"].map((k) => [k, cfg[k]]));
  writeFileSync(join(app, "www", "store-config.js"), "window.ATLAS_STORE = " + JSON.stringify(page) + ";\n");
  console.log("wrote www/store-config.js");
} else if (target === "android") {
  const man = "android/app/src/main/AndroidManifest.xml";
  let m = read(man);
  m = once(m, "<application", [
    '<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />',
    '    <uses-permission android:name="com.android.vending.BILLING" />',
    '    <uses-feature android:name="android.hardware.location" android:required="false" />',
    "", "    "].join("\n"));
  m = once(m, "</application>", '    <meta-data android:name="com.google.android.gms.ads.APPLICATION_ID" android:value="@string/admob_app_id" />\n    ');
  write(man, m);

  const strings = "android/app/src/main/res/values/strings.xml";
  let s = read(strings).replace(/\s*<string name="admob_app_id">[^<]*<\/string>/, "");
  s = once(s, "</resources>", `    <string name="admob_app_id">${esc(cfg.admob.android.appId)}</string>\n`);
  write(strings, s);

  const kts = existsSync(join(app, "android/app/build.gradle.kts"));
  const gradle = kts ? "android/app/build.gradle.kts" : "android/app/build.gradle";
  let g = read(gradle);
  const code = Number(process.env.VERSION_CODE || 1), name = cfg.version || "1.0.0";
  g = kts ? g.replace(/versionCode\s*=\s*\d+/, `versionCode = ${code}`).replace(/versionName\s*=\s*"[^"]*"/, `versionName = "${name}"`)
          : g.replace(/versionCode\s+\d+/, `versionCode ${code}`).replace(/versionName\s+"[^"]*"/, `versionName "${name}"`);
  if (process.env.ANDROID_KEYSTORE_PATH) {
    const signing = kts ? `
    signingConfigs {
        create("release") {
            storeFile = file(System.getenv("ANDROID_KEYSTORE_PATH"))
            storePassword = System.getenv("ANDROID_KEYSTORE_PASSWORD")
            keyAlias = System.getenv("ANDROID_KEY_ALIAS")
            keyPassword = System.getenv("ANDROID_KEY_PASSWORD")
        }
    }
` : `
    signingConfigs {
        release {
            storeFile file(System.getenv("ANDROID_KEYSTORE_PATH"))
            storePassword System.getenv("ANDROID_KEYSTORE_PASSWORD")
            keyAlias System.getenv("ANDROID_KEY_ALIAS")
            keyPassword System.getenv("ANDROID_KEY_PASSWORD")
        }
    }
`;
    if (!g.includes("ANDROID_KEYSTORE_PATH")) {
      g = g.replace(/android\s*\{\n/, (a) => a + signing);
      g = g.replace(/buildTypes\s*\{\s*(getByName\("release"\)|release)\s*\{\n/, (a) => a + (kts ? '            signingConfig = signingConfigs.getByName("release")\n' : "            signingConfig signingConfigs.release\n"));
      if (!/signingConfig\s*(=\s*)?signingConfigs/.test(g)) throw new Error("could not add release signing to " + gradle);
    }
  }
  write(gradle, g);
} else if (target === "ios") {
  const plist = "ios/App/App/Info.plist";
  let p = read(plist);
  const keys = {
    NSLocationWhenInUseUsageDescription: LOCATION_WHY,
    NSLocationAlwaysAndWhenInUseUsageDescription: LOCATION_WHY,
    NSUserTrackingUsageDescription: TRACKING_WHY,
    GADApplicationIdentifier: cfg.admob.ios.appId
  };
  let add = "";
  for (const [k, v] of Object.entries(keys)) {
    p = p.replace(new RegExp(`\\s*<key>${k}</key>\\s*<string>[^<]*</string>`), "");
    add += `\t<key>${k}</key>\n\t<string>${esc(v)}</string>\n`;
  }
  if (!p.includes("<key>ITSAppUsesNonExemptEncryption</key>")) add += "\t<key>ITSAppUsesNonExemptEncryption</key>\n\t<false/>\n";
  if (!p.includes("<key>SKAdNetworkItems</key>")) {
    // Google's own SKAdNetwork ID; Google's iOS guide lists the third-party buyers' IDs that can be added after it
    add += "\t<key>SKAdNetworkItems</key>\n\t<array>\n\t\t<dict>\n\t\t\t<key>SKAdNetworkIdentifier</key>\n\t\t\t<string>cstr6suwn9.skadnetwork</string>\n\t\t</dict>\n\t</array>\n";
  }
  const end = p.lastIndexOf("</dict>");
  p = p.slice(0, end) + add + p.slice(end);
  write(plist, p);
} else {
  console.error("usage: node scripts/configure-native.mjs www|android|ios");
  process.exit(2);
}
