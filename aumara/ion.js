/* Cesium ion / Google Maps Photorealistic 3D Tiles
 * Dashboard (Ion): https://ion.cesium.com/tokens
 * Dashboard (Google): Maps Platform Photorealistic 3D Tiles API
 * Allowed URLs:
 *   https://elcidspain.github.io
 *   https://elcidspain.github.io/aumara/
 * Runtime only: paste via the Ion button. Never put a key in the page URL.
 * Asset: 2275207 Google Photorealistic 3D Tiles
 */
window.AUMARA_ION = {
  asset: 2275207,
  pages: [
    "https://elcidspain.github.io",
    "https://elcidspain.github.io/aumara/",
  ],
  resolve: function () {
    try { return localStorage.getItem("CESIUM_ION_TOKEN") || ""; } catch (e) { return ""; }
  },
  apply: function (C) {
    var token = this.resolve();
    if (token) C.Ion.defaultAccessToken = token;
    return !!token;
  },
};
