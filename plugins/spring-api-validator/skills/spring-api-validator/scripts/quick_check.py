#!/usr/bin/env python3
"""Fast, deterministic checks for common Spring REST API defects.

Usage:
    python3 quick_check.py <project-root> [--json] [--fail-on error|warning|never] [--rules QC03,QC08]

Part of the spring-api-validator skill. Standard-library Python 3, no build or running app needed.
It reads .java/.kt sources under src/main (and the build file and application config) and reports
pattern matches with file:line, a rule id, what goes wrong at runtime and the fix.

It is a first pass, not a verdict: the patterns are exact for what they match, but they don't follow
calls into services or know the team's intent. The skill (or a reviewer) confirms each finding in the
code. Rules marked "verify" are heuristics that point at something worth a look.

Exit status: 0 unless --fail-on is set and a finding at or above that severity exists (then 1).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from list_endpoints import (  # noqa: E402  (shared parsing helpers)
    MAPPING_RE, SKIP_DIRS, balanced_args, join_paths, parse_mapping, skip_annotations,
    split_top_level, strip_comments,
)

SEVERITIES = ("error", "warning", "suggestion")

CONSTRAINTS = {
    "NotNull", "NotBlank", "NotEmpty", "Size", "Min", "Max", "DecimalMin", "DecimalMax", "Positive",
    "PositiveOrZero", "Negative", "NegativeOrZero", "Pattern", "Email", "Past", "PastOrPresent", "Future",
    "FutureOrPresent", "Digits", "AssertTrue", "AssertFalse", "Null", "Length", "Range", "URL",
}
STRING_TYPES = {"String", "CharSequence"}
COLLECTION_TYPES = {"List", "Set", "Collection", "Iterable", "Map", "SortedSet", "LinkedList", "ArrayList",
                    "HashSet", "MutableList", "MutableSet", "MutableMap"}
CONTAINER_TYPES = COLLECTION_TYPES | {"Optional", "Mono", "Flux"}
PRIMITIVES = {"int", "long", "short", "byte", "double", "float", "boolean", "char"}
NUMERIC_TYPES = {"int", "long", "short", "byte", "double", "float", "Integer", "Long", "Short", "Byte",
                 "Double", "Float", "BigDecimal", "BigInteger", "Int"}
BOOLEAN_TYPES = {"boolean", "Boolean"}
DATE_TYPES = {"LocalDate", "LocalDateTime", "LocalTime", "OffsetDateTime", "ZonedDateTime", "Instant",
              "Date", "YearMonth"}
WRAPPER_TYPES = {"ResponseEntity", "Optional", "List", "Set", "Collection", "Page", "Slice", "Mono", "Flux",
                 "PagedModel", "CompletableFuture", "Iterable", "Stream", "Callable", "DeferredResult"}
# Only words that are unambiguously actions; nouns that double as verbs ("transfer", "release", "import")
# would flag ordinary resource names.
ACTION_VERBS = {"delete", "remove", "cancel", "create", "update", "save", "add", "approve", "reject",
                "activate", "deactivate", "reset", "send", "publish", "accept", "confirm", "withdraw",
                "promote", "terminate", "submit", "enable", "disable", "assign", "unassign", "execute",
                "purge"}
VERB_PREFIX_RE = re.compile(r"^(get|fetch|list|find|create|add|update|save|delete|remove|set)[A-Z]")

RULES = {
    "QC01": ("validation-not-enabled", "Constraint annotations are used but no Bean Validation provider is on the classpath"),
    "QC02": ("validation-namespace", "Validation imports from the wrong namespace for this Spring Boot version"),
    "QC03": ("request-body-not-validated", "@RequestBody whose type has constraints, without @Valid/@Validated"),
    "QC04": ("nested-validation-not-cascaded", "Nested object or collection of constrained types without @Valid"),
    "QC05": ("constraint-type-mismatch", "Constraint on a type it doesn't support"),
    "QC06": ("notnull-on-primitive", "@NotNull on a primitive can never fail"),
    "QC07": ("primitive-in-request-body", "Primitive field in a request body: a missing value becomes 0/false"),
    "QC08": ("optional-primitive-parameter", "Optional request parameter or header declared as a primitive"),
    "QC09": ("mapping-without-method", "Handler @RequestMapping without a method answers every HTTP verb"),
    "QC10": ("path-variable-mismatch", "@PathVariable and URI template variable names don't match"),
    "QC11": ("multiple-request-bodies", "More than one @RequestBody in a handler"),
    "QC12": ("body-on-get-or-delete", "@RequestBody on a GET, HEAD or DELETE handler"),
    "QC13": ("verb-in-path", "Action verb in a GET path, or a verb that duplicates the HTTP method"),
    "QC14": ("date-parameter-format", "Date/time request parameter without @DateTimeFormat"),
    "QC15": ("entity-in-api", "JPA entity used as a request body or response type"),
    "QC16": ("bare-not-found", "Missing value turned into an unmapped exception (500) instead of a 404"),
    "QC17": ("bcrypt-password-length", "Password limit above BCrypt's 72-byte maximum"),
    "QC18": ("error-dispatch-401", "Unhandled errors likely reach clients as 401 (stateless token filter, /error not permitted)"),
    "QC19": ("kotlin-constraint-target", "Kotlin constraint on a constructor property without @field:"),
}


# ---------------------------------------------------------------------------------------------
# Source model

class Source:
    def __init__(self, path, root):
        self.path = path
        self.rel = os.path.relpath(path, root)
        self.kotlin = path.endswith(".kt")
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        self.text = strip_comments(raw)
        self._nl = [i for i, c in enumerate(self.text) if c == "\n"]

    def line(self, pos):
        lo, hi = 0, len(self._nl)
        while lo < hi:
            mid = (lo + hi) // 2
            if self._nl[mid] < pos:
                lo = mid + 1
            else:
                hi = mid
        return lo + 1


class Field:
    def __init__(self, name, type_, annotations, line, ctor_param=False, raw_annos=""):
        self.name = name
        self.type = type_
        self.annotations = annotations  # list of (name, args)
        self.line = line
        self.ctor_param = ctor_param      # Kotlin primary-constructor property / Java record component
        self.raw_annos = raw_annos

    def has(self, *names):
        return any(a[0] in names for a in self.annotations)

    def anno(self, name):
        return next((a for a in self.annotations if a[0] == name), None)


class TypeInfo:
    def __init__(self, name, kind, src, line, annotations):
        self.name = name
        self.kind = kind
        self.src = src
        self.line = line
        self.annotations = annotations
        self.fields = []

    @property
    def is_entity(self):
        return "Entity" in self.annotations

    def constraint_fields(self):
        return [f for f in self.fields if any(a[0] in CONSTRAINTS for a in f.annotations)]


ANNO_RE = re.compile(r"@(?:(?:field|get|param|set|property):)?([\w.]+)")


def read_annotations(text, i=0):
    """Read consecutive annotations starting at text[i]; return ([(simple_name, args)], next_index, raw)."""
    annos, start = [], i
    while True:
        while i < len(text) and text[i] in " \t\r\n":
            i += 1
        m = ANNO_RE.match(text, i)
        if not m or m.group(1) in ("interface",):
            return annos, i, text[start:i]
        args, end = balanced_args(text, m.end())
        if end == m.end():
            args = ""
        annos.append((m.group(1).split(".")[-1], args))
        i = end


def raw_type(type_str):
    """Simple name of the outer type: 'java.util.List<Foo>' -> 'List', 'Foo[]' -> 'Foo', 'Int?' -> 'Int'."""
    t = re.sub(r"@[\w.:]+(\([^)]*\))?\s*", "", type_str).strip()
    t = t.split("<", 1)[0].strip().rstrip("?").replace("[]", "").replace("...", "").strip()
    return t.split(".")[-1]


def type_args(type_str):
    if "<" not in type_str:
        return []
    inner = type_str[type_str.index("<") + 1:type_str.rindex(">")] if ">" in type_str else ""
    return [a.strip() for a in split_top_level(inner) if a.strip()]


def element_types(type_str):
    """Types to inspect for validation cascade / entity checks: the type itself, or a container's args."""
    rt = raw_type(type_str)
    if type_str.strip().endswith("[]"):
        return [type_str.strip()[:-2]]
    if rt in CONTAINER_TYPES or rt in WRAPPER_TYPES:
        out = []
        for a in type_args(type_str):
            out.extend(element_types(a))
        return out
    return [type_str]


