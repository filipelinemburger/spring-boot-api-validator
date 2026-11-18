#!/usr/bin/env python3
"""List Spring MVC / WebFlux endpoints declared with mapping annotations.

Usage: python3 list_endpoints.py <project-root> [--json]

Regex-based endpoint inventory for the spring-api-validator checker: it finds
@RequestMapping / @GetMapping / @PostMapping / @PutMapping / @PatchMapping /
@DeleteMapping in .java and .kt files, combines class-level and method-level
paths, and prefixes the context path / base path found in application config.
It does not resolve constants or evaluate SpEL; such paths are shown as {CONST:NAME}.
Always confirm the results by reading the controllers.
"""
import json
import os
import re
import sys

MAPPING_RE = re.compile(r"@(Request|Get|Post|Put|Patch|Delete)Mapping\b")
VERB_FOR = {"Get": "GET", "Post": "POST", "Put": "PUT", "Patch": "PATCH", "Delete": "DELETE"}
TYPE_DECL_RE = re.compile(r"\b(class|interface|object)\s+([A-Za-z_]\w*)")
SKIP_DIRS = {".git", "build", "target", "node_modules", ".gradle", ".idea", "out", "bin"}


def strip_comments(src):
    """Blank out comments while keeping string literals and line numbers intact."""
    out, i, n = [], 0, len(src)
    while i < n:
        c = src[i]
        if c == '"':
            if src.startswith('"""', i):  # Java text block / Kotlin raw string
                j = src.find('"""', i + 3)
                j = n if j == -1 else j + 3
            else:
                j = i + 1
                while j < n and src[j] != '"' and src[j] != "\n":
                    j += 2 if src[j] == "\\" else 1
                j += 1
            out.append(src[i:j])
            i = j
        elif src.startswith("//", i):
            j = src.find("\n", i)
            j = n if j == -1 else j
            out.append(" " * (j - i))
            i = j
        elif src.startswith("/*", i):
            j = src.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(re.sub(r"[^\n]", " ", src[i:j]))
            i = j
        else:
            out.append(c)
            i += 1
    return "".join(out)


def balanced_args(src, start):
    """If src[start:] begins (after spaces) with '(', return (args, end_index)."""
    i = start
    while i < len(src) and src[i] in " \t\r\n":
        i += 1
    if i >= len(src) or src[i] != "(":
        return "", start
    depth, j, in_str = 0, i, False
    while j < len(src):
        ch = src[j]
        if in_str:
            if ch == "\\":
                j += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                return src[i + 1:j], j + 1
        j += 1
    return src[i + 1:], len(src)


def split_top_level(args):
    parts, depth, cur, in_str, i = [], 0, [], False, 0
    while i < len(args):
        ch = args[i]
        if in_str:
            cur.append(ch)
            if ch == "\\" and i + 1 < len(args):
                cur.append(args[i + 1])
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
            cur.append(ch)
        elif ch in "([{":
            depth += 1
            cur.append(ch)
        elif ch in ")]}":
            depth -= 1
            cur.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def path_values(expr):
    """Turn a path expression ("a", {"a","b"}, [..], CONST, "a" + CONST) into a list of strings."""
    expr = expr.strip()
    if expr.startswith(("{", "[")) or expr.startswith("arrayOf("):
        inner = expr[expr.index("(") + 1:-1] if expr.startswith("arrayOf(") else expr[1:-1]
        vals = []
        for p in split_top_level(inner):
            vals.extend(path_values(p))
        return vals
    pieces = []
    for token in re.split(r"\s*\+\s*", expr):
        token = token.strip()
        if not token:
            continue
        m = re.fullmatch(r'"((?:[^"\\]|\\.)*)"', token)
        pieces.append(m.group(1) if m else "{CONST:%s}" % token)
    return ["".join(pieces)] if pieces else [""]


def parse_mapping(kind, args):
    paths, methods = None, []
    for i, part in enumerate(split_top_level(args)):
        m = re.match(r"^(\w+)\s*=\s*(.*)$", part, re.S)
        if m:
            key, val = m.group(1), m.group(2)
            if key in ("value", "path"):
                paths = path_values(val)
            elif key == "method":
                methods = re.findall(r"(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS|TRACE)", val)
        elif i == 0:
            paths = path_values(part)
    if paths is None:
        paths = [""]
    if kind != "Request":
        methods = [VERB_FOR[kind]]
    return paths, methods


def skip_annotations(src, i):
    """Skip whitespace, modifiers-free annotations (with args) and return the next index."""
    while True:
        while i < len(src) and src[i] in " \t\r\n":
            i += 1
        m = re.match(r"@[\w.]+", src[i:])
        if not m:
            return i
        _, i = balanced_args(src, i + m.end())


def handler_name(src, pos):
    i = skip_annotations(src, pos)
    sig = src[i:i + 600]
    m = re.search(r"\bfun\s+(?:<[^>]*>\s*)?([A-Za-z_]\w*)\s*\(", sig.split("{")[0])
    if m:
        return m.group(1)
    m = re.search(r"([A-Za-z_]\w*)\s*\(", sig)
    return m.group(1) if m else "?"


def join_paths(*parts):
    path = "/".join(p.strip("/") for p in parts if p and p.strip("/"))
    return "/" + path if path else "/"


