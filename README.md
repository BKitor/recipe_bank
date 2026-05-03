# Recipe Bank

Personal recipe website — saved HTML recipe pages normalized to JSON and served as a searchable static site.

**Stack:** [Eleventy](https://www.11ty.dev/) · [Pagefind](https://pagefind.app/) · GitHub Pages

---

## Website

### Setup

```bash
npm install
```

### Development server

```bash
npm run serve        # http://localhost:8080, live-reloads on file changes
```

### Build

```bash
npm run build        # generate static site → _site/
npm run build:full   # build + rebuild Pagefind search index
npm run clean        # delete _site/
```

---

## Recipe Importer

The `importer/` directory is an installable Python CLI tool that converts saved `.html` recipe pages into the JSON format the website consumes (`src/recipes/<slug>.json`).

### Setup

```bash
pip install -e "importer[dev]"
```

### Import recipes

```bash
# Import a whole directory
recipe-importer Recipes/

# Import specific files
recipe-importer "Recipes/SomeRecipe.html" "Recipes/Another.html"

# Preview without writing files or downloading images
recipe-importer --dry-run Recipes/

# Write output to a custom directory (useful for testing)
recipe-importer --output /tmp/preview Recipes/
```

After importing, run `npm run build:full` to rebuild the site and search index.

### Supported formats

The importer auto-detects the recipe format:

| Strategy | Detected by |
|---|---|
| `wprm_js` | WordPress WPRM plugin (with JS data) |
| `wprm_html` | WordPress WPRM plugin (HTML only) |
| `jetpack` | WordPress Jetpack recipe block |
| `serious_eats` | SeriousEats.com |
| `tasty` | Tasty Recipes plugin |
| `based_cooking` | based.cooking |
| `json_ld` | JSON-LD structured data (`application/ld+json`) |
| `generic_html` | Everything else — multi-component or flat HTML |

### Tests

```bash
cd importer && pytest
```

Snapshot fixtures live in `importer/tests/fixtures/`. After an intentional parser change, regenerate them:

```bash
python importer/tests/gen_fixtures.py
```

### Build a wheel

```bash
cd importer && python -m build   # outputs to importer/dist/
```
