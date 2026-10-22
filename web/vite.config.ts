import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { SITE, shareTags } from "./src/site.ts";
export default defineConfig({
  base: "./",
  plugins: [
    react(),
    {
      name: "reviewed-social-metadata",
      transformIndexHtml() {
        const metadata = shareTags(SITE);
        return [
          ...metadata.tags.map((tag) => ({
            ...tag,
            injectTo: "head" as const,
          })),
          ...(metadata.canonical
            ? [
                {
                  tag: "link",
                  attrs: { rel: "canonical", href: metadata.canonical },
                  injectTo: "head" as const,
                },
              ]
            : []),
        ];
      },
    },
  ],
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    restoreMocks: true,
  },
  build: { sourcemap: false },
});
