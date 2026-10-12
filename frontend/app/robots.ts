import type { MetadataRoute } from "next";
import { SITE_URL } from "@/lib/site-url";

// Emitted as a static robots.txt at build time.
export const dynamic = "force-static";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      // Everything behind sign-in. These pages render nothing without a session,
      // so an indexed copy would be an empty shell with a health-related title
      // on it. Keep them out.
      disallow: ["/cases/", "/case/", "/settings/", "/auth/"],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
