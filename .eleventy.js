const { HtmlBasePlugin } = require("@11ty/eleventy");

module.exports = function (eleventyConfig) {
  eleventyConfig.addPassthroughCopy("src/assets");

  eleventyConfig.addPlugin(HtmlBasePlugin);

  // pagefind UI (pagefind-ui.js + pagefind-ui.css) is auto-bundled by
  // `npx pagefind --site _site` when it detects references on the page.

  eleventyConfig.addFilter("formatTime", (minutes) => {
    if (!minutes) return "";
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h} hr ${m} min`;
    if (h) return `${h} hr`;
    return `${m} min`;
  });

  eleventyConfig.addFilter("allTags", (recipes) => {
    const tags = new Set();
    recipes.forEach((r) => (r.tags || []).forEach((t) => tags.add(t)));
    return [...tags].sort();
  });

  eleventyConfig.addFilter("first", (arr, n) => (arr || []).slice(0, n));

  eleventyConfig.addFilter("tagSlug", (tag) =>
    tag.toLowerCase().replace(/\s+/g, "-").replace(/[^\w-]/g, "")
  );

  return {
    dir: {
      input: "src",
      output: "_site",
      includes: "_includes",
      data: "_data",
    },
    templateFormats: ["njk", "html"],
    htmlTemplateEngine: "njk",
    pathPrefix: "/recipe_bank/",
  };
};
