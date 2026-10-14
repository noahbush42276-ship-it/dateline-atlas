// Bundled by esbuild into www/native.bundle.js in the cloud build. The web app (www/index.html) is plain HTML with
// no bundler, so this hands it the three native plugins it uses on window.AtlasNative.
import { AdMob } from "@capacitor-community/admob";
import { Geolocation } from "@capacitor/geolocation";
import { NativePurchases } from "@capgo/native-purchases";

window.AtlasNative = { AdMob, Geolocation, NativePurchases };
