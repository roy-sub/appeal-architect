import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site-url";

export const dynamic = "force-static";

// The public pages only. Trailing slashes to match next.config's trailingSlash,
// so the sitemap and the served URLs agree.
const PUBLIC_PATHS = ["/", "/triage/", "/pricing/", "/legal/", "/signin/"] as const;

export default function sitemap(): MetadataRoute.Sitemap {
  return PUBLIC_PATHS.map((path) => ({
    url: `${SITE_URL}${path}`,
    changeFrequency: path === "/" ? ("weekly" as const) : ("monthly" as const),
    priority: path === "/" ? 1 : path === "/triage/" ? 0.9 : 0.5,
  }));
}