def depth0(text, start, end):
    """Copy of text[start:end] with everything inside nested braces blanked (positions preserved)."""
    out, depth = [], 0
    in_str = False
    for k in range(start, end):
        c = text[k]
        if in_str:
            out.append(c if depth == 0 else " ")
            if c == "\\":
                continue
            if c == '"':
                in_str = False
            continue
        if c == '"':
            in_str = True
            out.append(c if depth == 0 else " ")
        elif c == "{":
            depth += 1
            out.append(" ")
        elif c == "}":
            depth -= 1
            out.append(" ")
        else:
            out.append(c if depth == 0 or c == "\n" else " ")
    return "".join(out)


def matching_brace(text, open_idx):
    depth, k, in_str = 0, open_idx, False
    while k < len(text):
        c = text[k]
        if in_str:
            if c == "\\":
                k += 2
                continue
            if c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return k
        k += 1
    return len(text) - 1


TYPE_RE = re.compile(r"\b(class|record|interface|enum)\s+([A-Z]\w*)")


def parse_param_list(src, text, base):
    """Parse 'a, b' parameter/component text (positions relative to base) into Fields."""
    fields, offset = [], 0
    for part in split_top_level(text):
        pos = text.index(part, offset) if part in text[offset:] else offset
        offset = pos + len(part)
        annos, k, raw = read_annotations(part)
        rest = part[k:].strip()
        rest = re.sub(r"^(?:final\s+|override\s+|private\s+|public\s+|protected\s+|internal\s+)+", "", rest)
        if src.kotlin:
            rest = re.sub(r"^(?:val|var)\s+", "", rest)
            if ":" not in rest:
                continue
            name, type_ = rest.split(":", 1)
            type_ = type_.split("=", 1)[0].strip()
            name = name.strip()
        else:
            rest = rest.split("=", 1)[0].strip()
            m = re.match(r"(.+?)\s+([A-Za-z_]\w*)$", rest, re.S)
            if not m:
                continue
            type_, name = m.group(1).strip(), m.group(2)
        fields.append(Field(name, type_, annos, src.line(base + pos), ctor_param=True, raw_annos=raw))
    return fields


