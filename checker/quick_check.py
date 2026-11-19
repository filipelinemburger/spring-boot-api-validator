#!/usr/bin/env python3
"""Fast, deterministic checks for common Spring REST API defects.

Usage:
    python3 quick_check.py <project-root> [--json] [--fail-on error|warning|never] [--rules QC03,QC08]

Part of the spring-api-validator project (the standalone checker). Standard-library Python 3, no build or running app needed.
It reads .java/.kt sources under src/main (and the build file and application config) and reports
pattern matches with file:line, a rule id, what goes wrong at runtime and the fix.

It is a first pass, not a verdict: the patterns are exact for what they match, but they don't follow
calls into services or know the team's intent. The skill (or a reviewer) confirms each finding in the
code. Rules marked "verify" are heuristics that point at something worth a look.

Options: --format text|json|github|markdown|sarif, --diff-base REF (only files changed since the branch left
REF), --fail-on SEVERITY, --rules/--skip IDS, --list-rules.

Exit status: 0; 1 when --fail-on is set and a reported finding is at or above that severity; 2 when the
--diff-base comparison can't be computed (e.g. a shallow clone without the base commit).
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from list_endpoints import (  # noqa: E402  (shared parsing helpers)
    MAPPING_RE, SKIP_DIRS, balanced_args, join_paths, parse_mapping, read_base_paths, scan_functional,
    skip_annotations, split_top_level, strip_comments,
)
import openapi_spec  # noqa: E402

VERSION = "0.12.0"  # kept equal to the plugin version (tests/test_quick_check.py)
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
# Kotlin non-null Int/Long/... compile to JVM primitives (a trailing "?" makes them boxed and nullable)
KOTLIN_PRIMITIVES = {"Int", "Long", "Short", "Byte", "Double", "Float", "Boolean", "Char"}


def is_primitive(type_str, kotlin=False):
    t = type_str.strip()
    if kotlin:
        return not t.endswith("?") and raw_type(t) in KOTLIN_PRIMITIVES
    return raw_type(t) in PRIMITIVES
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
                "purge", "reserve"}
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
    "QC20": ("schema-limits", "Request field allows values longer or larger than the database column it's stored in"),
    "QC21": ("functional-body-not-validated", "Functional endpoint reads a body whose type has constraints but never validates it"),
    "QC22": ("blocking-in-reactive", "block() in a WebFlux application"),
    "QC23": ("empty-means-200", "Handler can return an empty Mono or null, which becomes 200 with no body instead of 404"),
    "QC25": ("spec-operation-drift", "Operation in the OpenAPI spec with no handler, or handler missing from the spec"),
    "QC26": ("spec-required-drift", "Field the spec marks required isn't enforced by the DTO (or the reverse)"),
    "QC27": ("spec-status-drift", "Success status in the spec differs from what the handler returns"),
    "QC28": ("spec-schema-drift", "Property names or types differ between the spec schema and the DTO's JSON"),
    "QC29": ("annotation-doc-drift", "springdoc annotations (@ApiResponse, @Schema required) contradict the code"),
    "QC30": ("cascade-to-shared-entity", "cascade = ALL/REMOVE on a @ManyToOne or @ManyToMany: deleting one row deletes rows others still use"),
    "QC31": ("catch-all-handler-500", "@ExceptionHandler(Exception) in an advice that doesn't extend ResponseEntityExceptionHandler turns client errors (bad JSON, wrong types, 404/405/415, 403) into 500"),
    "QC32": ("ant-matcher-trailing-slash", "Restrictive antMatchers path that Spring MVC also serves with a trailing slash, which a broader permitAll rule then lets through (Spring Security 5)"),
    "QC33": ("location-without-context-path", "Location header built from a bare path while a context path is configured: it points to the wrong URL"),
    "QC34": ("no-content-with-body", "204 No Content returned with a body: the body never reaches the client"),
    "QC35": ("empty-collection-404", "Empty list answered with 404 instead of 200 []"),
    "QC24": ("advice-skips-functional-routes", "Exception mapped in @ControllerAdvice is thrown from a functional route the advice doesn't cover (WebFlux on Spring 5, or advice scoped by package/type)"),
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



def statement_start(back):
    """Index of the last ';', '{' or '}' in back that sits outside parentheses and strings (-1 if none).

    Annotation arguments such as @Table(uniqueConstraints = {...}) or @JsonIgnoreProperties({"a"}) contain
    braces that don't end the previous declaration."""
    depth, in_str = 0, False
    for i in range(len(back) - 1, -1, -1):
        ch = back[i]
        if in_str:
            if ch == '"' and (i == 0 or back[i - 1] != "\\"):
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == ")":
            depth += 1
        elif ch == "(":
            depth = max(0, depth - 1)
        elif ch in ";{}" and depth == 0:
            return i
    return -1

def parse_types(src):
    types = []
    text = src.text
    for m in TYPE_RE.finditer(text):
        kind, name = m.group(1), m.group(2)
        # annotations right before the declaration
        back = text[max(0, m.start() - 600):m.start()]
        cut = statement_start(back)
        annos = [a.split(".")[-1] for a in re.findall(r"@([\w.]+)", back[cut + 1:])]
        t = TypeInfo(name, kind, src, src.line(m.start()), set(annos))
        tm = re.search(r'@(?:[\w.]+\.)?Table\s*\(\s*(?:[^)]*?\bname\s*=\s*)?"([^"]+)"', back[cut + 1:])
        t.table = tm.group(1) if tm else None
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
    def __init__(self, src, name, verbs, paths, params, return_type, line, body="", annos=""):
        self.src = src
        self.body = body
        self.annos = annos
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
        nxt = MAPPING_RE.search(text, pend)
        limit = nxt.start() if nxt else len(text)
        brace = text.find("{", pend, limit)
        eq = re.match(r"[^{]*?=", text[pend:limit]) if src.kotlin else None
        if eq and (brace == -1 or pend + eq.end() < brace):
            body = text[pend + eq.end():limit]               # Kotlin expression body
        elif brace != -1:
            body = text[brace:matching_brace(text, brace) + 1]
        else:
            body = ""
        block_start = max(text.rfind(";", 0, m.start()), text.rfind("}", 0, m.start()), text.rfind("{", 0, m.start())) + 1
        handlers.append(Handler(src, sig_m.group(1), verbs, full_paths, params, ret, src.line(m.start()), body,
                                text[block_start:i]))
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
# Database schema limits (Flyway/plain SQL, Liquibase XML, JPA @Column)

def snake(name):
    """Spring Boot's default physical naming: managerName -> manager_name, OrderItem -> order_item."""
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", name).lower()


def parse_col_type(type_text):
    """('varchar', length) | ('numeric', precision, scale) | None for a SQL column type."""
    t = type_text.strip().lower()
    m = re.match(r"(?:n?varchar2?|character\s+varying|varying\s+character|n?char(?:acter)?)\s*\(\s*(\d+)", t)
    if m:
        return ("varchar", int(m.group(1)))
    m = re.match(r"(?:numeric|decimal|number|dec)\s*\(\s*(\d+)\s*(?:,\s*(\d+))?\s*\)", t)
    if m:
        return ("numeric", int(m.group(1)), int(m.group(2) or 0))
    return None


def _ident(s):
    return s.strip().strip('"`[]').split(".")[-1].strip('"`[]').lower()


