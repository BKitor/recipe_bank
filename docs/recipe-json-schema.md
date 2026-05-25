# Recipe JSON Schema

Each recipe is stored as a `.json` file under `src/recipes/`. The filename is the recipe's slug (e.g. `easy-butter-chicken-recipe.json`).

## Top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `title` | string | **Required** | Recipe name |
| `id` | string | **Required** | URL slug, auto-generated from `title` on import |
| `date_added` | string | **Required** | ISO 8601 date (`YYYY-MM-DD`), set automatically on import |
| `source_url` | string \| null | Optional | URL the recipe was imported from |
| `description` | string \| null | Optional | Short summary of the recipe |
| `prep_time_min` | integer \| null | Optional | Prep time in minutes |
| `cook_time_min` | integer \| null | Optional | Cook time in minutes |
| `total_time_min` | integer \| null | Optional | Total time in minutes |
| `servings` | string \| null | Optional | Yield description (e.g. `"4"`, `"6 servings"`) |
| `tags` | string[] | Optional | List of category/cuisine tags; defaults to `[]` |
| `ingredient_groups` | object[] | **Required** | One or more groups of ingredients (see below) |
| `instruction_groups` | object[] | **Required** | One or more groups of steps (see below) |
| `notes` | string \| null | Optional | Free-form notes, tips, or substitutions |

## `ingredient_groups` items

Each entry in `ingredient_groups` is an object with:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Optional | Group label (e.g. `"For the sauce"`); empty string `""` for ungrouped |
| `ingredients` | object[] | **Required** | List of ingredients (see below) |

### Ingredient object

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | **Required** | Ingredient name (e.g. `"garlic"`) |
| `amount` | string | Optional | Quantity (e.g. `"2"`, `"1/2"`); empty string if unquantified |
| `unit` | string | Optional | Unit of measure (e.g. `"tablespoons"`, `"cups"`); empty string if none |
| `notes` | string | Optional | Preparation note (e.g. `"minced"`, `"divided"`); empty string if none |

## `instruction_groups` items

Each entry in `instruction_groups` is an object with:

| Field | Type | Required | Description |
|---|---|---|---|
| `name` | string | Optional | Group label (e.g. `"Grilling Directions"`); empty string `""` for ungrouped |
| `steps` | string[] | **Required** | Ordered list of instruction steps |

## Example

```json
{
  "title": "Chicken Pan Sauce",
  "id": "chicken-pan-sauce",
  "date_added": "2026-05-02",
  "source_url": "https://example.com/chicken-pan-sauce",
  "description": "A quick weeknight pan sauce.",
  "prep_time_min": 10,
  "cook_time_min": 20,
  "total_time_min": 30,
  "servings": "4",
  "tags": ["Dinner", "American"],
  "ingredient_groups": [
    {
      "name": "",
      "ingredients": [
        { "amount": "2", "unit": "tablespoons", "name": "olive oil", "notes": "" },
        { "amount": "2", "unit": "pounds", "name": "chicken breast", "notes": "pounded to 1/2 inch thickness" }
      ]
    }
  ],
  "instruction_groups": [
    {
      "name": "",
      "steps": [
        "Season the chicken with salt and pepper.",
        "Sear in olive oil over medium-high heat, 5 minutes per side.",
        "Remove chicken, deglaze the pan with broth, and reduce until slightly thickened."
      ]
    }
  ],
  "notes": null
}
```
