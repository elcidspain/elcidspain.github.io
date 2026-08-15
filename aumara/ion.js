/* Cesium ion — Google Photorealistic 3D Tiles
 * Dashboard: https://ion.cesium.com/tokens
 * Production token: dedicated AUMARA application token, minimum public scopes.
 * Allowed URLs (restrict the token to these only):
 *   https://elcidspain.github.io/aumara/
 *   https://aumara.me/
 * Runtime only: CESIUM_ION_TOKEN from localStorage. Ignore ?ion= completely.
 * Never print the token. Never pass it through a public page URL.
 * Asset: 2275207 Google Photorealistic 3D Tiles
 */
(function () {
  try {
    var u = new URL(location.href);
    if (u.searchParams.has("ion")) {
      u.searchParams.delete("ion");
      history.replaceState(null, "", u.pathname + (u.search || "") + (u.hash || ""));
    }
  } catch (e) {}
})();
window.AUMARA_ION = {
  asset: 2275207,
  pages: [
    "https://elcidspain.github.io/aumara/",
    "https://aumara.me/",
  ],
  resolve: function () {
    try { return localStorage.getItem("CESIUM_ION_TOKEN") || ""; } catch (e) { return ""; }
  },
  apply: function (C) {
    var token = this.resolve();
    if (token) C.Ion.defaultAccessToken = token;
    return !!(token || (C.Ion && C.Ion.defaultAccessToken));
  },
};
