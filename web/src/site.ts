import config from "../site.config.json" with { type: "json" };
export type SiteConfig = {
  authorName: string;
  authorGithubUrl: string;
  professionalProfileUrl: string | null;
  productionUrl: string | null;
};
export const META = {
  title: "Marketing Uplift | The Decision Lab",
  description:
    "Who should actually see your next ad? Explore a real advertising benchmark, frozen estimates and the discipline behind a conservative no-targeting recommendation.",
  image: "social-preview.png",
  imageAlt:
    "Marketing Uplift — The Decision Lab. Who should actually see your next ad? Offline research; frozen recommendation: no targeting.",
};
function safeUrl(value: string) {
  const u = new URL(value);
  if (u.protocol !== "https:" || u.username || u.password || u.search || u.hash)
    throw new Error(
      "Use a public HTTPS URL without credentials, query or fragment.",
    );
  return u;
}
export function validateSiteConfig(value: SiteConfig) {
  if (
    !value ||
    Object.keys(value).sort().join("|") !==
      [
        "authorName",
        "authorGithubUrl",
        "professionalProfileUrl",
        "productionUrl",
      ]
        .sort()
        .join("|")
  )
    throw new Error(
      "Unexpected metadata fields; only reviewed public identity and URL fields are permitted.",
    );
  if (
    !value ||
    typeof value.authorName !== "string" ||
    !value.authorName.trim() ||
    value.authorName.length > 100
  )
    throw new Error("An explicitly reviewed author name is required.");
  if (safeUrl(value.authorGithubUrl).hostname !== "github.com")
    throw new Error("Author GitHub URL must use github.com.");
  if (value.professionalProfileUrl !== null)
    safeUrl(value.professionalProfileUrl);
  if (value.productionUrl !== null) {
    const u = safeUrl(value.productionUrl);
    if (
      !u.pathname.endsWith("/") ||
      /localhost|(^|\.)example\.(com|org|net)$|\.(test|invalid|example)$|^127\.|^\[::1\]$/.test(
        u.hostname,
      )
    )
      throw new Error(
        "Use the reviewed production HTTPS root, ending in /; placeholders are not publishable.",
      );
  }
  return value;
}
export const SITE = validateSiteConfig(config);
export function shareTags(value: SiteConfig) {
  const s = validateSiteConfig(value);
  const tags = [
    { tag: "meta", attrs: { name: "author", content: s.authorName } },
    { tag: "meta", attrs: { property: "og:type", content: "website" } },
    {
      tag: "meta",
      attrs: {
        property: "og:site_name",
        content: "Marketing Uplift | The Decision Lab",
      },
    },
    { tag: "meta", attrs: { property: "og:title", content: META.title } },
    {
      tag: "meta",
      attrs: { property: "og:description", content: META.description },
    },
    { tag: "meta", attrs: { name: "twitter:title", content: META.title } },
    {
      tag: "meta",
      attrs: { name: "twitter:description", content: META.description },
    },
    {
      tag: "meta",
      attrs: {
        name: "twitter:card",
        content: s.productionUrl ? "summary_large_image" : "summary",
      },
    },
  ];
  if (s.productionUrl) {
    const image = new URL(META.image, s.productionUrl).href;
    tags.push(
      { tag: "meta", attrs: { property: "og:url", content: s.productionUrl } },
      { tag: "meta", attrs: { property: "og:image", content: image } },
      { tag: "meta", attrs: { property: "og:image:width", content: "1200" } },
      { tag: "meta", attrs: { property: "og:image:height", content: "630" } },
      {
        tag: "meta",
        attrs: { property: "og:image:alt", content: META.imageAlt },
      },
      { tag: "meta", attrs: { name: "twitter:image", content: image } },
      {
        tag: "meta",
        attrs: { name: "twitter:image:alt", content: META.imageAlt },
      },
    );
    return { tags, canonical: s.productionUrl };
  }
  return { tags, canonical: null };
}
