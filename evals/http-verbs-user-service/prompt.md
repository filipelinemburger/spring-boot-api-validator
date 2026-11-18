---
tags: [spring-api-validator]
max_turns: 60
timeout_seconds: 1200
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit, Bash]
---

Check whether the endpoints in UserController use the right HTTP methods — GET to read, POST to create, PUT to update/replace, PATCH for partial updates, DELETE to remove — and whether they return the right status codes. Write your findings to verbs-report.md.

Input files: the project in the current directory
