/* Cesium ion ↔ GitHub Pages
 * Dashboard: https://ion.cesium.com/tokens
 * Allowed URLs:
 *   https://elcidspain.github.io
 *   https://elcidspain.github.io/aumara/
 * Asset: 2275207 Google Photorealistic 3D Tiles
 * Paste once: /aumara/?ion=TOKEN  (saved in this browser)
 */
window.AUMARA_ION = {
  asset: 2275207,
  pages: [
    "https://elcidspain.github.io",
    "https://elcidspain.github.io/aumara/",
  ],
  resolve: function () {
    var q = new URLSearchParams(location.search).get("ion");
    if (q) {
      try { localStorage.setItem("CESIUM_ION_TOKEN", q); } catch (e) {}
      return q;
    }
    try { return localStorage.getItem("CESIUM_ION_TOKEN") || ""; } catch (e) { return ""; }
  },
  apply: function (C) {
    var token = this.resolve();
    if (token) C.Ion.defaultAccessToken = token;
    return !!token;
  },
};