def parse_types(src):
    types = []
    text = src.text
    for m in TYPE_RE.finditer(text):
        kind, name = m.group(1), m.group(2)
        # annotations right before the declaration
        back = text[max(0, m.start() - 600):m.start()]
        cut = max(back.rfind(";"), back.rfind("}"), back.rfind("{"))
        annos = [a.split(".")[-1] for a in re.findall(r"@([\w.]+)", back[cut + 1:])]
        t = TypeInfo(name, kind, src, src.line(m.start()), set(annos))
        j = m.end()
        if text.startswith("<", j):  # generics
            depth = 0
            while j < len(text):
                depth += text[j] == "<"
                depth -= text[j] == ">"
                j += 1
                if depth == 0:
                    break
        # record components / Kotlin primary constructor
        k = j
        while k < len(text) and text[k] in " \t\r\n":
            k += 1
        if k < len(text) and text[k] == "(":
            comps, end = balanced_args(text, k)
            t.fields.extend(parse_param_list(src, comps, k + 1))
            j = end
        brace = text.find("{", j)
        semi = text.find(";", j)
        if src.kotlin and brace != -1 and re.search(r"\b(class|fun|val|var|object|interface)\b|\n\s*\n",
                                                    text[j:brace]):
            brace = -1  # Kotlin class without a body: the next brace belongs to something else
        if brace != -1 and (semi == -1 or brace < semi or src.kotlin):
            close = matching_brace(text, brace)
            body = depth0(text, brace + 1, close)
            if kind in ("class", "record") and not src.kotlin:
                pos = 0
                for stmt in body.split(";"):
                    abs_start = brace + 1 + pos
                    pos += len(stmt) + 1
                    s = stmt.strip()
                    if not s:
                        continue
                    annos2, k2, raw = read_annotations(s)
                    decl = s[k2:].strip().split("=", 1)[0]
                    if "(" in decl or re.search(r"\bstatic\b", decl):
                        continue  # methods, constructors, initialisers, constants
                    rest = re.sub(r"^(?:(?:private|protected|public|final|transient|volatile)\s+)+", "",
                                  decl).strip()
                    fm = re.match(r"(.+?)\s+([A-Za-z_]\w*)$", rest, re.S)
                    if not fm or fm.group(2) in ("serialVersionUID",):
                        continue
                    lead = len(stmt) - len(stmt.lstrip())
                    t.fields.append(Field(fm.group(2), fm.group(1).strip(), annos2,
                                          src.line(abs_start + lead), raw_annos=raw))
            elif src.kotlin and kind == "class":
                for fm in re.finditer(r"((?:@[\w.:]+(?:\([^)]*\))?\s*)*)\b(?:val|var)\s+(\w+)\s*:\s*([\w.<>, ?]+)",
                                      body):
                    annos2, _, raw = read_annotations(fm.group(1))
                    t.fields.append(Field(fm.group(2), fm.group(3).strip(), annos2,
                                          src.line(brace + 1 + fm.start()), raw_annos=raw))
        types.append(t)
    return types


class Param:
    def __init__(self, field):
        self.name = field.name
        self.type = field.type
        self.annotations = field.annotations
        self.line = field.line

    def anno(self, name):
        return next((a for a in self.annotations if a[0] == name), None)


class Handler:
    def __init__(self, src, name, verbs, paths, params, return_type, line):
        self.src = src
        self.name = name
        self.verbs = verbs        # [] means "every method"
        self.paths = paths
        self.params = params
        self.return_type = return_type
        self.line = line

    def label(self):
        verbs = "/".join(self.verbs) if self.verbs else "ANY"
        return f"{verbs} {self.paths[0] if self.paths else '/'} → {self.name}"


