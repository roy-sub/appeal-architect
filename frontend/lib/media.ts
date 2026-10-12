/** The media that has actually shipped.
 *
 *  A slot id in here renders its file; a slot id missing from here renders the
 *  designed placeholder. That is the only difference, and it is deliberate: the
 *  box, its aspect ratio and its position are owned by the call site, so adding
 *  or removing a file never moves the layout.
 *
 *  `width` and `height` are the file's real pixel size. They are rendered as
 *  attributes so the browser reserves the right box before the bytes arrive
 *  (no layout shift), and every ratio here matches the `ratio` its call site
 *  passes to within half a percent.
 */
export type MediaAsset = {
  src: string;
  width: number;
  height: number;
};

export const mediaAssets: Record<string, MediaAsset> = {
  // Landing
  "hero-bg": { src: "/media/hero-bg.webp", width: 1920, height: 1086 },
  "stat-backdrop": { src: "/media/stat-backdrop.webp", width: 1600, height: 686 },
  "feature-roadmap": { src: "/media/feature-roadmap.webp", width: 1600, height: 905 },
  "feature-graph": { src: "/media/feature-graph.webp", width: 1600, height: 905 },
  "feature-letter": { src: "/media/feature-letter.webp", width: 1100, height: 1473 },
  "feature-evidence": { src: "/media/feature-evidence.webp", width: 1600, height: 905 },
  "persona-1": { src: "/media/persona-1.webp", width: 900, height: 1206 },
  "persona-2": { src: "/media/persona-2.webp", width: 900, height: 1206 },
  "persona-3": { src: "/media/persona-3.webp", width: 900, height: 900 },

  // Workspace
  "empty-cases": { src: "/media/empty-cases.webp", width: 480, height: 358 },
  "upload-icon": { src: "/media/upload-icon.webp", width: 384, height: 384 },
  "camera-guide": { src: "/media/camera-guide.webp", width: 720, height: 964 },

  // Not a slot: the share card, referenced from app/layout.tsx metadata.
  // Listed so the set is readable in one place.
  "og-card": { src: "/media/og-card.png", width: 1200, height: 630 },
};
