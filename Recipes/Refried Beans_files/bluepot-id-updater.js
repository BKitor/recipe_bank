jQuery(document).ready(function () {
  let extendedRecipeSchema = null;
  let recipeSchema = null;

  jQuery('script[type="application/ld+json"]').each(function () {
    const schemaJQuery = jQuery(this);
    const schemaJson = jQuery.parseJSON(schemaJQuery.text());
    if (schemaJson['@type'] == 'ExtendedRecipe') {
      extendedRecipeSchema = {
        'jquery': schemaJQuery,
        'json': schemaJson,
        'id': schemaJson['@id']
      };
    } else if (schemaJson['@type'] == 'Recipe') {
      recipeSchema = {
        'jquery': schemaJQuery,
        'json': schemaJson,
        'id': schemaJson['@id']
      };
    } else if (schemaJson['@graph'] != null) {
      for (const element of schemaJson['@graph']) {
        if (element['@type'] == 'Recipe') {
          recipeSchema = {
            'jquery': schemaJQuery,
            'json': schemaJson,
            'id': element['@id']
          };
          break;
        }
      }
    }
  });

  if (extendedRecipeSchema != null && recipeSchema != null &&
      extendedRecipeSchema.id != recipeSchema.id) {
    if (recipeSchema.json['@graph'] != null) {
      for (let i = 0; i < recipeSchema.json['@graph'].length; i++) {
        if (recipeSchema.json['@graph'][i]['@type'] == 'Recipe') {
          recipeSchema.json['@graph'][i]['@id'] = extendedRecipeSchema.id;
          break;
        }
      }
    } else {
      recipeSchema.json['@id'] = extendedRecipeSchema.id;
    }
    recipeSchema.jquery.replaceWith('<script type=\"application/ld+json\">' +
        JSON.stringify(recipeSchema.json) + '<\/script>');
  }
});
