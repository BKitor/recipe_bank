// Downloads recipe images from external URLs into src/assets/images/.
// Run with: node scripts/download_images.js
// Safe to re-run — skips files that already exist.

const fs = require("fs");
const path = require("path");
const https = require("https");
const http = require("http");

const recipesDir = path.join(__dirname, "../src/recipes");
const imagesDir = path.join(__dirname, "../src/assets/images");

fs.mkdirSync(imagesDir, { recursive: true });

function download(url, dest, redirects = 5) {
  return new Promise((resolve, reject) => {
    if (redirects === 0) return reject(new Error("too many redirects"));
    const lib = url.startsWith("https") ? https : http;
    lib.get(url, (res) => {
      if (res.statusCode === 301 || res.statusCode === 302) {
        return download(res.headers.location, dest, redirects - 1)
          .then(resolve)
          .catch(reject);
      }
      if (res.statusCode !== 200) {
        res.resume();
        return reject(new Error(`HTTP ${res.statusCode}`));
      }
      const file = fs.createWriteStream(dest);
      res.pipe(file);
      file.on("finish", () => file.close(resolve));
      file.on("error", (err) => { fs.unlink(dest, () => {}); reject(err); });
    }).on("error", reject);
  });
}

function extFromUrl(url) {
  const part = url.split("?")[0].split(".").pop().toLowerCase();
  return ["jpg", "jpeg", "png", "webp", "gif"].includes(part) ? part : "jpg";
}

async function main() {
  const files = fs.readdirSync(recipesDir).filter((f) => f.endsWith(".json"));
  for (const f of files) {
    const recipe = JSON.parse(fs.readFileSync(path.join(recipesDir, f), "utf8"));
    if (!recipe.image_url) continue;
    const ext = extFromUrl(recipe.image_url);
    const dest = path.join(imagesDir, `${recipe.id}.${ext}`);
    if (fs.existsSync(dest)) {
      console.log(`skip  ${recipe.id}`);
      continue;
    }
    process.stdout.write(`fetch ${recipe.id} ... `);
    try {
      await download(recipe.image_url, dest);
      console.log("ok");
    } catch (e) {
      console.log(`FAIL (${e.message})`);
    }
  }
}

main();