def read_base_paths(root):
    """Collect context-path style settings from application*.yml/properties (best effort)."""
    keys = {
        "server.servlet.context-path": "context-path",
        "spring.mvc.servlet.path": "servlet-path",
        "spring.webflux.base-path": "webflux-base-path",
    }
    found = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not re.match(r"application.*\.(ya?ml|properties)$", fn):
                continue
            full = os.path.join(dirpath, fn)
            try:
                text = open(full, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            rel = os.path.relpath(full, root)
            if fn.endswith(".properties"):
                for key in keys:
                    m = re.search(r"^\s*%s\s*[=:]\s*(\S+)" % re.escape(key), text, re.M)
                    if m:
                        found.setdefault(key, []).append((m.group(1), rel))
            else:
                for key in keys:
                    leaf = key.split(".")[-1]
                    m = re.search(r"^\s*%s\s*:\s*['\"]?([^'\"\s#]+)" % re.escape(leaf), text, re.M)
                    flat = re.search(r"^\s*%s\s*:\s*['\"]?([^'\"\s#]+)" % re.escape(key), text, re.M)
                    hit = flat or (m if "-" in leaf else None)
                    if hit:
                        found.setdefault(key, []).append((hit.group(1), rel))
    return found


def scan_file(path, root):
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    if not MAPPING_RE.search(raw):
        return []
    src = strip_comments(raw)
    is_controller = bool(re.search(r"@(Rest)?Controller\b", src))
    type_m = TYPE_DECL_RE.search(src)
    type_pos = type_m.start() if type_m else -1
    type_name = type_m.group(2) if type_m else os.path.basename(path).rsplit(".", 1)[0]

    class_paths, class_methods, endpoints = [""], [], []
    for m in MAPPING_RE.finditer(src):
        args, end = balanced_args(src, m.end())
        paths, methods = parse_mapping(m.group(1), args)
        line = src.count("\n", 0, m.start()) + 1
        if type_pos != -1 and m.start() < type_pos:
            class_paths, class_methods = paths, methods
            continue
        name = handler_name(src, end)
        verbs = methods or class_methods
        flags = []
        if not verbs:
            flags.append("ALL-METHODS (no method= on @RequestMapping)")
            verbs = ["ANY"]
        if not is_controller:
            flags.append("no @Controller on type (interface or inherited mapping?)")
        for cp in class_paths:
            for p in paths:
                full = join_paths(cp, p)
                if "{CONST:" in full:
                    flags_here = flags + ["path uses constants"]
                else:
                    flags_here = flags
                for v in verbs:
                    endpoints.append({
                        "method": v,
                        "path": full,
                        "handler": "%s#%s" % (type_name, name),
                        "location": "%s:%d" % (os.path.relpath(path, root), line),
                        "flags": flags_here,
                    })
    return endpoints


ROUTE_RE = re.compile(
    r"(?:\.|\b)(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\(\s*\"([^\"]*)\"\s*(?:,\s*([^,()]+?(?:::|\.)\s*\w+|\{))?")


def scan_functional(path, root):
    """Functional endpoints: RouterFunctions.route().GET("/x", handler::m) and route(GET("/x"), handler::m),
    WebFlux and WebMvc.fn alike. Nested prefixes (.path / .nest / nest(path(...))) are flagged, not resolved."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
    except OSError:
        return []
    if not re.search(r"\bRouterFunction|coRouter|\brouter\s*\{", raw):
        return []
    src = strip_comments(raw)
    nested = bool(re.search(r"\.path\s*\(\s*\"|\.nest\s*\(|\bnest\s*\(|\"[^\"]*\"\s*\.nest\s*\{", src))
    endpoints = []
    matches = list(ROUTE_RE.finditer(src))
    for k, m in enumerate(matches):
        verb, p = m.group(1), m.group(2)
        if not p.startswith("/") and p != "":
            continue  # e.g. a header or media type string, not a path
        handler = (m.group(3) or "").strip()
        nxt = matches[k + 1].start() if k + 1 < len(matches) else len(src)
        tail = src[m.end():min(nxt, m.end() + 200)]
        if not handler or handler == "{":
            # route(GET("/x").and(accept(JSON)), handler::m) — the handler follows the predicate
            hm = re.search(r",\s*([\w.]+::\w+)", tail)
            handler = hm.group(1) if hm else "(lambda)"
        handler = re.sub(r"\s+", "", handler).replace("this::", "")
        flags = ["functional route"] + (["nested prefix not resolved — check .path/.nest"] if nested else [])
        endpoints.append({
            "method": verb,
            "path": p or "/",
            "handler": handler,
            "location": "%s:%d" % (os.path.relpath(path, root), src.count("\n", 0, m.start()) + 1),
            "flags": flags,
        })
    return endpoints


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_json = "--json" in sys.argv
    root = os.path.abspath(args[0] if args else ".")
    endpoints = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if os.sep + "test" + os.sep in dirpath + os.sep and "src" in dirpath:
            continue
        for fn in filenames:
            if fn.endswith((".java", ".kt")):
                endpoints.extend(scan_file(os.path.join(dirpath, fn), root))
                endpoints.extend(scan_functional(os.path.join(dirpath, fn), root))
    endpoints.sort(key=lambda e: (e["path"], e["method"]))
    bases = read_base_paths(root)

    if as_json:
        print(json.dumps({"base_paths": bases, "endpoints": endpoints}, indent=2))
        return
    for key, vals in bases.items():
        for val, where in vals:
            print("# %s = %s  (%s) — prefix the paths below with it" % (key, val, where))
    if not endpoints:
        print("No mapping annotations found under %s" % root)
        return
    w_m = max(len(e["method"]) for e in endpoints)
    w_p = max(len(e["path"]) for e in endpoints)
    w_h = max(len(e["handler"]) for e in endpoints)
    for e in endpoints:
        flag = ("  [" + "; ".join(e["flags"]) + "]") if e["flags"] else ""
        print("%-*s  %-*s  %-*s  %s%s" % (w_m, e["method"], w_p, e["path"], w_h, e["handler"], e["location"], flag))
    print("\n%d endpoint mapping(s). Regex-based: confirm by reading the code." % len(endpoints))


if __name__ == "__main__":
    main()
