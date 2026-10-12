/** Where this build of the site will live.
 *
 *  Only absolute URLs need it: the share card, canonical links, robots.txt and
 *  the sitemap. Without it Next falls back to http://localhost:3000 and every
 *  share of the site points at a machine nobody else can reach, which is a
 *  silent failure — the page still renders, the preview is just blank.
 *
 *  Set NEXT_PUBLIC_SITE_URL at build time. Cloudflare Pages sets it per
 *  environment, so a preview deploy advertises itself and not production.
 */
export const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000").replace(/\/$/, "");
