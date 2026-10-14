# Putting Dateline Atlas on Google Play and the App Store

Everything in the code is ready: the free version with one banner ad, the Upgrade purchase, the news feed, the
weather, and cloud builds for both phones. What's left is account work that only the account owner can do:
signing up, paying the store fees, accepting agreements, entering bank and tax details, and creating keys.
This guide goes through it in order. Plan on a few hours of clicking spread over about three weeks, because
Google requires a 14-day test before a new personal developer account can publish.

Prices: the Upgrade is **$1.99 on Google Play** and **$2.99 on the App Store**. The app itself is free on both.

---

## 1. Accounts (day 1)

1. **Google Play Console**: <https://play.google.com/console/signup>. Choose a personal account, pay the
   one-time $25, and verify your identity. Google asks for a phone number and a public contact email; that email
   is shown on the store listing.
2. **Apple Developer Program**: <https://developer.apple.com/programs/enroll/> ($99 a year). Enrolling as an
   individual is fine; your name appears as the seller.
3. **AdMob**: <https://admob.google.com/>, signed in with the same Google account. Free.
4. **Getting paid**
   - Google: Play Console → Settings → **Payments profile**, which makes a Google payments merchant account.
     It's needed before you can sell the Upgrade.
   - Apple: App Store Connect → **Business** → accept the **Paid Apps** agreement, then add bank and tax details.
     The Upgrade can't be sold until this shows as active.
   - AdMob: Payments → add bank details. AdMob pays monthly once earnings pass $100.

## 2. The keys the cloud builds need (day 1)

These stay with you. Add them in GitHub: the dateline-atlas repository → **Settings → Secrets and variables →
Actions → New repository secret**. Don't paste them into a chat, an email, or a file in the repository.

### Android upload key

You need Java's `keytool`. If you don't have it, install a JDK in PowerShell with
`winget install EclipseAdoptium.Temurin.21.JDK`, then open a new PowerShell window.

```powershell
cd $HOME\Documents
keytool -genkeypair -v -keystore dateline-upload.jks -alias upload -keyalg RSA -keysize 2048 -validity 10000
```

It asks for a password and your name. Then copy the key as text:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("$HOME\Documents\dateline-upload.jks")) | Set-Clipboard
```

Add four secrets: `ANDROID_KEYSTORE_BASE64` (paste the clipboard), `ANDROID_KEYSTORE_PASSWORD`,
`ANDROID_KEY_ALIAS` (`upload`), `ANDROID_KEY_PASSWORD` (the same password, unless you gave the key its own).
Back up `dateline-upload.jks` somewhere safe. Google Play keeps the real signing key; if this upload key is ever
lost, Google can reset it, but that takes a few days.

### App Store Connect API key

App Store Connect → **Users and Access → Integrations → App Store Connect API → Team Keys → +**. Name it
"GitHub builds" and give it **Admin** access (the build needs it to make its own signing certificate). Download
the `.p8` file; Apple only lets you download it once.

Add four secrets:
- `APPSTORE_API_KEY_ID`: the key ID shown in the list.
- `APPSTORE_API_ISSUER_ID`: the issuer ID shown above the list.
- `APPSTORE_API_PRIVATE_KEY`: open the `.p8` file in Notepad and paste all of it, including the BEGIN and END lines.
- `APPLE_TEAM_ID`: developer.apple.com → Account → Membership details → Team ID (10 characters).

## 3. Register the app with each store (day 1–2)

### Apple

1. developer.apple.com → **Certificates, IDs & Profiles → Identifiers → +** → App IDs → App. Description
   "Dateline Atlas", Bundle ID **Explicit**: `io.github.noahbush42276.datelineatlas`. Leave the capabilities as
   they are (In-App Purchase is on by default).
2. App Store Connect → **Apps → + → New App**: iOS, name "Dateline Atlas" (or "Dateline Atlas: World News" if
   the name is taken), language English (U.S.), that bundle ID, SKU `dateline-atlas`.
3. **Monetization → In-App Purchases → +** → **Non-Consumable**. Reference name "Upgrade", product ID
   **`atlas_upgrade`** (exactly this). Price **$2.99**. Add an English display name ("Upgrade") and description
   ("Every story, deep search and filters, and no ads."). Apple asks for a review screenshot: use
   `review-upgrade-sheet.png` from the store kit.

### Google

1. Play Console → **Create app**: name "Dateline Atlas", English (United States), **App**, **Free**. Accept
   the declarations.
2. **Monetize → Products → One-time products → Create**: product ID **`atlas_upgrade`**, name "Upgrade",
   description as above, price **$1.99** (let Google set the other countries' prices), then **Activate**. Play
   only shows this page after the first build has been uploaded (step 5), so come back to it then.

### AdMob

1. **Apps → Add app** twice: Android and iOS. Say the app isn't on a store yet; you'll link it after it's
   published.
2. In each app, **Ad units → Add → Banner**, named "Bottom banner". Under advanced settings, set **Automatic
   refresh → Custom → 60 seconds**.
3. Copy the four IDs: each app ID (contains `~`) and each banner ad unit ID (contains `/`). These aren't secret.
   Send them to Claude, or put them in `app/store-config.json` yourself and set `"adsTesting": false`. Until
   then the builds show Google's test ads.
4. **Privacy & messaging**: create a **European regulations** message (GDPR) and a **US state regulations**
   message for both apps, and publish them. The app shows them where the law requires.
5. **app-ads.txt** (Google uses it to confirm the ads are yours): create a public GitHub repository named
   exactly `noahbush42276-ship-it.github.io`, add a file `app-ads.txt` containing the line AdMob shows you under
   Apps → View all apps → app-ads.txt (it looks like `google.com, pub-…, DIRECT, f08c47fec0942fa0`), and turn on
   GitHub Pages for it. Use `https://noahbush42276-ship-it.github.io` as the website on both store listings.

