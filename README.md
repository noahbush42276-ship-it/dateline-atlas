# Dateline Atlas

World news on a relief globe. Twice a day (5:52 AM and 5:52 PM New York time) a news sweep reads about 50 outlets in 17 languages, translates the headlines, groups reports of the same event, and scores each story for reliability and for how differently outlets frame it. The sweep runs on Noah's PC with a local AI model (EMA, using Gemma); when the PC misses one, Claude runs it instead. The app's Sources tab says which ran the latest sweep.

This repository is the installable phone app. It is a web app (PWA): Chrome installs it like any other Android app, it opens full screen from its own icon, and it keeps working offline with the last sweep it downloaded.

## Install on Android

1. Open the site in Chrome: `https://noahbush42276-ship-it.github.io/dateline-atlas/`
2. Tap the **⋮** menu, then **Install app** (on some phones: **Add to Home screen → Install**).
3. Atlas appears in your app drawer. Open it once while online so it saves the stories for offline use.

### Want an APK file instead?

1. Go to **pwabuilder.com** on a computer and paste the site address.
2. Choose **Package for stores → Android → Generate**, then download the zip.
3. Copy the `.apk` inside it to your phone and open it. Android asks you to allow installs from that app (your file manager or browser) the first time.

The APK is the same app with the same automatic updates. Publishing it on Google Play also needs a Play developer account.

## How the news updates

- `data/feed.json` holds every current story plus the latest sweep's status.
- After each sweep, `data/feed.json` is replaced with the new stories: by Wire, the news agent in Local HQ on Noah's PC, or by Claude's fallback sweep (built with `tools/make_feed.py` from an export of the Atlas database).
- The app checks for a new feed when you open it and every 15 minutes while it is open, and shows "New sweep landed" when one arrives. Offline, it shows the saved sweep and the header reads **Saved**.
- National and international stories stay for 30 days after the event; local and regional ones for 7.

Everything in this repository is public, including the stories in `data/feed.json`.

## Publishing this folder by hand

1. On github.com, create a **public** repository named `dateline-atlas`.
2. **Add file → Upload files**, and drag in everything in this folder (keep the `data`, `icons`, `lib` and `tools` folders).
3. **Settings → Pages → Build and deployment**: Source **Deploy from a branch**, branch **main**, folder **/ (root)**, then **Save**.
4. The site is live at the address above within a couple of minutes.

## Files

| Path | What it is |
| --- | --- |
| `index.html` | The app: globe, story strip, Stories / Bias / Sources tabs, story reports |
| `data/feed.json` | The stories, replaced after every sweep |
| `sw.js` | Service worker: offline copy of the app and the last feed |
| `manifest.webmanifest`, `icons/` | What Android uses to install the app |
| `earth-relief-2k.jpg`, `earth-relief-4k.jpg` | Globe texture (the 4k one loads only when zoomed in) |
| `lib/d3.min.js` | D3 7.9.0 for the globe |
| `tools/make_feed.py` | Builds `data/feed.json` from a database export |

## Credits

Land relief and vegetation tints: Natural Earth shaded relief (public domain). Ocean depth: NOAA ETOPO global relief model; seafloor ridges and trenches: NOAA ETOPO1 (public domain). Coastlines, lakes and borders: Natural Earth 1:110m and 1:50m (public domain). D3 by Mike Bostock, ISC license (`lib/d3-LICENSE.txt`). Headlines belong to the outlets that published them; every report links to its original. Translations, reliability scores and framing notes are an AI model's judgments (EMA's or Claude's) and can be wrong.