def parse_handlers(src):
    text = src.text
    if not re.search(r"@(Rest)?Controller\b|@RequestMapping\b", text):
        return []
    tm = TYPE_RE.search(text)
    type_pos = tm.start() if tm else -1
    class_paths, class_methods, handlers = [""], [], []
    for m in MAPPING_RE.finditer(text):
        args, end = balanced_args(text, m.end())
        paths, methods = parse_mapping(m.group(1), args)
        if type_pos != -1 and m.start() < type_pos:
            class_paths, class_methods = paths, methods
            continue
        i = skip_annotations(text, end)
        sig_m = re.compile(r"(?:\bfun\s+)?([A-Za-z_]\w*)\s*\(").search(text, i)
        if not sig_m:
            continue
        params_text, pend = balanced_args(text, sig_m.end() - 1)
        if src.kotlin:
            after = text[pend:pend + 300]
            rm = re.match(r"\s*:\s*([^{=]+)", after)
            ret = rm.group(1).strip() if rm else "Unit"
        else:
            ret = re.sub(r"\b(public|protected|private|static|final|synchronized|abstract|default)\b", "",
                         text[i:sig_m.start()]).strip()
        params = [Param(f) for f in parse_param_list(src, params_text, sig_m.end())]
        full_paths = [join_paths(cp, p) for cp in class_paths for p in paths]
        verbs = methods or class_methods
        handlers.append(Handler(src, sig_m.group(1), verbs, full_paths, params, ret, src.line(m.start())))
    return handlers


# ---------------------------------------------------------------------------------------------
# Project context

def read_files(root, patterns):
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and d != "node_modules"]
        for fn in filenames:
            if any(re.fullmatch(p, fn) for p in patterns):
                try:
                    with open(os.path.join(dirpath, fn), encoding="utf-8", errors="replace") as fh:
                        out.append((os.path.join(dirpath, fn), fh.read()))
                except OSError:
                    pass
    return out


def boot_version(build_files):
    for path, text in build_files:
        m = (re.search(r"<artifactId>spring-boot-starter-parent</artifactId>\s*<version>([\d.]+)", text)
             or re.search(r"<artifactId>spring-boot-dependencies</artifactId>\s*<version>([\d.]+)", text)
             or re.search(r"org\.springframework\.boot['\"]\)?\s*version\s*['\"]([\d.]+)", text)
             or re.search(r"spring-boot-gradle-plugin:([\d.]+)", text)
             or re.search(r"springBoot\s*=\s*['\"]([\d.]+)", text))
        if m:
            return tuple(int(x) for x in m.group(1).split(".")[:2] if x.isdigit())
    return None


def is_main_source(path):
    p = path.replace(os.sep, "/")
    return "/src/test/" not in p and "/src/it/" not in p and "/test/" not in p.split("/src/")[0]


# ---------------------------------------------------------------------------------------------
# Checks

class Report:
    def __init__(self, only, skip):
        self.findings = []
        self.only = only
        self.skip = skip or set()

    def add(self, rule, severity, src_rel, line, message, fix, confidence="certain", endpoint=None):
        if (self.only and rule not in self.only) or rule in self.skip:
            return
        key = (rule, src_rel, line, message)
        if any((f["rule"], f["file"], f["line"], f["message"]) == key for f in self.findings):
            return
        self.findings.append({
            "rule": rule, "name": RULES[rule][0], "severity": severity, "confidence": confidence,
            "file": src_rel, "line": line, "endpoint": endpoint, "message": message, "fix": fix,
        })


