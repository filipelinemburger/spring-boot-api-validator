---
type: llm
focus: trace
weight: 1
---

The report flags that Recipe.cuisine is @ManyToOne(cascade = CascadeType.ALL), so deleting a recipe (DELETE /api/recipes/{id}, and account deletion through Author.recipes) also removes its Cuisine, and because schema.sql declares recipes.cuisine_id ... ON DELETE CASCADE the database then deletes every other author's recipes of that cuisine — at its most severe level