def parse_sql_schema(text, rel, schema):
    """Apply CREATE TABLE / ALTER TABLE statements in order to `schema` {(table, column): (limit, source)}."""
    text = re.sub(r"--[^\n]*", lambda m: " " * len(m.group(0)), text)
    text = re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group(0)), text, flags=re.S)
    line_of = lambda pos: text.count("\n", 0, pos) + 1  # noqa: E731
    ident = r'("[^"]+"|`[^`]+`|\[[^\]]+\]|[\w.]+)'
    for m in re.finditer(rf"create\s+(?:temporary\s+)?table\s+(?:if\s+not\s+exists\s+)?{ident}\s*\(", text, re.I):
        table = _ident(m.group(1))
        body, _ = balanced_args(text, m.end() - 1)
        for part in split_top_level(body):
            p = part.strip()
            if not p or re.match(r"(constraint|primary|unique|foreign|check|index|key|exclude)\b", p, re.I):
                continue
            cm = re.match(ident + r"\s+(.+)", p, re.S)
            if cm:
                limit = parse_col_type(cm.group(2))
                if limit:
                    schema[(table, _ident(cm.group(1)))] = (limit, f"{rel}:{line_of(text.find(p, m.start()))}")
    for m in re.finditer(rf"alter\s+table\s+(?:if\s+exists\s+)?(?:only\s+)?{ident}\s+(.*?);", text, re.I | re.S):
        table, actions = _ident(m.group(1)), m.group(2)
        src_line = f"{rel}:{line_of(m.start())}"
        for act in split_top_level(actions):
            a = act.strip()
            am = re.match(rf"add\s+(?:column\s+)?(?:if\s+not\s+exists\s+)?{ident}\s+(.+)", a, re.I | re.S)
            if am and not re.match(r"(constraint|primary|unique|foreign|check|index)\b", am.group(1), re.I):
                limit = parse_col_type(am.group(2))
                if limit:
                    schema[(table, _ident(am.group(1)))] = (limit, src_line)
                continue
            am = re.match(rf"(?:alter|modify)\s+(?:column\s+)?{ident}\s+(?:set\s+data\s+)?(?:type\s+)?(.+)", a, re.I | re.S)
            if am:
                limit = parse_col_type(am.group(2))
                if limit:
                    schema[(table, _ident(am.group(1)))] = (limit, src_line)
                continue
            am = re.match(rf"rename\s+column\s+{ident}\s+to\s+{ident}", a, re.I)
            if am and (table, _ident(am.group(1))) in schema:
                schema[(table, _ident(am.group(2)))] = schema.pop((table, _ident(am.group(1))))


def parse_liquibase_xml(text, rel, schema):
    for tag in re.finditer(r"<(createTable|addColumn|modifyDataType)\b([^>]*?)(/?)>", text, re.S):
        kind, attrs = tag.group(1), tag.group(2)
        tm = re.search(r'tableName\s*=\s*"([^"]+)"', attrs)
        if not tm:
            continue
        table = tm.group(1).lower()
        line = f"{rel}:{text.count(chr(10), 0, tag.start()) + 1}"
        if kind == "modifyDataType":
            cm = re.search(r'columnName\s*=\s*"([^"]+)"', attrs)
            ty = re.search(r'newDataType\s*=\s*"([^"]+)"', attrs)
            if cm and ty and parse_col_type(ty.group(1)):
                schema[(table, cm.group(1).lower())] = (parse_col_type(ty.group(1)), line)
            continue
        if tag.group(3):  # self-closing <createTable …/> has no columns
            continue
        close = text.find(f"</{kind}>", tag.end())
        body = text[tag.end():close if close != -1 else len(text)]
        for col in re.finditer(r"<column\b([^>]*)>", body):
            nm = re.search(r'\bname\s*=\s*"([^"]+)"', col.group(1))
            ty = re.search(r'\btype\s*=\s*"([^"]+)"', col.group(1))
            if nm and ty and parse_col_type(ty.group(1)):
                schema[(table, nm.group(1).lower())] = (parse_col_type(ty.group(1)), line)


def load_schema(root):
    """Column limits from migrations, applied in version order (V1__, V2__, … then the rest)."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        parts = os.path.relpath(dirpath, root).replace(os.sep, "/").split("/")
        if "test" in parts or not ("main" in parts or "db" in parts or "migration" in parts or "changelog" in parts):
            continue  # migrations live under src/main/resources (or a top-level db/ folder), never in tests
        rel_dir = "/".join(parts)
        for fn in filenames:
            if fn.endswith(".sql") or (fn.endswith(".xml") and ("changelog" in fn.lower() or "liquibase" in rel_dir.lower()
                                                                or "changelog" in rel_dir.lower())):
                files.append(os.path.join(dirpath, fn))

    def order(path):
        m = re.match(r"V(\d+(?:[._]\d+)*)__", os.path.basename(path))
        return (0, [int(x) for x in re.split(r"[._]", m.group(1))]) if m else (1, [os.path.basename(path)])

    schema = {}
    for path in sorted(files, key=order):
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            continue
        rel = os.path.relpath(path, root)
        if path.endswith(".sql"):
            parse_sql_schema(text, rel, schema)
        else:
            parse_liquibase_xml(text, rel, schema)
    return schema


def describe_limit(limit):
    if limit[0] == "varchar":
        return f"VARCHAR({limit[1]})"
    return f"NUMERIC({limit[1]},{limit[2]})"


def narrower(a, b):
    """The more restrictive of two limits of the same kind."""
    if a is None or a[0] != b[0]:
        return b if a is None else a
    if a[0] == "varchar":
        return a if a[1] <= b[1] else b
    return a if (a[1] - a[2], a[2]) <= (b[1] - b[2], b[2]) else b



# ---------------------------------------------------------------------------------------------
# OpenAPI drift helpers

HTTP_STATUS = {"OK": 200, "CREATED": 201, "ACCEPTED": 202, "NO_CONTENT": 204, "RESET_CONTENT": 205,
               "PARTIAL_CONTENT": 206, "MOVED_PERMANENTLY": 301, "FOUND": 302, "SEE_OTHER": 303,
               "NOT_MODIFIED": 304, "BAD_REQUEST": 400, "NOT_FOUND": 404, "CONFLICT": 409}


def success_statuses(h):
    """Success statuses a handler can return, or None when the code doesn't say (e.g. a computed status)."""
    m = re.search(r"@ResponseStatus\s*\(\s*(?:(?:code|value)\s*=\s*)?(?:HttpStatus\.)?(\w+)", h.annos)
    if m and m.group(1) in HTTP_STATUS:
        return {HTTP_STATUS[m.group(1)]}
    found = set()
    for pat, code in ((r"\.created\s*\(", 201), (r"\.noContent\s*\(", 204), (r"\.accepted\s*\(", 202),
                      (r"ResponseEntity\s*\.\s*ok\b", 200), (r"ResponseEntity\s*\.\s*of\s*\(", 200)):
        if re.search(pat, h.body):
            found.add(code)
    for m in re.finditer(r"(?:\.status|ResponseEntity\s*(?:<[^>]*>)?\s*\()\s*\(?[^;]*?HttpStatus\.(\w+)", h.body):
        if m.group(1) in HTTP_STATUS and HTTP_STATUS[m.group(1)] < 300:
            found.add(HTTP_STATUS[m.group(1)])
    for m in re.finditer(r"\.status\s*\(\s*(2\d\d)\s*\)", h.body):
        found.add(int(m.group(1)))
    if found:
        return found
    rt = raw_type(h.return_type or "")
    args = type_args(h.return_type or "")
    if rt == "ResponseEntity" or (args and raw_type(args[0]) == "ResponseEntity"):
        return None  # built from a variable or helper we can't see
    return {200}


def norm_path(p):
    p = re.sub(r"\{[^}]*\}", "{}", p or "/")
    p = re.sub(r"/+", "/", p)
    return p.rstrip("/") or "/"


def json_name(f, snake_case):
    a = f.anno("JsonProperty")
    if a:
        m = re.search(r'"([^"]+)"', a[1])
        if m:
            return m.group(1)
    return snake(f.name) if snake_case else f.name


def schema_kind(schema):
    t = (schema or {}).get("type")
    if t:
        return str(t)
    if "$ref" in (schema or {}) or "allOf" in (schema or {}) or "properties" in (schema or {}):
        return "object"
    return None


