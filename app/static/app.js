/* posthog-js bootstrap, plus the two client-side hooks the demo needs:
   - every HTMX request carries the distinct id and session id so server events join the same person
   - the "fault-cart-js-error" flag makes Add to cart throw, which exception autocapture reports */
!(function (t, e) { var o, n, p, r; e.__SV || ((window.posthog = e), (e._i = []), (e.init = function (i, s, a) { function g(t, e) { var o = e.split("."); 2 == o.length && ((t = t[o[0]]), (e = o[1])), (t[e] = function () { t.push([e].concat(Array.prototype.slice.call(arguments, 0))); }); } ((p = t.createElement("script")).type = "text/javascript"), (p.crossOrigin = "anonymous"), (p.async = !0), (p.src = s.api_host.replace(".i.posthog.com", "-assets.i.posthog.com") + "/static/array.js"), (r = t.getElementsByTagName("script")[0]).parentNode.insertBefore(p, r); var u = e; for (void 0 !== a ? (u = e[a] = []) : (a = "posthog"), u.people = u.people || [], u.toString = function (t) { var e = "posthog"; return "posthog" !== a && (e += "." + a), t || (e += " (stub)"), e; }, u.people.toString = function () { return u.toString(1) + ".people (stub)"; }, o = "init capture register register_once register_for_session unregister unregister_for_session getFeatureFlag getFeatureFlagPayload isFeatureEnabled reloadFeatureFlags updateEarlyAccessFeatureEnrollment getEarlyAccessFeatures on onFeatureFlags onSurveysLoaded onSessionId getSurveys getActiveMatchingSurveys renderSurvey canRenderSurvey identify setPersonProperties group resetGroups setPersonPropertiesForFlags resetPersonPropertiesForFlags setGroupPropertiesForFlags resetGroupPropertiesForFlags reset get_distinct_id getGroups get_session_id get_session_replay_url alias set_config startSessionRecording stopSessionRecording sessionRecordingStarted captureException loadToolbar get_property getSessionProperty createPersonProfile opt_in_capturing opt_out_capturing has_opted_in_capturing has_opted_out_capturing clear_opt_in_out_capturing debug getPageViewId captureTraceFeedback captureTraceMetric".split(" "), n = 0; n < o.length; n++) g(u, o[n]); e._i.push([i, s, a]); }), (e.__SV = 1)); })(document, window.posthog || []);

if (window.SHOP && window.SHOP.posthogKey) {
  posthog.init(window.SHOP.posthogKey, {
    api_host: window.SHOP.posthogHost,
    capture_exceptions: true,
    capture_pageview: true,
    capture_pageleave: true,
    autocapture: true,
    person_profiles: "always",
  });
}

document.addEventListener("htmx:configRequest", function (event) {
  if (!window.posthog || !posthog.get_distinct_id) return;
  event.detail.headers["X-PostHog-Distinct-Id"] = posthog.get_distinct_id();
  if (posthog.get_session_id) event.detail.headers["X-PostHog-Session-Id"] = posthog.get_session_id();
});

document.addEventListener("submit", function (event) {
  var form = event.target;
  if (!form.classList || !form.classList.contains("add-form")) return;
  var planted = window.SHOP.flags["fault-cart-js-error"];
  if (window.posthog && posthog.isFeatureEnabled) planted = posthog.isFeatureEnabled("fault-cart-js-error") || planted;
  if (planted) {
    event.preventDefault();
    event.stopImmediatePropagation();
    var slug = form.querySelector("[name=slug]").value;
    throw new TypeError("Cannot read properties of undefined (reading 'variantId') while adding " + slug);
  }
});
