# Dateline Atlas phone apps (Android and iPhone)

The store apps are the Dateline Atlas web app inside a [Capacitor](https://capacitorjs.com/) shell, built in the
cloud by GitHub Actions, so no Mac or Android Studio is needed.

- **Free:** the top 80 stories, headline search, one banner ad at the bottom (Google AdMob; it refreshes on its own).
- **Upgrade:** one in-app purchase, product ID `atlas_upgrade` (non-consumable): every story (300+), deep search
  with filters by country and reliability, no ad. $1.99 on Google Play, $2.99 on the App Store (prices are set in
  each store's console; the app shows whatever the store says).
- **News:** `data/store-feed.json` on this site, built only from the GDELT Project's open index (free for
  commercial use with credit). The free web app keeps using `data/feed.json`.
- **Weather:** optional, US only, from the National Weather Service (free for any use). Location is approximate
  and asked for only when the person turns weather on.

## What's here

| Path | What it is |
| --- | --- |
| `www/index.html` | The app's page: built by `store/build_store.py` from the shared Atlas template (don't edit by hand) |
| `www/store-config.js` | Written from `store-config.json` at build time |
| `store-config.json` | App ID, version, Upgrade product ID, free-tier size, AdMob IDs, policy links |
| `native-entry.js` | Bundled into `www/native.bundle.js`: the AdMob, Geolocation and purchases plugins |
| `scripts/configure-native.mjs` | Fills in the generated Android and iOS projects: permissions, AdMob app ID, version, signing |
| `scripts/copy-assets.mjs` | Copies the d3 library and relief images from the site into `www/` |
| `assets/` | Icon and splash sources; `@capacitor/assets` makes every size from them |
| `../.github/workflows/app-android.yml` | Android build: signed `.aab` for Google Play, or a test `.apk` before the key exists |
| `../.github/workflows/app-ios.yml` | iPhone build on a cloud Mac: uploads to App Store Connect (TestFlight), or a compile check before the keys exist |

The `android/` and `ios/` projects are generated fresh on every build, so they aren't kept here.

## Building

Actions tab → **Phone app - Android** or **Phone app - iPhone** → **Run workflow**. Pushing a tag named
`app-v…` (for example `app-v1.0.0`) runs both.

- Android: the result is under the run's **Artifacts**. With the signing secrets it's
  `app-release.aab`, which you upload in Play Console; without them it's `app-debug.apk`, which you can install on
  an Android phone to try.
- iPhone: with the App Store secrets, the build goes straight to App Store Connect and shows up in TestFlight
  after Apple processes it (usually 5–30 minutes).

The build number is the workflow's run number, so every build counts up. Change `version` in
`store-config.json` for each release you send to the stores.

## Repository secrets

Settings → Secrets and variables → Actions → **New repository secret**. You add these yourself; nothing in this
repository contains them.

| Secret | Used for |
| --- | --- |
| `ANDROID_KEYSTORE_BASE64` | Your upload key (`.jks` file), base64-encoded |
| `ANDROID_KEYSTORE_PASSWORD` | The keystore password |
| `ANDROID_KEY_ALIAS` | The key alias (for example `upload`) |
| `ANDROID_KEY_PASSWORD` | The key password |
| `APPSTORE_API_KEY_ID` | App Store Connect API key ID |
| `APPSTORE_API_ISSUER_ID` | App Store Connect issuer ID |
| `APPSTORE_API_PRIVATE_KEY` | The contents of the `AuthKey_….p8` file |
| `APPLE_TEAM_ID` | Your 10-character Apple Developer team ID |

## Going live with ads

`store-config.json` starts with `"adsTesting": true` and Google's sample AdMob IDs, which show test ads only.
When your AdMob account has the two apps and a banner ad unit for each, put your app IDs and banner unit IDs in
`store-config.json`, set `"adsTesting": false`, and run both builds again. In AdMob, set each banner unit's
refresh rate to 60 seconds.
