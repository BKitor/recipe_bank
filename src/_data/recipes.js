const fs = require("fs");
const path = require("path");

const IMAGE_EXTS = ["jpg", "jpeg", "png", "webp", "gif"];
const imgDir = path.join(__dirname, "../assets/images");

function localImage(id) {
  for (const ext of IMAGE_EXTS) {
    if (fs.existsSync(path.join(imgDir, `${id}.${ext}`))) {
      return `/assets/images/${id}.${ext}`;
    }
  }
  return null;
}

module.exports = () => {
  const dir = path.join(__dirname, "../recipes");
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => {
      const recipe = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
      recipe.image = localImage(recipe.id) || recipe.image_url || null;
      return recipe;
    })
    .sort((a, b) => a.title.localeCompare(b.title));
};
