#!/usr/bin/env python3
"""Find and read OpenAPI 3.x / Swagger 2.0 specs (YAML or JSON) with the standard library only.

Used by quick_check.py for the spec-drift rules. The YAML reader covers the subset OpenAPI files use:
block mappings and sequences, quoted and plain scalars, flow sequences/mappings ([a, b], {a: b}),
block scalars (| and >), and comments. Anchors, aliases and multi-document files are not supported;
a file it can't read is reported and skipped.

    python3 openapi_spec.py <project-root>    # prints the operations found in each spec
"""
import json
import os
import re
import sys

SPEC_NAME = re.compile(r"(openapi|swagger|api[-_]?spec|api[-_]?docs?)[\w.-]*\.(ya?ml|json)$", re.I)
SKIP_DIRS = {".git", "build", "target", "node_modules", ".gradle", ".idea", "out", "bin", "dist", ".venv"}
METHODS = ("get", "put", "post", "delete", "patch", "head", "options")


# ---------------------------------------------------------------------------------------------
# Minimal YAML reader

class YamlError(ValueError):
    pass


def _strip_comment(line):
    out, quote = [], None
    for k, c in enumerate(line):
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == "#" and (k == 0 or line[k - 1] in " \t"):
            break
        out.append(c)
    return "".join(out).rstrip()


def _split_flow(text):
    parts, depth, cur, quote = [], 0, [], None
    for c in text:
        if quote:
            cur.append(c)
            if c == quote:
                quote = None
            continue
        if c in "'\"":
            quote = c
        elif c in "[{":
            depth += 1
        elif c in "]}":
            depth -= 1
        elif c == "," and depth == 0:
            parts.append("".join(cur).strip())
            cur = []
            continue
        cur.append(c)
    if "".join(cur).strip():
        parts.append("".join(cur).strip())
    return parts


def _scalar(text):
    t = text.strip()
    if t == "" or t in ("~", "null", "Null", "NULL"):
        return None
    if t[0] == "[" and t.endswith("]"):
        return [_scalar(p) for p in _split_flow(t[1:-1])]
    if t[0] == "{" and t.endswith("}"):
        out = {}
        for p in _split_flow(t[1:-1]):
            k, _, v = p.partition(":")
            out[_scalar(k)] = _scalar(v)
        return out
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "'\"":
        s = t[1:-1]
        return s.replace("''", "'") if t[0] == "'" else s.encode().decode("unicode_escape") if "\\" in s else s
    if t in ("true", "True", "TRUE"):
        return True
    if t in ("false", "False", "FALSE"):
        return False
    if re.fullmatch(r"-?\d+", t):
        return int(t)
    if re.fullmatch(r"-?\d+\.\d*(e[-+]?\d+)?", t, re.I):
        return float(t)
    return t


def _key_value(text):
    """Split 'key: value' at the first ': ' (or trailing ':') outside quotes; None if not a mapping entry."""
    quote = None
    for k, c in enumerate(text):
        if quote:
            if c == quote:
                quote = None
        elif c in "'\"":
            quote = c
        elif c == ":" and (k + 1 == len(text) or text[k + 1] in " \t"):
            return _scalar(text[:k]), text[k + 1:].strip()
    return None