## 4. First builds (day 2)

GitHub → dateline-atlas → **Actions**.

- **Phone app - iPhone → Run workflow.** With the App Store secrets in place, it builds, signs and uploads. After
  10–30 minutes the build appears in App Store Connect → TestFlight. Install **TestFlight** on your iPhone and
  try it. In-app purchases in TestFlight are free test purchases.
- **Phone app - Android → Run workflow.** With the Android secrets in place, the run's **Artifacts** has
  `app-release.aab`. Download it (unzip if needed).

## 5. Google's 14-day test (day 2–17)

New personal Play accounts must run a **closed test with at least 12 testers for 14 days in a row** before they
can apply for production.

1. Play Console → **Test and release → Testing → Internal testing** → create a release → upload the `.aab`.
   Add yourself as a tester, install from the opt-in link, and check that the app runs. Then create the
   `atlas_upgrade` product (section 3) and add yourself under **Settings → License testing** so your test
   purchases are free.
2. **Closed testing** → create a track → upload the same `.aab` → add at least 12 testers (a Google Group or a
   list of their Google account emails) → send them the opt-in link. They need to stay opted in for 14 days.
3. Fill in everything under **Policy → App content** while you wait (answers in section 7).
4. After 14 days: **Dashboard → Apply for production**. Google asks a few questions about the test. Approval
   usually takes a few days.

## 6. Store listings

Screenshots, the feature graphic and the Upgrade review screenshot are in the store kit (Claude sent it with
this guide).

| | Google Play | App Store |
| --- | --- | --- |
| Name | Dateline Atlas: World News | Dateline Atlas |
| Short text | World news on a globe, checked for reliability and how it's framed. *(80 max)* | Subtitle: World news on a globe *(30 max)* |
| Category | News & Magazines | News |
| Phone screenshots | `google-play-phone/` (1080 × 1920) | `app-store-iphone-6.9in/` (1320 × 2868) |
| Tablet screenshots | `google-play-tablet-10in/` | `app-store-ipad-13in/` (2064 × 2752) |
| Feature graphic | `google-play-feature-graphic.png` | — |
| Privacy policy | https://noahbush42276-ship-it.github.io/dateline-atlas/privacy.html | same |
| Support / website | https://noahbush42276-ship-it.github.io/dateline-atlas/support.html | same |
| Keywords | — | news,world,globe,map,headlines,fact check,bias,reliability,breaking,international |