def run_checks(root, only=None, skip=None):
    rep = Report(only, skip)
    build_files = read_files(root, [r"pom\.xml", r"build\.gradle(\.kts)?", r"libs\.versions\.toml"])
    config_files = read_files(root, [r"application.*\.(ya?ml|properties)"])
    build_text = "\n".join(t for _, t in build_files)
    config_text = "\n".join(t for _, t in config_files)
    boot = boot_version(build_files)

    sources = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            path = os.path.join(dirpath, fn)
            if fn.endswith((".java", ".kt")) and is_main_source(os.path.relpath(path, root)):
                sources.append(Source(path, root))

    types, handlers = {}, []
    for s in sources:
        for t in parse_types(s):
            types.setdefault(t.name, t)
        handlers.extend(parse_handlers(s))

    def lookup(type_str):
        return types.get(raw_type(type_str))

    deep_cache = {}

    def constrained_deep(t, seen=None):
        if t.name in deep_cache:
            return deep_cache[t.name]
        seen = seen or set()
        if t.name in seen:
            return False
        seen.add(t.name)
        result = bool(t.constraint_fields())
        if not result:
            for f in t.fields:
                for et in element_types(f.type):
                    u = lookup(et)
                    if u and u.kind != "enum" and constrained_deep(u, seen):
                        result = True
        deep_cache[t.name] = result
        return result

    # Request-reachable types (bodies and everything nested in them)
    body_types = {}
    for h in handlers:
        for p in h.params:
            if p.anno("RequestBody"):
                for et in element_types(p.type):
                    u = lookup(et)
                    if u:
                        body_types.setdefault(u.name, u)
    reachable, stack = {}, list(body_types.values())
    while stack:
        t = stack.pop()
        if t.name in reachable or t.kind == "enum":
            continue
        reachable[t.name] = t
        for f in t.fields:
            for et in element_types(f.type):
                u = lookup(et)
                if u and u.name not in reachable:
                    stack.append(u)

    uses_constraints = any(t.constraint_fields() for t in types.values()) or any(
        any(a[0] in CONSTRAINTS for a in p.annotations) for h in handlers for p in h.params)
    javax_files = [s for s in sources if re.search(r"import\s+javax\.validation\.", s.text)]
    jakarta_files = [s for s in sources if re.search(r"import\s+jakarta\.validation\.", s.text)]

    # QC01 — validation provider
    if uses_constraints and build_files and not re.search(
            r"spring-boot-starter-validation|hibernate-validator|bval-jsr|apache\.bval", build_text):
        rep.add("QC01", "error", os.path.relpath(build_files[0][0], root), 1,
                "Constraint annotations are used, but neither spring-boot-starter-validation nor another "
                "Bean Validation provider is a dependency, so @Valid does nothing and no constraint is checked.",
                "Add the org.springframework.boot:spring-boot-starter-validation dependency.")

    # QC02 — namespace
    if boot:
        wrong, ns = (javax_files, "javax") if boot >= (3, 0) else (jakarta_files, "jakarta")
        right = "jakarta" if ns == "javax" else "javax"
        for s in wrong:
            m = re.search(rf"import\s+{ns}\.validation\.", s.text)
            rep.add("QC02", "error", s.rel, s.line(m.start()),
                    f"Imports {ns}.validation, but Spring Boot {boot[0]}.{boot[1]} validates {right}.validation "
                    f"annotations only: the constraints in this file are silently ignored "
                    f"(it compiles only because a {ns}.validation jar is on the classpath).",
                    f"Change the imports to {right}.validation.*.")

    # Handler checks
    date_format_global = re.search(r"spring\.mvc\.format\.", config_text) or (
        re.search(r"^\s*mvc:\s*$", config_text, re.M) and re.search(r"^\s+format:\s*$", config_text, re.M))
    entity_returns = {}
    for h in handlers:
        rel = h.src.rel
        ep = h.label()
        bodies = [p for p in h.params if p.anno("RequestBody")]
        mismatched = False

        # QC09
        if not h.verbs and re.search(r"@RequestMapping", h.src.text) and h.paths is not None:
            rep.add("QC09", "error", rel, h.line,
                    f"{h.name} uses @RequestMapping without a method, so it answers GET, POST, PUT, PATCH, DELETE "
                    f"and HEAD alike.", "Use @GetMapping/@PostMapping/… (or set method = RequestMethod.X).",
                    endpoint=ep)

        # QC11 / QC12
        if len(bodies) > 1:
            rep.add("QC11", "error", rel, h.line,
                    f"{h.name} declares {len(bodies)} @RequestBody parameters; the body can only be read once, "
                    f"so every request fails.", "Wrap the values in one request DTO.", endpoint=ep)
        if bodies and set(h.verbs) & {"GET", "HEAD", "DELETE"}:
            rep.add("QC12", "warning", rel, bodies[0].line,
                    f"{'/'.join(h.verbs)} handler {h.name} reads a @RequestBody. HTTP gives such a body no "
                    f"defined meaning and many clients, proxies and CDNs drop it.",
                    "Move the data to the path or query, or use POST for an action that needs a payload.",
                    endpoint=ep)

        # QC03 / QC15 (request side)
        for p in bodies:
            valid = bool(p.anno("Valid") or p.anno("Validated")) or "@Valid" in p.type
            for et in element_types(p.type):
                u = lookup(et)
                if not u:
                    continue
                if u.is_entity:
                    rep.add("QC15", "error", rel, p.line,
                            f"{h.name} binds the request body straight to the JPA entity {u.name}: clients can set "
                            f"any of its fields (ids, status, ownership, timestamps).",
                            f"Bind a request DTO with only the editable fields and map it onto {u.name}.",
                            endpoint=ep)
                if not valid and constrained_deep(u):
                    rep.add("QC03", "error", rel, p.line,
                            f"{h.name} takes @RequestBody {p.type} without @Valid, so the constraints on {u.name} "
                            f"never run.", f"Annotate the parameter: @Valid @RequestBody {p.type} {p.name}.",
                            endpoint=ep)

        # QC15 (response side) — collected, reported once per entity below
        for et in element_types(h.return_type) if h.return_type else []:
            u = lookup(et)
            if u and u.is_entity:
                entity_returns.setdefault(u.name, []).append(h)

        # QC08 / QC10 / QC14
        templates = set()
        for path in h.paths:
            templates |= set(re.findall(r"\{\*?(\w+)(?::[^}]*)?\}", path))
        unresolved = any("{CONST:" in path for path in h.paths)
        bound, has_map = set(), False
        for p in h.params:
            for kind in ("RequestParam", "RequestHeader", "CookieValue"):
                a = p.anno(kind)
                if a and re.search(r"required\s*=\s*false", a[1]) and not re.search(r"defaultValue\s*=", a[1]) \
                        and raw_type(p.type) in PRIMITIVES:
                    rep.add("QC08", "error", rel, p.line,
                            f"@{kind}(required = false) {p.type} {p.name}: when the {kind[7:].lower() or 'value'} "
                            f"is absent Spring can't put null into a primitive and throws IllegalStateException "
                            f"(500).", f'Add defaultValue = "…", or use the wrapper type '
                            f'({"Integer" if raw_type(p.type) == "int" else raw_type(p.type).capitalize()}) '
                            f'or Optional<…>.', endpoint=ep)
            pv = p.anno("PathVariable")
            if pv is not None:
                if raw_type(p.type) in ("Map", "MultiValueMap"):
                    has_map = True
                    continue
                m = re.search(r'(?:^|value\s*=\s*|name\s*=\s*)"([^"]+)"', pv[1].strip())
                name = m.group(1) if m else p.name
                bound.add(name)
                if templates is not None and not unresolved and name not in templates:
                    mismatched = True
                    rep.add("QC10", "error", rel, p.line,
                            f"@PathVariable '{name}' is not in the URI template ({', '.join(h.paths)}): every "
                            f"request fails with MissingPathVariableException (500).",
                            f"Name it after the template variable, e.g. @PathVariable(\"{sorted(templates)[0]}\")"
                            if templates else "Add the variable to the mapping path.", endpoint=ep)
            rp = p.anno("RequestParam") or p.anno("PathVariable")
            if rp is not None and raw_type(p.type) in DATE_TYPES and not p.anno("DateTimeFormat") \
                    and not date_format_global:
                newer = boot is not None and boot >= (3, 2)
                rep.add("QC14", "suggestion" if newer else "warning", rel, p.line,
                        f"{raw_type(p.type)} parameter '{p.name}' has no @DateTimeFormat. "
                        + ("Spring 6.1+ falls back to ISO parsing, so ISO input binds, but the accepted formats "
                           "aren't explicit." if newer else
                           "It is parsed with a locale-dependent short style, so ISO input like 2026-11-17 fails "
                           "with 400."),
                        "Add @DateTimeFormat(iso = DateTimeFormat.ISO.DATE) (or DATE_TIME), or set "
                        "spring.mvc.format.date / date-time.", confidence="certain" if not newer else "verify",
                        endpoint=ep)
        if templates and not unresolved and not has_map and not mismatched:
            for v in sorted(templates - bound):
                rep.add("QC10", "warning", rel, h.line,
                        f"URI template variable '{v}' in {', '.join(h.paths)} is not bound to any @PathVariable "
                        f"of {h.name}.", "Bind it, or remove it from the path.", endpoint=ep)

        # QC13
        for path in h.paths:
            segments = [s for s in path.split("/") if s and not s.startswith("{")]
            if "GET" in h.verbs or not h.verbs:
                for seg in segments:
                    # whole segment only: '/cancel' is an action, '/save-games' is a resource name
                    if seg.lower() in ACTION_VERBS:
                        rep.add("QC13", "warning", rel, h.line,
                                f"GET {path} contains the action '{seg}'. If {h.name} changes state, prefetchers, "
                                f"crawlers, retries and HEAD requests will trigger it.",
                                "Check what the handler does; if it writes, use POST (action), PUT/PATCH or DELETE.",
                                confidence="verify", endpoint=ep)
            for seg in segments:
                if VERB_PREFIX_RE.match(seg):
                    rep.add("QC13", "suggestion", rel, h.line,
                            f"Path segment '{seg}' starts with a verb; the HTTP method already says what happens.",
                            "Use a noun for the resource, e.g. GET /orders instead of /getOrders.",
                            confidence="verify", endpoint=ep)

    for name, hs in entity_returns.items():
        u = types[name]
        listed = ", ".join(f"{h.name} ({h.src.rel.rsplit('/', 1)[-1]}:{h.line})" for h in hs)
        rep.add("QC15", "warning", hs[0].src.rel, hs[0].line,
                f"{len(hs)} handler(s) return the JPA entity {name}: {listed}. Its fields become the API contract; "
                f"bidirectional or lazy associations can fail at serialization; internal fields leak.",
                f"Return a response DTO built from {name}.", endpoint=hs[0].label() if len(hs) == 1 else None)

    # Type checks
    for t in types.values():
        src = t.src
        for f in t.fields:
            rt = raw_type(f.type)
            names = {a[0] for a in f.annotations}
            # QC05
            bad = []
            if names & {"NotBlank", "Pattern", "Email", "URL"} and rt not in STRING_TYPES and rt not in ("Any", "Object"):
                bad = sorted(names & {"NotBlank", "Pattern", "Email", "URL"})
            if "Size" in names and (rt in NUMERIC_TYPES or rt in BOOLEAN_TYPES or rt in DATE_TYPES):
                bad.append("Size")
            if "NotEmpty" in names and (rt in NUMERIC_TYPES or rt in BOOLEAN_TYPES or rt in DATE_TYPES):
                bad.append("NotEmpty")
            if names & {"Past", "Future", "PastOrPresent", "FutureOrPresent"} and rt in STRING_TYPES | NUMERIC_TYPES:
                bad.extend(sorted(names & {"Past", "Future", "PastOrPresent", "FutureOrPresent"}))
            for b in bad:
                rep.add("QC05", "error", src.rel, f.line,
                        f"@{b} on {t.name}.{f.name} ({f.type}) isn't supported for that type: once validation runs, "
                        f"every request with this object fails with UnexpectedTypeException (500).",
                        "Use a constraint for the type, e.g. @NotNull (plus @Positive/@Min) for numbers, "
                        "@NotBlank only on strings.")
            # QC06
            if "NotNull" in names and rt in PRIMITIVES:
                rep.add("QC06", "warning", src.rel, f.line,
                        f"@NotNull on {t.name}.{f.name} ({f.type}) can never fail: a primitive is never null, and "
                        f"a missing JSON value becomes {'false' if rt == 'boolean' else '0'}.",
                        f"Use the wrapper type ({'Boolean' if rt == 'boolean' else 'Integer' if rt == 'int' else rt.capitalize()}) "
                        f"with @NotNull.")
            # QC07
            if t.name in reachable and not t.is_entity and rt in PRIMITIVES and not src.kotlin \
                    and "NotNull" not in names:
                rep.add("QC07", "warning", src.rel, f.line,
                        f"{t.name} is (part of) a request body and {f.name} is a primitive {f.type}: when a client "
                        f"omits it (or misspells it, since unknown JSON fields are ignored) it silently becomes "
                        f"{'false' if rt == 'boolean' else '0'} and the request goes through with that value.",
                        f"Make it a wrapper type with @NotNull if it's required, or give it an explicit default.",
                        confidence="verify")
            # QC04
            if t.name in reachable and not f.has("Valid") and "@Valid" not in f.type:
                for et in element_types(f.type):
                    u = lookup(et)
                    if u and u.kind != "enum" and not u.is_entity and constrained_deep(u):
                        rep.add("QC04", "error", src.rel, f.line,
                                f"{t.name}.{f.name} ({f.type}) holds {u.name}, which has constraints, but validation "
                                f"doesn't cascade without @Valid, so they never run.",
                                f"Annotate the field with @Valid, or for collections use the element form, "
                                f"e.g. List<@Valid {u.name}>.")
            # QC17
            if re.search(r"password", f.name, re.I) and t.name in reachable and rt in STRING_TYPES and \
                    re.search(r"BCryptPasswordEncoder", "\n".join(s.text for s in sources)):
                size = f.anno("Size") or f.anno("Length")
                mx = re.search(r"max\s*=\s*(\d+)", size[1]) if size else None
                if mx and int(mx.group(1)) > 72:
                    rep.add("QC17", "warning", src.rel, f.line,
                            f"{t.name}.{f.name} allows up to {mx.group(1)} characters, but BCrypt only uses 72 bytes "
                            f"and Spring Security 6.4.4+ throws IllegalArgumentException when encoding longer input "
                            f"(500 instead of a validation error; non-ASCII characters use several bytes each).",
                            "Cap it at 72 bytes, e.g. @Size(max = 72) plus a UTF-8 byte-length check.")
            # QC19
            if src.kotlin and f.ctor_param and any(a[0] in CONSTRAINTS or a[0] == "Valid" for a in f.annotations) \
                    and not re.search(r"@(field|get):", f.raw_annos):
                rep.add("QC19", "error", src.rel, f.line,
                        f"Constraint on constructor property {t.name}.{f.name} targets the constructor parameter, "
                        f"which Bean Validation ignores.", "Use the field target, e.g. @field:NotBlank.")

    # QC16 — not-found handling
    for s in sources:
        if not re.search(r"@(Service|Component|RestController|Controller)\b", s.text):
            continue
        for m in re.finditer(r"\.orElseThrow\(\s*\)|findById\([^()]*\)\s*\.get\(\)", s.text):
            rep.add("QC16", "warning", s.rel, s.line(m.start()),
                    "A missing value throws NoSuchElementException, which no handler maps, so the client gets a "
                    "500 (or whatever /error turns it into). If this can happen for a client-supplied id, it "
                    "should be a 404.",
                    "Throw a mapped not-found exception, e.g. .orElseThrow(() -> new ResponseStatusException("
                    "HttpStatus.NOT_FOUND)) or the project's own not-found exception.", confidence="verify")

    # QC18 — error dispatch behind a stateless token filter
    sec = [s for s in sources if "SecurityFilterChain" in s.text and
           re.search(r"anyRequest\(\)\s*\.\s*authenticated\(\)", s.text)]
    all_text = "\n".join(s.text for s in sources)
    custom_filter = [s for s in sources if re.search(r"extends\s+OncePerRequestFilter|:\s*OncePerRequestFilter", s.text)
                     and re.search(r"SecurityContextHolder", s.text) and re.search(r"setAuthentication|setContext", s.text)
                     and not re.search(r"securityContextRepository|saveContext", s.text)]
    if sec and custom_filter and not re.search(r'"/error|DispatcherType\.ERROR|dispatcherTypeMatchers', all_text):
        s = sec[0]
        m = re.search(r"anyRequest\(\)\s*\.\s*authenticated\(\)", s.text)
        rep.add("QC18", "error", s.rel, s.line(m.start()),
                f"Every request needs authentication and /error isn't permitted, while {custom_filter[0].rel} only "
                f"puts the authentication in the current thread. Exceptions the advice doesn't handle are forwarded "
                f"to /error, that dispatch is anonymous, and the client gets 401 instead of the real 400/404/500. "
                f"Check how the client reacts to 401 (many log the user out).",
                "Permit the error dispatch (.dispatcherTypeMatchers(DispatcherType.ERROR).permitAll() or "
                "requestMatchers(\"/error\").permitAll()) and handle framework exceptions in the advice. Confirm "
                "with a request against a running server: MockMvc doesn't perform error dispatches.",
                confidence="verify")

    order = {s: i for i, s in enumerate(SEVERITIES)}
    rep.findings.sort(key=lambda f: (order[f["severity"]], f["file"], f["line"], f["rule"]))
    stack = {
        "spring_boot": ".".join(map(str, boot)) if boot else None,
        "validation_namespace": ("jakarta" if jakarta_files and not javax_files else
                                 "javax" if javax_files and not jakarta_files else
                                 "mixed" if javax_files and jakarta_files else None),
        "sources": len(sources), "handlers": len(handlers), "types": len(types),
    }
    return stack, rep.findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--fail-on", choices=["error", "warning", "suggestion", "never"], default="never",
                    help="exit 1 when a finding at or above this severity exists (for CI)")
    ap.add_argument("--rules", help="comma-separated rule ids to run, e.g. QC03,QC08")
    ap.add_argument("--skip", help="comma-separated rule ids to leave out, e.g. QC16")
    ap.add_argument("--list-rules", action="store_true", help="print the rules and exit")
    args = ap.parse_args()
    if args.list_rules:
        for k, (name, summary) in RULES.items():
            print(f"{k}  {name:32} {summary}")
        return
    root = os.path.abspath(args.root)
    ids = lambda s: {r.strip().upper() for r in s.split(",") if r.strip()} if s else None  # noqa: E731
    stack, findings = run_checks(root, ids(args.rules), ids(args.skip))

    if args.json:
        print(json.dumps({"root": root, "stack": stack, "findings": findings,
                          "rules": {k: {"name": v[0], "summary": v[1]} for k, v in RULES.items()}}, indent=2))
    else:
        boot = stack["spring_boot"] or "unknown"
        print(f"Spring API quick check — {root}")
        print(f"Spring Boot {boot} · validation: {stack['validation_namespace'] or 'none'} · "
              f"{stack['handlers']} handlers · {stack['types']} types\n")
        for sev in SEVERITIES:
            group = [f for f in findings if f["severity"] == sev]
            if not group:
                continue
            print(f"{sev.upper()}S ({len(group)})")
            explained = set()
            for f in sorted(group, key=lambda f: (f["rule"], f["file"], f["line"])):
                tag = " [verify]" if f["confidence"] == "verify" else ""
                print(f"  {f['rule']} {f['name']}{tag}  {f['file']}:{f['line']}")
                if f["endpoint"]:
                    print(f"      {f['endpoint']}")
                key = (f["rule"], f["message"])
                if key in explained:
                    continue  # same explanation as the previous occurrence: location only
                explained.add(key)
                print(f"      {f['message']}")
                print(f"      Fix: {f['fix']}")
            print()
        counts = {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES}
        print(f"{counts['error']} errors, {counts['warning']} warnings, {counts['suggestion']} suggestions. "
              "These are pattern matches: confirm each in the code; [verify] marks heuristics.")

    if args.fail_on != "never":
        limit = SEVERITIES.index(args.fail_on)
        if any(SEVERITIES.index(f["severity"]) <= limit for f in findings):
            sys.exit(1)


if __name__ == "__main__":
    main()