def yaml_load(text):
    lines = []
    for raw in text.replace("\t", "  ").split("\n"):
        if raw.strip() in ("---", "...") and not lines:
            continue
        lines.append(raw)
    pos = [0]

    def indent(line):
        return len(line) - len(line.lstrip(" "))

    def next_content(k):
        while k < len(lines) and not _strip_comment(lines[k]).strip():
            k += 1
        return k

    def block_scalar(style, base):
        out = []
        k = pos[0]
        while k < len(lines) and (not lines[k].strip() or indent(lines[k]) > base):
            out.append(lines[k])
            k += 1
        pos[0] = k
        body = [ln for ln in out]
        if not any(ln.strip() for ln in body):
            return ""
        cut = min(indent(ln) for ln in body if ln.strip())
        body = [ln[cut:] for ln in body]
        return "\n".join(body).strip("\n") if style.startswith("|") else " ".join(ln.strip() for ln in body if ln.strip())

    def parse_value(rest, base):
        if rest.startswith(("|", ">")):
            return block_scalar(rest, base)
        if rest == "":
            k = next_content(pos[0])
            if k < len(lines):
                ln = lines[k]
                if indent(ln) > base or (indent(ln) == base and ln.strip().startswith("- ")):
                    pos[0] = k
                    return parse_block(indent(ln))
            return None
        if rest[0] in "[{" and not (rest.endswith("]") or rest.endswith("}")):
            # flow collection spanning lines
            buf = rest
            while pos[0] < len(lines) and buf.count("[") + buf.count("{") > buf.count("]") + buf.count("}"):
                buf += " " + _strip_comment(lines[pos[0]]).strip()
                pos[0] += 1
            return _scalar(buf)
        return _scalar(rest)

    def parse_block(ind):
        k = next_content(pos[0])
        if k >= len(lines):
            return None
        pos[0] = k
        first = _strip_comment(lines[k]).strip()
        if first.startswith("- ") or first == "-":
            items = []
            while True:
                k = next_content(pos[0])
                if k >= len(lines) or indent(lines[k]) != ind:
                    break
                content = _strip_comment(lines[k]).strip()
                if not (content.startswith("- ") or content == "-"):
                    break
                pos[0] = k + 1
                item = content[1:].strip()
                if not item:
                    items.append(parse_value("", ind))
                elif _key_value(item) is not None and not item.startswith(("'", '"', "[", "{")):
                    # "- key: value" opens a mapping whose other keys sit at ind + 2
                    key, rest = _key_value(item)
                    mapping = {key: parse_value(rest, ind + 2)}
                    k2 = next_content(pos[0])
                    if k2 < len(lines) and indent(lines[k2]) == ind + 2:
                        more = parse_block(ind + 2)
                        if isinstance(more, dict):
                            mapping.update(more)
                    items.append(mapping)
                else:
                    items.append(_scalar(item))
            return items
        mapping = {}
        while True:
            k = next_content(pos[0])
            if k >= len(lines) or indent(lines[k]) != ind:
                break
            content = _strip_comment(lines[k]).strip()
            if content.startswith("- "):
                break
            kv = _key_value(content)
            if kv is None:
                raise YamlError(f"line {k + 1}: expected 'key: value', got {content[:40]!r}")
            pos[0] = k + 1
            mapping[kv[0]] = parse_value(kv[1], ind)
        return mapping

    k = next_content(0)
    if k >= len(lines):
        return None
    pos[0] = k
    return parse_block(indent(lines[k]))


# ---------------------------------------------------------------------------------------------
# Spec model

