/**
 * The design folder is the visual authority. This fails if the implementation's
 * tokens have drifted from it.
 *
 * `design/project/tokens.css` is the approved palette. `app/globals.css` is what
 * actually ships. Tailwind v4 is CSS-first, so there is no `tailwind.config.ts`
 * to compare — `design/project/tailwind.theme.ts` is kept as a reference and
 * checked here too, so all three agree.
 *
 * Run: npm run check:tokens
 */
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const DESIGN_TOKENS = join(here, "..", "..", "design", "project", "tokens.css");
const DESIGN_THEME = join(here, "..", "..", "design", "project", "tailwind.theme.ts");
const SHIPPED = join(here, "..", "app", "globals.css");

/**
 * Tokens the implementation may add beyond the design file. Each needs a reason.
 */
const ALLOWED_ADDITIONS = new Map([
  ["--paper", "alias of --surface, used by the letter's print styles"],
  ["--ease-expo", "landing-page gesture easing, added with the scroll reveals"],
]);

/**
 * Tokens in the design file that the implementation deliberately does not carry.
 */
const ALLOWED_OMISSIONS = new Map([
  ["--font-sans", "set by next/font as --font-plex-sans"],
  ["--font-doc", "set by next/font as --font-newsreader"],
  ["--font-mono", "set by next/font as --font-plex-mono"],
  ["--s1", "Tailwind's own spacing scale is used instead, not overridden"],
  ["--s2", "see --s1"],
  ["--s3", "see --s1"],
  ["--s4", "see --s1"],
  ["--s5", "see --s1"],
  ["--s6", "see --s1"],
  ["--s7", "see --s1"],
  ["--s8", "see --s1"],
  ["--s9", "see --s1"],
  ["--s10", "see --s1"],
  ["--s11", "see --s1"],
  ["--r-sharp", "radii are written as arbitrary px to stay pixel-exact"],
  ["--r-sm", "see --r-sharp"],
  ["--r-md", "see --r-sharp"],
  ["--r-lg", "see --r-sharp"],
  ["--r-xl", "see --r-sharp"],
  ["--dur-1", "durations live in lib/motion.ts as seconds for Motion"],
  ["--dur-2", "see --dur-1"],
  ["--dur-3", "see --dur-1"],
  ["--dur-4", "see --dur-1"],
  ["--dur-5", "see --dur-1"],
]);

/** Parse `--name: value;` declarations from the first `:root` block. */
function parseRootTokens(css) {
  const start = css.indexOf(":root");
  if (start === -1) throw new Error("no :root block found");
  let depth = 0;
  let end = start;
  for (let i = css.indexOf("{", start); i < css.length; i++) {
    if (css[i] === "{") depth++;
    else if (css[i] === "}") {
      depth--;
      if (depth === 0) {
        end = i;
        break;
      }
    }
  }
  // Strip comments before splitting: a declaration preceded by a section
  // comment would otherwise not match at the start of its piece and be skipped.
  const block = css
    .slice(css.indexOf("{", start) + 1, end)
    .replace(/\/\*[\s\S]*?\*\//g, "");

  const tokens = new Map();
  for (const piece of block.split(";")) {
    const match = /^\s*(--[a-z0-9-]+)\s*:\s*([\s\S]+?)\s*$/.exec(piece);
    if (match) tokens.set(match[1], normalise(match[2]));
  }
  return tokens;
}

/** Compare values, not spelling: casing and whitespace are not drift. */
function normalise(value) {
  return value
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, " ");
}

const design = parseRootTokens(readFileSync(DESIGN_TOKENS, "utf8"));
const shipped = parseRootTokens(readFileSync(SHIPPED, "utf8"));
const themeSource = readFileSync(DESIGN_THEME, "utf8");

const problems = [];

for (const [name, designValue] of design) {
  if (!shipped.has(name)) {
    if (!ALLOWED_OMISSIONS.has(name)) {
      problems.push(`${name} is in the design tokens but not in app/globals.css`);
    }
    continue;
  }
  const shippedValue = shipped.get(name);
  if (shippedValue !== designValue) {
    problems.push(
      `${name} has drifted — design says ${designValue}, globals.css says ${shippedValue}`,
    );
  }
}

for (const name of shipped.keys()) {
  if (!design.has(name) && !ALLOWED_ADDITIONS.has(name)) {
    problems.push(
      `${name} is in app/globals.css but not in the design tokens. ` +
        "If it is deliberate, add it to ALLOWED_ADDITIONS with a reason.",
    );
  }
}

// Every colour hex in the design theme must appear in the shipped tokens, so the
// theme file and the CSS cannot disagree either.
const shippedValues = new Set(shipped.values());
for (const hex of new Set(themeSource.match(/#[0-9a-fA-F]{6}\b/g) ?? [])) {
  if (!shippedValues.has(hex.toLowerCase())) {
    problems.push(`${hex} appears in design/project/tailwind.theme.ts but in no shipped token`);
  }
}

if (problems.length > 0) {
  console.error("Design tokens have drifted from /design:\n");
  for (const problem of problems) console.error(`  - ${problem}`);
  console.error(
    "\n/design is the visual authority. Change the design file first, or record " +
      "the exception in scripts/check-tokens.mjs with a reason.",
  );
  process.exit(1);
}

console.log(
  `Tokens agree with /design: ${design.size} design tokens, ${shipped.size} shipped, ` +
    `${ALLOWED_OMISSIONS.size} documented omissions, ${ALLOWED_ADDITIONS.size} documented additions.`,
);