**Description** (both stores; Apple's limit is 4,000 characters):

> Dateline Atlas puts the world's news on a 3D relief globe. Twice a day it gathers fresh reporting from
> hundreds of outlets in many languages, groups it into stories, and pins each one where it happened.
>
> Every story shows how well its facts hold up: how many independent outlets, owners and countries report it,
> which claims are corroborated and which are contested. A framing score shows where outlets tell the same
> story differently, with the wording each one chose.
>
> • The globe: spin it, zoom in, tap a pin for the story
> • Reliability and framing scores for every story, with links to the original articles
> • Filter by topic and time; see what's new since the last sweep
> • Optional local weather for the United States, from the National Weather Service
> • Works offline with the last stories it downloaded
>
> The app is free with one small banner ad and shows the top 80 stories. The Upgrade, a one-time purchase,
> unlocks every story (300 and more), deep search inside summaries, claims and outlets, filters by country and
> reliability, and removes the ad.
>
> Stories are found through the GDELT Project's open index of world news. Reliability and framing scores are
> made by an AI model; they are judgments, not verdicts, and every story links to its sources.

## 7. Questionnaires

These are the answers that match what the app does. Read each question yourself before answering; I'm not a
lawyer, and the stores' wording changes.

**Google Play → App content**
- Privacy policy: the link above. Ads: **Yes, contains ads**. App access: **all functionality is available
  without special access** (the Upgrade is an ordinary purchase).
- Target audience: **13 and over** (or 18+). Not designed for children.
- News app: **Yes**. Google's news policy asks for the publisher's contact details; put your contact email on
  the support page and in the listing.
- Content rating questionnaire: category **News**; it reports real-world violence in news, without graphic
  imagery; no user-generated content, no gambling.
- Data safety (Google's AdMob guidance lists what its SDK collects; check it at
  <https://developers.google.com/admob/android/privacy/play-data-disclosure>):
  - Location → **Approximate location**: collected, not shared, optional, for **app functionality** (weather).
  - Device or other IDs: collected and shared (AdMob), for **advertising or marketing**, **analytics** and
    **fraud prevention**.
  - App activity → app interactions, and App info and performance → diagnostics: collected and shared by
    AdMob, same purposes.
  - Data is encrypted in transit: **Yes**. Users can request deletion: the app keeps nothing on a server, so
    say so; deleting the app deletes its data.
- Advertising ID: **Yes**, used for advertising.

**App Store Connect → App Privacy** (Google's guide for the same answers:
<https://developers.google.com/admob/ios/privacy/data-disclosure>)
- Coarse Location: App Functionality, not linked to identity, not used for tracking.
- Identifiers → Device ID: Third-Party Advertising, used for tracking (when the person allows it).
- Usage Data → Product Interaction and Advertising Data: Third-Party Advertising, Analytics.
- Diagnostics → Crash Data / Performance Data: App Functionality (AdMob).
- Age rating questionnaire: news app; infrequent or mild references to real violence (news), no unrestricted
  web browsing (links open in Safari).
- Encryption: the build already says it uses only standard HTTPS, so App Store Connect won't ask.

## 8. Submitting

- **Apple**: App Store Connect → the app → the version page → add screenshots, description, keywords, support
  and privacy URLs → **Build**: pick the TestFlight build → **In-App Purchases**: add `atlas_upgrade` → review
  notes (below) → **Add for Review**. Review usually takes 1–3 days.
- **Google**: after production is approved, **Production → Create release** with the latest `.aab` → roll out.

Review notes for both stores:

> The app is free with one AdMob banner ad. The non-consumable in-app purchase "Upgrade" (atlas_upgrade)
> unlocks the full story list (the free version shows the top 80), deep search and filters, and removes the ad.
> Tap the star button at the top or the Sources tab → Upgrade; "Restore purchases" is in both places. Weather is
> optional: tap the weather button on the globe and allow approximate location; it covers the United States
> only (National Weather Service). No sign-in is needed.

## 9. After launch

- **Updates**: change `version` in `app/store-config.json` (for example 1.0.1), run both workflows, upload the
  new `.aab` in Play Console, and submit the new build in App Store Connect.
- **Link AdMob**: once each app is live, AdMob → the app → App settings → **Link to app store**.
- **News**: nothing to do. Wire sweeps twice a day on the PC, and the Phone app upload task puts the store feed
  online at 6:58 AM and 6:58 PM. The PC has to be on (or asleep, so HQ can wake it) for new stories.