def java_kind(type_str):
    rt = raw_type(type_str)
    if rt in STRING_TYPES or rt in DATE_TYPES or rt in ("UUID", "URI", "URL", "Char", "char", "Character"):
        return "string"
    if rt in ("int", "long", "short", "byte", "Integer", "Long", "Short", "Byte", "BigInteger", "Int"):
        return "integer"
    if rt in ("double", "float", "Double", "Float"):
        return "number"
    if rt in BOOLEAN_TYPES:
        return "boolean"
    if rt in COLLECTION_TYPES - {"Map", "MutableMap"} or type_str.strip().endswith("[]"):
        return "array"
    return None  # BigDecimal (number or string), enums, objects: don't judge


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



def pattern_max_length(regex):
    """Longest string a simple regex can match, or None when unbounded or too complex to tell.

    Handles literals, escapes, character classes, groups, alternation and ?, {n}, {n,m} quantifiers —
    enough for codes like [A-Z]{3}, \\d{4,6} or (EUR|USD)."""
    i, n = 0, len(regex)

    def alternation():
        nonlocal i
        best = sequence()
        while i < n and regex[i] == "|":
            i += 1
            other = sequence()
            best = None if best is None or other is None else max(best, other)
        return best

    def sequence():
        nonlocal i
        total = 0
        while i < n and regex[i] not in "|)":
            unit = atom()
            if unit is None:
                return None
            if i < n and regex[i] in "*+":
                return None
            if i < n and regex[i] == "?":
                i += 1
            elif i < n and regex[i] == "{":
                m = re.match(r"\{(\d+)(?:,(\d*))?\}", regex[i:])
                if not m or (m.group(2) == ""):
                    return None
                unit *= int(m.group(2) or m.group(1))
                i += m.end()
            if i < n and regex[i] in "?+" and regex[i - 1] in "?}":
                i += 1  # lazy/possessive suffix
            total += unit
        return total

    def atom():
        nonlocal i
        c = regex[i]
        if c in "^$":
            i += 1
            return 0
        if c == "\\":
            i += 2
            return 1
        if c == "[":
            j = i + 1
            if j < n and regex[j] == "^":
                j += 1
            if j < n and regex[j] == "]":
                j += 1
            while j < n and regex[j] != "]":
                j += 2 if regex[j] == "\\" else 1
            if j >= n:
                return None
            i = j + 1
            return 1
        if c == "(":
            i += 1
            if regex.startswith("?:", i):
                i += 2
            inner = alternation()
            if inner is None or i >= n or regex[i] != ")":
                return None
            i += 1
            return inner
        i += 1
        return 1

    try:
        result = alternation()
    except IndexError:
        return None
    return result if i == n else None


