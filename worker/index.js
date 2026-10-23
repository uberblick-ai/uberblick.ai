// Splits uberblick.ai between the website and the legacy Rails app.
//
// The legacy app (uberblick-ai/uberblick) still runs behind the uberblick.ai
// DNS record. Requests for its paths go there unchanged with fetch(request);
// on a Workers route that is the origin the DNS record names, so the app keeps
// its host, cookies, websocket (/cable) and the WAF rules for /mcp and OAuth.
// Everything else is the website in out/, served by the assets binding; the
// legacy marketing pages /pricing and /request-access redirect there
// (static/_redirects). Every other host the Worker answers for, www and the
// old preview host next, redirects to the apex; wrangler dev on localhost does
// not, so the site can be tried locally.
// Remove a prefix here once the Rails app no longer serves it; remove the
// whole list, and the "Legacy login" button in build.py, when it shuts down.

const APEX = 'uberblick.ai';

const LEGACY = [
  '/app', '/mcp', '/oauth', '/auth', '/__', '/sign-in', '/sign-out',
  '/invites', '/slack', '/prd', '/rfc', '/rfcs', '/bug', '/feature-request',
  '/pages', '/settings', '/triage', '/search', '/cards', '/workspaces',
  '/workspace-access', '/account', '/comment_threads', '/product-requirements',
  '/dashboard', '/admin', '/assets', '/rails', '/cable', '/up',
];

const legacy = (path) =>
  path.startsWith('/.well-known/oauth-') ||
  LEGACY.some((p) => path === p || path.startsWith(`${p}/`));

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.hostname.endsWith(`.${APEX}`)) {
      url.hostname = APEX;
      return Response.redirect(url.toString(), 301);
    }
    if (legacy(url.pathname)) {
      ctx.passThroughOnException();
      return fetch(request);
    }
    return env.ASSETS.fetch(request);
  },
};