def load_document(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    if path.lower().endswith(".json"):
        return json.loads(text)
    return yaml_load(text)


def find_specs(root):
    """Spec files under root: by name (openapi*.yaml, swagger.json, …) or by an 'openapi:'/'swagger:' first key."""
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        parts = os.path.relpath(dirpath, root).replace(os.sep, "/").split("/")
        if "test" in parts:
            continue
        for fn in filenames:
            if not fn.lower().endswith((".yaml", ".yml", ".json")) or fn.startswith("application"):
                continue
            path = os.path.join(dirpath, fn)
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    head = fh.read(400)
            except OSError:
                continue
            if re.search(r'^\s*["\']?(openapi|swagger)["\']?\s*:', head, re.M) or (
                    SPEC_NAME.search(fn) and re.search(r"(openapi|swagger)", head)):
                found.append(path)
    return sorted(found)


def _ref_name(ref):
    return ref.rsplit("/", 1)[-1] if isinstance(ref, str) else None


class Spec:
    def __init__(self, path, root, doc):
        self.path = path
        self.rel = os.path.relpath(path, root)
        self.doc = doc if isinstance(doc, dict) else {}
        self.swagger2 = str(self.doc.get("swagger", "")).startswith("2")
        self.schemas = (self.doc.get("definitions") if self.swagger2 else
                        (self.doc.get("components") or {}).get("schemas")) or {}
        self.base_path = self._base_path()

    def _base_path(self):
        if self.swagger2:
            return (self.doc.get("basePath") or "").rstrip("/")
        servers = self.doc.get("servers") or []
        if servers and isinstance(servers[0], dict) and isinstance(servers[0].get("url"), str):
            url = re.sub(r"\{[^}]*\}", "", servers[0]["url"])
            path = re.sub(r"^[a-z]+://[^/]*", "", url, flags=re.I)
            return path.rstrip("/")
        return ""

    def resolve(self, schema, depth=0):
        """Follow $ref and merge allOf into one {required, properties} view (or return the schema as is)."""
        if not isinstance(schema, dict) or depth > 8:
            return schema if isinstance(schema, dict) else {}
        if "$ref" in schema:
            name = _ref_name(schema["$ref"])
            target = self.schemas.get(name, {})
            out = dict(self.resolve(target, depth + 1))
            out.setdefault("x-name", name)
            return out
        if "allOf" in schema:
            merged = {"required": [], "properties": {}}
            for part in schema["allOf"]:
                r = self.resolve(part, depth + 1)
                merged["required"] += list(r.get("required") or [])
                merged["properties"].update(r.get("properties") or {})
                if r.get("x-name") and "x-name" not in merged:
                    merged["x-name"] = r["x-name"]
            return merged
        return schema

    def _json_schema(self, holder):
        """The JSON schema of a requestBody/response (OpenAPI 3 content map or Swagger 2 schema)."""
        if not isinstance(holder, dict):
            return None
        if self.swagger2:
            return holder.get("schema")
        content = holder.get("content") or {}
        for media, body in content.items():
            if "json" in str(media) or media == "*/*":
                return (body or {}).get("schema")
        return None

    def operations(self):
        """[(METHOD, path, op_dict, line_hint)] — line_hint is the path's line in the file when it can be found."""
        ops = []
        try:
            with open(self.path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except OSError:
            text = ""
        for path, item in (self.doc.get("paths") or {}).items():
            if not isinstance(item, dict):
                continue
            m = re.search(r'^\s*["\']?' + re.escape(str(path)) + r'["\']?\s*:', text, re.M)
            line = text.count("\n", 0, m.start()) + 1 if m else 1
            for method in METHODS:
                op = item.get(method)
                if isinstance(op, dict):
                    ops.append((method.upper(), str(path), op, line))
        return ops

    def request_schema(self, op):
        if self.swagger2:
            for p in op.get("parameters") or []:
                if isinstance(p, dict) and p.get("in") == "body":
                    return p.get("schema")
            return None
        return self._json_schema(op.get("requestBody"))

    def success_codes(self, op):
        codes = []
        for code in (op.get("responses") or {}):
            c = str(code)
            if re.fullmatch(r"2\d\d", c):
                codes.append(int(c))
            elif c.upper() == "2XX":
                codes.extend(range(200, 300))
        return codes

    def success_schema(self, op):
        for code, resp in (op.get("responses") or {}).items():
            if re.fullmatch(r"2\d\d", str(code)):
                s = self._json_schema(resp)
                if s:
                    return s
        return None


def load_specs(root):
    """[(Spec|None, rel_path, error)] for every spec file under root."""
    out = []
    for path in find_specs(root):
        rel = os.path.relpath(path, root)
        try:
            doc = load_document(path)
            if not isinstance(doc, dict) or not doc.get("paths"):
                out.append((None, rel, "no paths found"))
                continue
            out.append((Spec(path, root, doc), rel, None))
        except (ValueError, YamlError, OSError) as e:
            out.append((None, rel, str(e)))
    return out


def main():
    root = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    specs = load_specs(root)
    if not specs:
        print(f"No OpenAPI/Swagger spec found under {root}")
    for spec, rel, err in specs:
        if err:
            print(f"# {rel}: could not read ({err})")
            continue
        print(f"# {rel} ({'Swagger 2.0' if spec.swagger2 else 'OpenAPI 3'}, base path '{spec.base_path or '/'}', "
              f"{len(spec.schemas)} schemas)")
        for method, path, op, line in spec.operations():
            req = spec.resolve(spec.request_schema(op) or {}).get("x-name")
            res = spec.resolve(spec.success_schema(op) or {}).get("x-name")
            print(f"  {method:7} {path:45} 2xx={spec.success_codes(op)} body={req or '-'} returns={res or '-'}"
                  f"  ({rel}:{line})")


if __name__ == "__main__":
    main()