def split_top(args):
    """Split call arguments on top-level commas."""
    parts, depth, cur, in_str = [], 0, "", False
    for ch in args:
        if in_str:
            cur += ch
            if ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "([{<":
            depth += 1
        elif ch in ")]}>":
            depth -= 1
        elif ch == "," and depth == 0:
            parts.append(cur.strip())
            cur = ""
            continue
        cur += ch
    if cur.strip():
        parts.append(cur.strip())
    return parts

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
        if t.is_entity:
            continue  # an entity bound as a body is QC15's finding; don't treat its graph as request DTOs
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
                    required = any(a[0] in ("NotNull", "NotBlank", "NotEmpty") for f in u.fields for a in f.annotations)
                    fix = (f"Annotate the parameter: @Valid @RequestBody {p.type} {p.name}."
                           if not (h.verbs == ["PATCH"] and required) else
                           f"For a partial update, @Valid on {u.name} would also require its @NotNull fields: validate "
                           f"the merged entity before saving, or bind a PATCH DTO (or validation group) without them.")
                    rep.add("QC03", "error", rel, p.line,
                            f"{h.name} takes @RequestBody {p.type} without @Valid, so the constraints on {u.name} "
                            f"never run: invalid values reach the service and the database.", fix, endpoint=ep)

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
                        and is_primitive(p.type, h.src.kotlin):
                    rep.add("QC08", "error", rel, p.line,
                            f"@{kind}(required = false) {p.type} {p.name}: when the {kind[7:].lower() or 'value'} "
                            f"is absent Spring can't put null into a primitive and throws IllegalStateException "
                            f"(500).",
                            (f'Add defaultValue = "…", or make it nullable ({raw_type(p.type)}?).' if h.src.kotlin else
                             f'Add defaultValue = "…", or use the wrapper type '
                             f'({"Integer" if raw_type(p.type) == "int" else raw_type(p.type).capitalize()}) '
                             f'or Optional<…>.'), endpoint=ep)
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
            if rp is not None and raw_type(p.type) in DATE_TYPES - {"Instant"} and not p.anno("DateTimeFormat") \
                    and not date_format_global:
                newer = boot is not None and boot >= (3, 0)  # ISO fallback since Spring 6.0
                rep.add("QC14", "suggestion" if newer else "warning", rel, p.line,
                        f"{raw_type(p.type)} parameter '{p.name}' has no @DateTimeFormat. "
                        + ("Spring 6.0+ falls back to ISO parsing, so ISO input binds, but the accepted formats "
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
            if "NotNull" in names and rt in PRIMITIVES and not t.is_entity:
                rep.add("QC06", "warning", src.rel, f.line,
                        f"@NotNull on {t.name}.{f.name} ({f.type}) can never fail: a primitive is never null, and "
                        f"a missing JSON value becomes {'false' if rt == 'boolean' else '0'}.",
                        f"Use the wrapper type ({'Boolean' if rt == 'boolean' else 'Integer' if rt == 'int' else rt.capitalize()}) "
                        f"with @NotNull.")
            # QC07
            if t.name in reachable and not t.is_entity and rt in PRIMITIVES and not src.kotlin \
                    and "NotNull" not in names:
                rep.add("QC07", "suggestion" if rt == "boolean" else "warning", src.rel, f.line,
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
                    not re.search(r"Login|Credentials|SignIn|Auth(?:entication)?Request", t.name) and \
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

    # QC20 — request limits vs. database columns
    schema = load_schema(root)
    column_limits = {}  # field name -> [(limit, entity, "table.column", source)]
    for t in types.values():
        if not t.is_entity:
            continue
        table = (t.table or snake(t.name)).lower()
        for f in t.fields:
            col_anno = f.anno("Column")
            col = snake(f.name)
            limit, source = None, None
            if col_anno:
                nm = re.search(r'\bname\s*=\s*"([^"]+)"', col_anno[1])
                col = nm.group(1).lower() if nm else col
                ln = re.search(r"\blength\s*=\s*(\d+)", col_anno[1])
                pr = re.search(r"\bprecision\s*=\s*(\d+)", col_anno[1])
                sc = re.search(r"\bscale\s*=\s*(\d+)", col_anno[1])
                if ln:
                    limit, source = ("varchar", int(ln.group(1))), f"{t.src.rel}:{f.line}"
                elif pr:
                    limit, source = ("numeric", int(pr.group(1)), int(sc.group(1)) if sc else 0), f"{t.src.rel}:{f.line}"
            if (table, col) in schema:
                db_limit, db_source = schema[(table, col)]
                if narrower(limit, db_limit) is db_limit:
                    limit, source = db_limit, db_source
            if limit:
                column_limits.setdefault(f.name, []).append((limit, t.name, f"{table}.{col}", source))

    for t in reachable.values():
        # Entities are QC15's job; lookup-only bodies (login, search, filters) never write their values.
        if t.is_entity or re.search(r"Login|Search|Filter|Query|Criteria|Lookup|Credentials", t.name):
            continue
        for f in t.fields:
            if re.search(r"(?i)password|passwd|secret", f.name):
                continue  # stored as a hash, never as typed
            rt = raw_type(f.type)
            kind = "varchar" if rt in STRING_TYPES else "numeric" if rt in NUMERIC_TYPES else None
            cands = [c for c in column_limits.get(f.name, []) if c[0][0] == kind]
            if not kind or not cands:
                continue
            linked = [c for c in cands if c[1] in t.name]
            if not linked and kind == "varchar":
                # Strings matched by field name only are too often codes the service validates against a fixed
                # list before storing; numbers matched by name (money copied into a narrower column) stay in.
                continue
            pool, confidence = (linked, "certain") if linked else (cands, "verify")
            best = None
            for c in pool:
                if best is None or narrower(best[0], c[0]) is c[0]:
                    best = c
            limit, entity, column, source = best
            others = "" if linked or len(cands) == 1 else \
                f" (narrowest of {len(cands)} columns named after '{f.name}': {', '.join(c[2] for c in cands)})"
            if kind == "varchar":
                size = f.anno("Size") or f.anno("Length")
                mx = re.search(r"max\s*=\s*(\d+)", size[1]) if size else None
                if mx and int(mx.group(1)) <= limit[1]:
                    continue
                pattern = f.anno("Pattern")
                rx = re.search(r'regexp\s*=\s*"((?:[^"\\]|\\.)*)"', pattern[1]) if pattern else None
                plen = pattern_max_length(rx.group(1).encode().decode("unicode_escape")) if rx else None
                if plen is not None and plen <= limit[1]:
                    continue  # @Pattern matches the whole value, so a bounded regex bounds the length
                allowed = f"up to {mx.group(1)} characters" if mx else "any length"
                rep.add("QC20", "warning", t.src.rel, f.line,
                        f"{t.name}.{f.name} allows {allowed}, but it is stored in {column} {describe_limit(limit)} "
                        f"({source}){others}. Longer input passes validation and then fails when the row is written: "
                        f"a database error (500, or whatever the advice maps it to) instead of a 400.",
                        f"Add @Size(max = {limit[1]}) (or the column's real limit) so validation rejects it with a 400.",
                        confidence=confidence)
            else:
                whole = limit[1] - limit[2]
                digits = f.anno("Digits")
                dint = re.search(r"integer\s*=\s*(\d+)", digits[1]) if digits else None
                bounded = bool(dint and int(dint.group(1)) <= whole)
                for name in ("DecimalMax", "Max"):
                    a = f.anno(name)
                    v = re.search(r'(?:value\s*=\s*)?"?(-?[\d.]+)"?', a[1]) if a else None
                    if v:
                        try:
                            bounded = bounded or float(v.group(1)) < 10 ** whole
                        except ValueError:
                            pass
                if bounded:
                    continue
                biggest = ("9" * whole or "0") + ("." + "9" * limit[2] if limit[2] else "")
                rep.add("QC20", "warning", t.src.rel, f.line,
                        f"{t.name}.{f.name} has no upper bound, but it is stored in {column} {describe_limit(limit)} "
                        f"({source}){others}, which holds at most {biggest}. A larger value passes validation and then "
                        f"overflows when the row is written — possibly later, in another request or a batch job that "
                        f"copies it there.",
                        f"Add @Digits(integer = {whole}, fraction = {limit[2]}) or @DecimalMax(\"{biggest}\").",
                        confidence=confidence)

    # Reactive and functional endpoints (WebFlux, WebMvc.fn)
    webflux = bool(re.search(r"spring-boot-starter-webflux", build_text)) and not re.search(
        r"spring-boot-starter-web(?![\w-])", build_text)
    all_src = "\n".join(s.text for s in sources)

    # QC21 — functional endpoints don't run Bean Validation on bodies
    body_read = re.compile(r"(?:bodyToMono|bodyToFlux|body|awaitBody|awaitBodyOrNull)"
                           r"(?:\s*\(\s*(\w+)(?:\.class|::class(?:\.java)?)\s*\)|\s*<\s*(\w+)\s*>\s*\(\s*\))")
    for s in sources:
        if "ServerRequest" not in s.text:
            continue
        validates = re.search(r"\bValidator\b|\.validate\s*\(|SmartValidator|ValidatorFactory", s.text)
        for m in body_read.finditer(s.text):
            u = types.get(m.group(1) or m.group(2))
            if u and not validates and constrained_deep(u):
                rep.add("QC21", "error", s.rel, s.line(m.start()),
                        f"This functional handler reads a {u.name} body, which has constraints, but functional "
                        f"endpoints don't run Bean Validation (there's no @Valid), so they never apply.",
                        "Inject a jakarta.validation.Validator (or Spring's Validator) and validate the body before "
                        "using it, turning violations into a 400 (e.g. ServerWebInputException).")

    # QC22 — blocking on the event loop
    if webflux:
        for s in sources:
            if re.search(r"CommandLineRunner|ApplicationRunner|@Scheduled|@SpringBootApplication", s.text):
                continue
            web = re.search(r"@(Rest)?Controller\b|ServerRequest", s.text)
            if not (web or re.search(r"@(Service|Component)\b", s.text)):
                continue
            for m in re.finditer(r"\.block(?:First|Last|Optional)?\s*\(|\.toFuture\(\)\s*\.(?:get|join)\(", s.text):
                rep.add("QC22", "error", s.rel, s.line(m.start()),
                        "block() in a WebFlux application. On a request (event-loop) thread Reactor refuses it "
                        "with IllegalStateException (\"block() ... not supported in thread reactor-http-nio\"), so "
                        "the request fails with 500; elsewhere it stalls a thread the server needs.",
                        "Stay reactive: replace the block() with flatMap/map on the Mono and return it.",
                        confidence="certain" if web else "verify")

    # QC23 — "not found" becomes 200 with an empty body
    for h in handlers:
        if h.verbs and "GET" not in h.verbs:
            continue
        rt = raw_type(h.return_type or "")
        args = type_args(h.return_type or "")
        lookup_call = re.search(r"\bfind\w*\(|\bget\w*OrNull\(|OrNull\(", h.body)
        guarded = re.search(r"switchIfEmpty|defaultIfEmpty|notFound|NotFound|Mono\.error|ResponseStatusException"
                            r"|orElseThrow|\?:\s*throw|throw\s", h.body)
        if rt == "Mono" and args and raw_type(args[0]) not in ("ResponseEntity", "ServerResponse", "Void") \
                and lookup_call and not guarded:
            rep.add("QC23", "warning", h.src.rel, h.line,
                    f"{h.name} returns {h.return_type} from a lookup without switchIfEmpty: when nothing is found the "
                    f"Mono completes empty and WebFlux answers 200 with no body instead of 404.",
                    "Add .switchIfEmpty(Mono.error(new ResponseStatusException(HttpStatus.NOT_FOUND))) or map to "
                    "ResponseEntity with .defaultIfEmpty(ResponseEntity.notFound().build()).",
                    confidence="verify", endpoint=h.label())
        elif h.src.kotlin and (h.return_type or "").strip().endswith("?") and lookup_call and not guarded:
            rep.add("QC23", "warning", h.src.rel, h.line,
                    f"{h.name} returns a nullable {h.return_type}: when the lookup finds nothing it returns null and "
                    f"Spring answers 200 with an empty body instead of 404.",
                    "Return a non-null type and throw a not-found exception (?: throw …), or return ResponseEntity.",
                    confidence="verify", endpoint=h.label())

    # QC24 — @ControllerAdvice and functional endpoints. Global advice covers functional handlers in WebFlux
    # since Spring 6.0 and in WebMvc.fn since 5.3; it doesn't on WebFlux 5.x, and scoped advice never does.
    advised = set()
    old_webflux = webflux and boot is not None and boot < (3, 0)
    for s in sources:
        am = re.search(r"@(?:Rest)?ControllerAdvice\b(\s*\([^)]*\))?", s.text)
        if not am:
            continue
        scoped = bool(am.group(1) and re.search(r"basePackages|basePackageClasses|assignableTypes|annotations|"
                                                r"\(\s*\"", am.group(1)))
        if old_webflux or scoped:
            for m in re.finditer(r"@ExceptionHandler\s*\(([^)]*)\)", s.text):
                advised |= set(re.findall(r"(\w+)(?:\.class|::class)", m.group(1)))
    if advised:
        for s in sources:
            if "ServerRequest" not in s.text or not re.search(r"ServerResponse", s.text):
                continue
            for name in sorted(advised):
                u = types.get(name)
                if u and "ResponseStatus" in u.annotations:
                    continue  # @ResponseStatus on the exception still applies
                m = re.search(rf"(?:\bnew\s+|\bthrow\s+|\berror\s*\(\s*|\(\s*){name}\s*\(", s.text)
                if m:
                    rep.add("QC24", "warning", s.rel, s.line(m.start()),
                            f"{name} is mapped by an @ExceptionHandler in a @ControllerAdvice, but this functional "
                            f"handler throws it and that advice doesn't cover functional routes here "
                            f"({'WebFlux on Spring 5.x' if old_webflux else 'the advice is scoped by package, type or annotation'}). "
                            f"It reaches the default error handling: 500 instead of the status the advice gives.",
                            "Handle it in the route (.onError(…) / onErrorResume in the handler, or a "
                            "HandlerFilterFunction), or give the exception @ResponseStatus.",
                            confidence="verify")


    # QC25–QC28 — OpenAPI spec vs. code
    snake_case = bool(re.search(r"property-naming-strategy\s*[:=]\s*['\"]?(SNAKE_CASE|snake_case|"
                                r"com\.fasterxml\.jackson\.databind\.PropertyNamingStrategies\.SnakeCaseStrategy)",
                                config_text))

    def enforced(f, src):
        names = {a[0] for a in f.annotations}
        if names & {"NotNull", "NotBlank", "NotEmpty"}:
            return True
        t = f.type.strip()
        return src.kotlin and not t.endswith("?") and raw_type(t) not in KOTLIN_PRIMITIVES

    compared = {}

    def fields_by_json(t):
        return {json_name(f, snake_case): f for f in t.fields if not f.has("JsonIgnore")}

    def compare_schema(spec, op_label, schema, t, side, where_rel, where_line):
        sch = spec.resolve(schema or {})
        props = sch.get("properties") or {}
        if not props or not t or t.kind == "enum":
            return
        dto = fields_by_json(t)
        sname = sch.get("x-name") or "inline schema"
        pair = (spec.rel, sname, t.name, side)
        if sch.get("x-name") and pair in compared:
            compared[pair].append(op_label)
            return  # same schema and DTO already compared for another operation
        compared[pair] = [op_label]
        missing = [p for p in props if p not in dto]
        if missing:
            effect = ("clients sending them have them silently ignored" if side == "request"
                      else "clients expecting them never receive them")
            rep.add("QC28", "warning", t.src.rel, t.line,
                    f"{op_label}: the spec's {side} schema {sname} has {', '.join(missing)}, which {t.name} doesn't "
                    f"have{' (JSON names after snake_case)' if snake_case else ''} — {effect}.",
                    "Rename the DTO field (or @JsonProperty) to match the spec, or fix the spec.")
        extra = [n for n in dto if n not in props]
        if extra:
            rep.add("QC28", "suggestion", t.src.rel, t.line,
                    f"{op_label}: {t.name} has {', '.join(extra)}, which the spec's {side} schema {sname} doesn't "
                    f"document.", "Add them to the spec (or drop them from the DTO).")
        for name, ps in props.items():
            f = dto.get(name)
            if not f:
                continue
            want, have = schema_kind(spec.resolve(ps) if "$ref" in (ps or {}) else ps), java_kind(f.type)
            if want and have and want != have and not (want == "number" and have == "integer"):
                rep.add("QC28", "warning", t.src.rel, f.line,
                        f"{op_label}: '{name}' is {want} in the spec but {have} ({f.type}) in {t.name}.",
                        "Align the type in the spec or the DTO; generated clients rely on it.")
        if side == "request":
            required = list(sch.get("required") or [])
            for r in required:
                f = dto.get(r)
                if f and not enforced(f, t.src):
                    rep.add("QC26", "warning", t.src.rel, f.line,
                            f"{op_label}: the spec marks '{r}' required, but {t.name}.{f.name} isn't enforced "
                            f"(no @NotNull/@NotBlank/@NotEmpty), so requests without it are accepted.",
                            "Add the constraint (and @Valid on the body), or drop it from the spec's required list.")
            undocumented = [n for n, f in dto.items() if n in props and n not in required and
                            {a[0] for a in f.annotations} & {"NotNull", "NotBlank", "NotEmpty"}]
            if undocumented:
                rep.add("QC26", "suggestion", t.src.rel, t.line,
                        f"{op_label}: {t.name} requires {', '.join(undocumented)}, but the spec doesn't list "
                        f"{'it' if len(undocumented) == 1 else 'them'} as required.",
                        "Add them to the schema's required list so clients know.")

    bases = read_base_paths(root)
    ctx = ""
    for key in ("server.servlet.context-path", "spring.webflux.base-path", "spring.mvc.servlet.path"):
        if bases.get(key):
            ctx += bases[key][0][0].rstrip("/")
    functional = []
    for s in sources:
        functional += scan_functional(s.path, root)

    for spec, spec_rel, err in openapi_spec.load_specs(root):
        if err:
            continue
        code_eps = [(v, p, h) for h in handlers for v in (h.verbs or ["ANY"]) for p in h.paths]
        code_eps += [(e["method"], e["path"], None) for e in functional]
        best = None
        for cpre in {ctx, ""}:
            for spre in {spec.base_path, ""}:
                code_keys = {(v, norm_path(cpre + p)) for v, p, _ in code_eps}
                hits = sum((m, norm_path(spre + p)) in code_keys or ("ANY", norm_path(spre + p)) in code_keys
                           for m, p, _, _ in spec.operations())
                if best is None or hits > best[0]:
                    best = (hits, cpre, spre)
        _, cpre, spre = best
        index = {}
        for v, p, h in code_eps:
            index.setdefault((v, norm_path(cpre + p)), h)
        matched_code = set()
        for method, path, op, line in spec.operations():
            key = (method, norm_path(spre + path))
            if key not in index and ("ANY", key[1]) not in index:
                rep.add("QC25", "error", spec_rel, line,
                        f"The spec documents {method} {spre + path}, but no handler serves it — clients built from "
                        f"the spec get 404/405.", "Implement it, or remove/update it in the spec.")
                continue
            h = index.get(key) or index.get(("ANY", key[1]))
            matched_code.add(key if key in index else ("ANY", key[1]))
            if h is None:
                continue  # functional route: no handler model to compare
            label = f"{method} {spre + path}"
            want = spec.success_codes(op)
            have = success_statuses(h)
            if want and have and not (have & set(want)):
                rep.add("QC27", "warning", h.src.rel, h.line,
                        f"{label}: the spec documents {'/'.join(map(str, sorted(set(want))))} but {h.name} returns "
                        f"{'/'.join(map(str, sorted(have)))}.",
                        "Return the documented status (e.g. ResponseEntity.created(…) / @ResponseStatus) or fix "
                        "the spec.", endpoint=h.label())
            body = next((p for p in h.params if p.anno("RequestBody")), None)
            if body:
                for et in element_types(body.type):
                    u = lookup(et)
                    if u and not u.is_entity:
                        compare_schema(spec, label, spec.request_schema(op), u, "request", u.src.rel, u.line)
            for et in element_types(h.return_type or ""):
                u = lookup(et)
                if u and raw_type(et) not in WRAPPER_TYPES:
                    compare_schema(spec, label, spec.success_schema(op), u, "response", u.src.rel, u.line)
        undocumented = [(v, p, h) for v, p, h in code_eps if (v, norm_path(cpre + p)) not in matched_code]
        for v, p, h in undocumented[:15]:
            rep.add("QC25", "suggestion", h.src.rel if h else spec_rel, h.line if h else 1,
                    f"{v} {cpre + p} isn't documented in {spec_rel}.", "Document it in the spec (or confirm it's "
                    "meant to be internal).", endpoint=h.label() if h else None)

    # QC29 — springdoc annotations that contradict the code
    for h in handlers:
        documented = {int(c) for c in re.findall(r'@ApiResponse\s*\([^)]*responseCode\s*=\s*"(2\d\d)"', h.annos)}
        have = success_statuses(h)
        if documented and have and not (have & documented):
            rep.add("QC29", "warning", h.src.rel, h.line,
                    f"{h.name} documents {'/'.join(map(str, sorted(documented)))} with @ApiResponse but returns "
                    f"{'/'.join(map(str, sorted(have)))}.", "Make the annotation and the returned status agree.",
                    endpoint=h.label())
    for t in reachable.values():
        for f in t.fields:
            a = f.anno("Schema")
            if a and re.search(r"requiredMode\s*=\s*(?:Schema\.)?RequiredMode\.REQUIRED|required\s*=\s*true", a[1]) \
                    and not enforced(f, t.src):
                rep.add("QC29", "warning", t.src.rel, f.line,
                        f"{t.name}.{f.name} is documented as required (@Schema) but nothing enforces it, so the "
                        f"generated docs promise a check the API doesn't make.",
                        "Add @NotNull/@NotBlank (and @Valid on the body), or drop the required flag.")

    # QC30 — cascading removal into the "one" side of a many-to-one (or across a many-to-many)
    deletes = any("DELETE" in h.verbs for h in handlers) or any(
        re.search(r"\.(?:delete|deleteById|deleteAll|deleteAllById|remove)\s*\(", s.text) for s in sources)
    for t in types.values():
        if not t.is_entity:
            continue
        for f in t.fields:
            for kind in ("ManyToOne", "ManyToMany"):
                a = f.anno(kind)
                cm = re.search(r"\bcascade\s*=\s*[\[{]?[^)]*?\b(?:CascadeType\.)?(ALL|REMOVE)\b", a[1]) if a else None
                if not cm:
                    continue
                target = re.sub(r".*<\s*([\w.]+)\s*>.*", r"\1", f.type).split(".")[-1].rstrip("?")
                what = (f"the {target} it points to, which every other {t.name} that uses it still references"
                        if kind == "ManyToOne" else
                        f"every {target} in {f.name}, though other rows (and other {t.name}s) can still use them")
                rep.add("QC30", "error" if deletes else "warning", t.src.rel, f.line,
                        f"{t.name}.{f.name} is @{kind} with cascade {cm.group(1)}: removing a {t.name} also removes "
                        f"{what}. Depending on the foreign keys, the delete fails (constraint violation: a 500 or "
                        f"whatever the advice maps it to) or silently deletes the other rows too (ON DELETE CASCADE)."
                        + ("" if deletes else " No delete was found in the code, so this matters once something "
                           f"removes a {t.name}."),
                        f"Drop REMOVE/ALL from the cascade on {t.name}.{f.name} (keep PERSIST/MERGE if needed); "
                        f"cascade removal belongs on compositions (@OneToMany/@OneToOne to rows only this one owns).")

    controllers = [x for x in sources if re.search(r"@(RestController|Controller)\b", x.text)]

    # QC31 — a catch-all handler that turns framework 4xx into 500
    framework_4xx = [
        ("HttpMessageNotReadableException", "malformed or unreadable JSON (400)"),
        ("MethodArgumentTypeMismatchException", "a parameter of the wrong type, e.g. /owners/abc (400)"),
        ("MissingServletRequestParameterException", "a missing required parameter (400)"),
        ("HttpRequestMethodNotSupportedException", "a wrong HTTP method (405)"),
        ("HttpMediaTypeNotSupportedException", "an unsupported Content-Type (415)"),
    ]
    if boot is not None and boot >= (3, 2):
        framework_4xx.append(("NoResourceFoundException", "an unknown path (404)"))
    if re.search(r"spring-boot-starter-security|spring-security", build_text) and \
            re.search(r"@(PreAuthorize|PostAuthorize|Secured|RolesAllowed)\b", all_src):
        framework_4xx.append(("AccessDeniedException", "a @PreAuthorize/@Secured denial (403)"))
    advice_text = "\n".join(x.text for x in sources if re.search(r"@(Rest)?ControllerAdvice\b", x.text))
    if not webflux:
        for x in sources:
            if not re.search(r"@(Rest)?ControllerAdvice\b", x.text) or \
                    re.search(r"(extends|:)\s*ResponseEntityExceptionHandler\b", x.text):
                continue
            catch_all = re.search(r"@ExceptionHandler\s*\(([^)]*\b(?:java\.lang\.)?(?:Exception|Throwable|RuntimeException)"
                                  r"(?:\.class|::class)[^)]*)\)", x.text) or \
                re.search(r"@ExceptionHandler\s+(?:@\w+(?:\([^)]*\))?\s+)*(?:public\s+|protected\s+|fun\s+)?[\w<>?, ]*?\w+\s*"
                          r"\(\s*(?:final\s+)?(?:\w+\s*:\s*)?(?:Exception|Throwable|RuntimeException)\b", x.text)
            if not catch_all:
                continue
            missing = [(e, what) for e, what in framework_4xx if e not in advice_text]
            if not missing:
                continue
            body = x.text[catch_all.end():catch_all.end() + 1500]
            to_500 = re.search(r"INTERNAL_SERVER_ERROR|\b500\b", body.split("@ExceptionHandler")[0])
            rep.add("QC31", "error", x.rel, x.line(catch_all.start()),
                    "This advice catches every exception but doesn't extend ResponseEntityExceptionHandler or handle "
                    "Spring's own 4xx exceptions, so these "
                    + ("come back as 500" if to_500 else "end up in the catch-all instead of their real status")
                    + ": " + "; ".join(w for _, w in missing)
                    + ". Clients see server errors for their own mistakes, and monitoring counts them as outages.",
                    "Extend ResponseEntityExceptionHandler (it maps Spring's exceptions to their 4xx statuses) or add "
                    "handlers for those exceptions; let AccessDeniedException through to Spring Security.",
                    confidence="certain" if to_500 else "verify")

    # QC32 — Spring Security 5 antMatchers and Spring MVC's trailing-slash match
    if boot is not None and boot < (3, 0) and not webflux and "setUseTrailingSlashMatch(false)" not in all_src:
        for x in sources:
            if ".antMatchers" not in x.text:
                continue
            permits = []
            for m in re.finditer(r"\.antMatchers\s*\(([^)]*)\)\s*\.\s*permitAll\s*\(", x.text):
                permits += [(pre, m.group(1)) for pre in re.findall(r'"([^"]+)/\*\*"', m.group(1))]
            open_all = re.search(r"anyRequest\s*\(\s*\)\s*\.\s*permitAll", x.text)
            restrictive = r"(authenticated|fullyAuthenticated|hasRole|hasAnyRole|hasAuthority|hasAnyAuthority|denyAll|access)"
            for m in re.finditer(r"\.antMatchers\s*\(([^)]*)\)\s*\.\s*" + restrictive + r"\b", x.text):
                method = re.search(r"HttpMethod\.(\w+)", m.group(1))
                for path in re.findall(r'"([^"]+)"', m.group(1)):
                    if path.endswith("**") or path.endswith("/"):
                        continue
                    wider = [pre for pre, args in permits if path.startswith(pre + "/")
                             and (not method or not re.search(r"HttpMethod\.", args) or method.group(0) in args)]
                    if not wider and not open_all:
                        continue
                    via = f'"{wider[0]}/**" ... permitAll()' if wider else "anyRequest().permitAll()"
                    rep.add("QC32", "error", x.rel, x.line(m.start()),
                            f'antMatchers("{path}").{m.group(2)}() matches only "{path}", but Spring MVC (Boot 2.x) '
                            f'also serves "{path}/". That request skips this rule and falls to {via}, so it runs '
                            f"without the required authentication (an anonymous user reaches the handler, which "
                            f"usually fails with a 500 on the missing user, or exposes data).",
                            f'Use mvcMatchers("{path}") (it matches what Spring MVC matches), or add "{path}/" to '
                            f"the rule, or turn off trailing-slash matching.", confidence="verify")

    # QC33 — Location built from a bare path while a context path is set
    context_path = next((v for key in ("server.servlet.context-path", "spring.mvc.servlet.path")
                         for v, _ in bases.get(key, []) if v.strip("/'\" ")), None)
    if context_path and not webflux:
        loc = re.compile(r"(?:\.created|setLocation|\.location|header\s*\(\s*(?:HttpHeaders\.LOCATION|\"Location\")\s*,)"
                         r"\s*\(?\s*(?:URI\.create\s*\(\s*\"/|new\s+URI\s*\(\s*\"/|URI\s*\(\s*\"/|UriComponentsBuilder\s*\."
                         r"\s*(?:newInstance\s*\(\s*\)\s*\.\s*path|fromPath)\s*\(\s*\"/)")
        for x in controllers:
            hits = [m for m in loc.finditer(x.text)]
            if hits:
                rep.add("QC33", "warning", x.rel, x.line(hits[0].start()),
                        f"{len(hits)} Location header{'s' if len(hits) > 1 else ''} built from a path starting at '/', "
                        f"but the app runs under the context path {context_path.strip()}: clients following "
                        f"{'them' if len(hits) > 1 else 'it'} get a 404.",
                        "Build it from the request: ServletUriComponentsBuilder.fromCurrentContextPath() or "
                        "fromCurrentRequest().path(\"/{id}\"), or inject a UriComponentsBuilder parameter.")

    # QC34 — 204 No Content with a body
    for x in controllers:
        hits = []
        for m in re.finditer(r"new\s+ResponseEntity\s*(?:<[^>]*>)?\s*", x.text):
            args, _ = balanced_args(x.text, m.end())
            parts = split_top(args[1:-1]) if args.startswith("(") else split_top(args)
            if len(parts) >= 2 and re.search(r"NO_CONTENT", parts[-1]) and not re.search(
                    r"(?i)headers|HttpStatus|null", parts[0]):
                hits.append(m)
        hits += list(re.finditer(r"status\s*\(\s*HttpStatus\.NO_CONTENT\s*\)\s*\.\s*body\s*\(", x.text))
        if hits:
            hits.sort(key=lambda m: m.start())
            rep.add("QC34", "warning", x.rel, x.line(hits[0].start()),
                    f"{len(hits)} response{'s' if len(hits) > 1 else ''} with status 204 No Content and a body: "
                    f"a 204 can't carry one, so the server drops it and clients expecting the updated resource "
                    f"get nothing.",
                    "Return 200 with the body, or 204 without one — whichever the API documents.")
    for h in handlers:
        rt = raw_type(h.return_type or "")
        if re.search(r"HttpStatus\.NO_CONTENT|NO_CONTENT\b", h.annos or "") and "ResponseStatus" in (h.annos or "") \
                and rt not in ("void", "Void", "Unit", "", "ResponseEntity", "Mono", "Flux") \
                and not re.search(r"Mono<\s*Void|Mono<\s*Unit", h.return_type or ""):
            rep.add("QC34", "warning", h.src.rel, h.line,
                    f"@ResponseStatus(NO_CONTENT) on a handler that returns {h.return_type}: the body is dropped.",
                    "Return void, or use 200 if clients need the body.", endpoint=h.label())

    # QC35 — an empty collection answered with 404
    for x in controllers:
        hits = []
        for m in re.finditer(r"if\s*\(\s*(\w+)\.isEmpty\(\)\s*\)\s*\{?\s*(?:return\s+(?:new\s+ResponseEntity\s*(?:<[^>]*>)?\s*\(\s*"
                             r"HttpStatus\.NOT_FOUND|ResponseEntity\s*\.\s*(?:notFound\s*\(|status\s*\(\s*HttpStatus\.NOT_FOUND))"
                             r"|throw\s+(?:new\s+)?\w*NotFound\w*)", x.text):
            var = re.escape(m.group(1))
            before = x.text[max(0, m.start() - 1500):m.start()]
            if re.search(r"\b(?:List|Collection|Set|Iterable|Page|ArrayList|LinkedList|HashSet)\s*<[^;=(){}]*>\s+" + var + r"\s*=",
                         before) or re.search(r"\b(?:val|var)\s+" + var + r"\s*:\s*(?:Mutable)?(?:List|Collection|Set)<", before):
                hits.append(m)
        if hits:
            rep.add("QC35", "warning", x.rel, x.line(hits[0].start()),
                    f"{len(hits)} handler{'s' if len(hits) > 1 else ''} answer{'s' if len(hits) == 1 else ''} an empty "
                    f"collection with 404. An empty list or a search with no matches is a successful answer: clients "
                    f"get an error they must special-case, and a 404 suggests the URL itself is wrong.",
                    "Return 200 with [] (404 is for a single resource that doesn't exist).")

    # QC16 — not-found handling
    for s in sources:
        if not re.search(r"@(Service|Component|RestController|Controller)\b", s.text):
            continue
        for m in re.finditer(r"\.orElseThrow\(\s*\)|findById\([^()]*\)\s*\.get\(\)|OrNull\([^()]*\)\s*!!", s.text):
            var = re.search(r"(\w+)\s*$", s.text[max(0, m.start() - 80):m.start()])
            if var and m.group(0).startswith(".orElseThrow") and re.search(
                    r"\b" + re.escape(var.group(1)) + r"\s*\.\s*isPresent\s*\(", s.text[max(0, m.start() - 400):m.start()]):
                continue  # guarded: the Optional was checked first
            exc = "NullPointerException" if m.group(0).endswith("!!") else "NoSuchElementException"
            rep.add("QC16", "warning", s.rel, s.line(m.start()),
                    f"A missing value throws {exc}, which no handler maps, so the client gets a "
                    "500 (or whatever /error turns it into). If this can happen for a client-supplied id, it "
                    "should be a 404.",
                    ("Use ?: throw ResponseStatusException(HttpStatus.NOT_FOUND) (or the project's own not-found "
                     "exception) instead of !!." if exc == "NullPointerException" else
                     "Throw a mapped not-found exception, e.g. .orElseThrow(() -> new ResponseStatusException("
                     "HttpStatus.NOT_FOUND)) or the project's own not-found exception."), confidence="verify")

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


def git(root, *args):
    import subprocess
    out = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr.strip() or f"git {' '.join(args)} failed")
    return out.stdout


def changed_files(root, base):
    """Files (root-relative) changed since `base` diverged — committed on this branch or not yet committed."""
    # realpath on both sides: git reports resolved paths (/private/var/… on macOS, symlinked workspaces in CI)
    root = os.path.realpath(root)
    top = os.path.realpath(git(root, "rev-parse", "--show-toplevel").strip())
    merge_base = git(root, "merge-base", base, "HEAD").strip()
    names = git(root, "diff", "--name-only", "--diff-filter=ACMR", merge_base).split()
    names += git(top, "ls-files", "--others", "--exclude-standard", "--full-name").split()  # new, untracked
    return {os.path.relpath(os.path.join(top, n), root) for n in names}


def repo_relative(root, rel):
    """Path as GitHub sees it (relative to the repository root) for annotations."""
    try:
        top = os.path.realpath(git(root, "rev-parse", "--show-toplevel").strip())
        return os.path.relpath(os.path.join(os.path.realpath(root), rel), top)
    except (RuntimeError, OSError):
        return rel


def gh_escape(s, prop=False):
    s = s.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return s.replace(":", "%3A").replace(",", "%2C") if prop else s


def print_text(root, stack, findings, scope):
    boot = stack["spring_boot"] or "unknown"
    print(f"Spring API quick check — {root}")
    print(f"Spring Boot {boot} · validation: {stack['validation_namespace'] or 'none'} · "
          f"{stack['handlers']} handlers · {stack['types']} types{scope}\n")
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


def print_github(root, findings):
    """GitHub Actions workflow commands: shown inline on the PR's changed files."""
    level = {"error": "error", "warning": "warning", "suggestion": "notice"}
    for f in findings:
        title = f"{f['rule']} {f['name']}" + (" (verify)" if f["confidence"] == "verify" else "")
        body = f"{f['message']}\nFix: {f['fix']}"
        if f["endpoint"]:
            body = f"{f['endpoint']}\n{body}"
        print(f"::{level[f['severity']]} file={gh_escape(repo_relative(root, f['file']), True)},line={f['line']},"
              f"title={gh_escape(title, True)}::{gh_escape(body)}")


def print_markdown(root, stack, findings, scope):
    counts = {s: sum(f["severity"] == s for f in findings) for s in SEVERITIES}
    print("## Spring API quick check\n")
    print(f"Spring Boot {stack['spring_boot'] or 'unknown'} · {stack['handlers']} handlers{scope} · "
          f"**{counts['error']} errors, {counts['warning']} warnings, {counts['suggestion']} suggestions**\n")
    if not findings:
        print("No findings.")
        return
    icon = {"error": "🔴", "warning": "🟡", "suggestion": "🔵"}
    print("| | Rule | Where | Finding |\n|---|---|---|---|")
    for f in findings:
        msg = f["message"].replace("|", "\\|").replace("\n", " ")
        where = f"`{repo_relative(root, f['file'])}:{f['line']}`"
        verify = " *(verify)*" if f["confidence"] == "verify" else ""
        print(f"| {icon[f['severity']]} | {f['rule']} {f['name']}{verify} | {where} | {msg} |")
    print("\nPattern matches from `quick_check.py`: confirm each in the code. `(verify)` marks heuristics.")


SARIF_LEVEL = {"error": "error", "warning": "warning", "suggestion": "note"}
HELP_URI = "https://github.com/filipelinemburger/spring-boot-api-validator#quick-check-no-ai-ci-friendly"


def sarif_report(root, findings):
    """SARIF 2.1.0 for GitHub code scanning (upload with github/codeql-action/upload-sarif).

    Paths are relative to the repository root. Each result carries a fingerprint built from the rule,
    file, endpoint and message — not the line — so an alert survives code moving around it; identical
    findings in one file are told apart by their order.
    """
    import hashlib
    try:
        top = os.path.realpath(git(root, "rev-parse", "--show-toplevel").strip())
    except (RuntimeError, OSError):
        top = os.path.realpath(root)
    ids = sorted(RULES)
    rules = [{
        "id": rid,
        "name": RULES[rid][0],
        "shortDescription": {"text": RULES[rid][1]},
        "fullDescription": {"text": RULES[rid][1]},
        "helpUri": HELP_URI,
        "help": {"text": f"{RULES[rid][1]}. Each finding's message says what goes wrong at runtime and how to fix "
                         f"it. Pattern matches: confirm each in the code.",
                 "markdown": f"**{rid} {RULES[rid][0]}**: {RULES[rid][1]}.\n\nEach finding's message says what goes "
                             f"wrong at runtime and how to fix it. Pattern matches: confirm each in the code. "
                             f"[All rules]({HELP_URI})"},
        "properties": {"tags": ["spring", "rest-api", "maintainability"], "precision": "high"},
    } for rid in ids]
    index = {rid: i for i, rid in enumerate(ids)}
    seen = {}
    results = []
    for f in sorted(findings, key=lambda f: (f["file"], f["line"] or 0, f["rule"])):
        path = os.path.relpath(os.path.join(os.path.realpath(root), f["file"]), top).replace(os.sep, "/")
        key = "\x1f".join((f["rule"], path, f["endpoint"] or "", f["message"]))
        seen[key] = seen.get(key, 0) + 1
        digest = hashlib.sha256(f"{key}\x1f{seen[key]}".encode("utf-8")).hexdigest()
        text = f"{f['message']}\nFix: {f['fix']}"
        if f["endpoint"]:
            text = f"{f['endpoint']}: {text}"
        if f["confidence"] == "verify":
            text += "\n(Heuristic: verify in the code.)"
        results.append({
            "ruleId": f["rule"],
            "ruleIndex": index[f["rule"]],
            "level": SARIF_LEVEL[f["severity"]],
            "message": {"text": text},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": path, "uriBaseId": "%SRCROOT%"},
                "region": {"startLine": max(1, int(f["line"] or 1))},
            }}],
            "partialFingerprints": {"springApiQuickCheck/v1": digest},
            "properties": {"severity": f["severity"], "confidence": f["confidence"]},
        })
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {"driver": {
                "name": "Spring API quick check",
                "semanticVersion": VERSION,
                "informationUri": "https://github.com/filipelinemburger/spring-boot-api-validator",
                "rules": rules,
            }},
            "results": results,
            "columnKind": "unicodeCodePoints",
        }],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--format", choices=["text", "json", "github", "markdown", "sarif"], default="text",
                    help="text (default), json, github (Actions annotations), markdown (job summary) "
                         "or sarif (GitHub code scanning)")
    ap.add_argument("--json", action="store_true", help="same as --format json")
    ap.add_argument("--diff-base", metavar="REF",
                    help="only report findings in files changed since the branch diverged from REF (e.g. origin/main)")
    ap.add_argument("--fail-on", choices=["error", "warning", "suggestion", "never"], default="never",
                    help="exit 1 when a reported finding is at or above this severity (for CI)")
    ap.add_argument("--rules", help="comma-separated rule ids to run, e.g. QC03,QC08")
    ap.add_argument("--skip", help="comma-separated rule ids to leave out, e.g. QC16")
    ap.add_argument("--list-rules", action="store_true", help="print the rules and exit")
    args = ap.parse_args()
    if args.list_rules:
        for k, (name, summary) in RULES.items():
            print(f"{k}  {name:32} {summary}")
        return
    root = os.path.realpath(args.root)
    fmt = "json" if args.json else args.format
    ids = lambda s: {r.strip().upper() for r in s.split(",") if r.strip()} if s else None  # noqa: E731
    stack, findings = run_checks(root, ids(args.rules), ids(args.skip))

    scope = ""
    if args.diff_base:
        try:
            changed = changed_files(root, args.diff_base)
        except RuntimeError as e:
            print(f"--diff-base {args.diff_base}: {e}", file=sys.stderr)
            sys.exit(2)  # distinct from 1 ("findings at or above --fail-on") so CI can fall back
        findings = [f for f in findings if f["file"] in changed]
        scope = f" · files changed since {args.diff_base}: {len(changed)}"

    if fmt == "json":
        print(json.dumps({"root": root, "stack": stack, "diff_base": args.diff_base, "findings": findings,
                          "rules": {k: {"name": v[0], "summary": v[1]} for k, v in RULES.items()}}, indent=2))
    elif fmt == "github":
        print_github(root, findings)
    elif fmt == "markdown":
        print_markdown(root, stack, findings, scope)
    elif fmt == "sarif":
        print(json.dumps(sarif_report(root, findings), indent=2))
    else:
        print_text(root, stack, findings, scope)

    if args.fail_on != "never":
        limit = SEVERITIES.index(args.fail_on)
        if any(SEVERITIES.index(f["severity"]) <= limit for f in findings):
            sys.exit(1)


if __name__ == "__main__":
    main()
