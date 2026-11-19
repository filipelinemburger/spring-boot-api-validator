---
type: llm
focus: trace
weight: 1
---

The report flags that Cookbook.recipes is @ManyToMany(cascade = CascadeType.ALL), so deleting a personal cookbook (DELETE /api/cookbooks/{id}) deletes the recipes saved in it, including recipes written by other authors — at its most severe level
