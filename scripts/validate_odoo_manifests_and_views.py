#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validate Odoo addon manifests and XML view files under `custom_addons/`.

Checks performed:
- Parse each `__manifest__.py` safely via ast.literal_eval.
- Verify referenced files in keys like `data`, `demo`, `qweb` exist.
- Optionally scan `assets` (if present) for file existence.
- Parse XML files under `views/` to ensure they are well-formed.
- Basic CSV header check for `security/ir.model.access.csv` if present.

Prints a concise summary with any problems found.
"""
from __future__ import annotations

import sys
import ast
import csv
import json
from pathlib import Path
from typing import Dict, List, Any

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO_ROOT = Path(__file__).resolve().parents[1]
ADDONS_ROOT = REPO_ROOT / "custom_addons"


def safe_load_manifest(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        node = ast.parse(text, filename=str(path))
        # Expect the file to contain a single dict literal
        for stmt in node.body:
            if isinstance(stmt, ast.Assign):
                value = stmt.value
            elif isinstance(stmt, ast.Expr):
                value = stmt.value
            else:
                continue
            try:
                return ast.literal_eval(value)
            except Exception:
                continue
        # Fallback: try literal_eval on entire content
        return ast.literal_eval(text)
    except Exception as e:
        raise ValueError(f"Failed to parse manifest {path}: {e}")


def _resolve_module_relative(module_dir: Path, rel: Path) -> Path:
    """Resolve a manifest path that may be absolute from module root or prefixed with module name.

    Odoo allows entries like "static/..." or "<module>/static/...". This helper
    tries both to find the actual file on disk.
    """
    candidate = module_dir / rel
    if candidate.exists():
        return candidate
    # If path begins with the module name, strip it and try again
    parts = list(rel.parts)
    if parts and parts[0] == module_dir.name:
        stripped = Path(*parts[1:])
        candidate2 = module_dir / stripped
        if candidate2.exists():
            return candidate2
    return candidate


def check_manifest_files(module_dir: Path, manifest: Dict[str, Any]) -> List[str]:
    problems: List[str] = []
    keys = ["data", "demo", "qweb"]
    for key in keys:
        files = manifest.get(key) or []
        if isinstance(files, (list, tuple)):
            for rel in files:
                rel_path = Path(rel)
                full = _resolve_module_relative(module_dir, rel_path)
                if not full.exists():
                    problems.append(f"Missing file referenced in manifest {key}: {rel}")

    # Handle assets structure (dict of bundles -> list of files)
    assets = manifest.get("assets")
    if isinstance(assets, dict):
        for bundle, items in assets.items():
            if not isinstance(items, (list, tuple)):
                continue
            for rel in items:
                # skip wildcards; only check direct files
                if any(ch in rel for ch in ["*", "?"]):
                    continue
                full = _resolve_module_relative(module_dir, Path(rel))
                if not full.exists():
                    problems.append(f"Missing asset file in bundle {bundle}: {rel}")
    return problems


def check_views_xml(module_dir: Path) -> List[str]:
    problems: List[str] = []
    import xml.etree.ElementTree as ET
    views_dir = module_dir / "views"
    if not views_dir.exists():
        return problems
    for xml_path in sorted(views_dir.rglob("*.xml")):
        try:
            ET.parse(str(xml_path))
        except ET.ParseError as e:
            problems.append(f"Malformed XML: {xml_path.relative_to(module_dir)} -> {e}")
        except Exception as e:
            problems.append(f"Error reading XML: {xml_path.relative_to(module_dir)} -> {e}")
    return problems


def check_access_csv(module_dir: Path) -> List[str]:
    problems: List[str] = []
    csv_path = module_dir / "security" / "ir.model.access.csv"
    if not csv_path.exists():
        return problems
    try:
        with csv_path.open("r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, [])
        # Minimal expected columns in Odoo access CSV
        expected = {"id", "name", "model_id:id", "group_id:id", "perm_read", "perm_write", "perm_create", "perm_unlink"}
        if not expected.issubset({h.strip() for h in header}):
            problems.append(
                f"Unexpected access CSV header in {csv_path.relative_to(module_dir)}: {header}"
            )
    except Exception as e:
        problems.append(f"Error reading access CSV: {csv_path.relative_to(module_dir)} -> {e}")
    return problems


def main() -> int:
    if not ADDONS_ROOT.exists():
        print("custom_addons directory not found")
        return 2

    summary = {"modules": 0, "manifest_problems": 0, "xml_problems": 0, "csv_problems": 0}
    details: Dict[str, Dict[str, List[str]]] = {}

    for module_dir in sorted([p for p in ADDONS_ROOT.iterdir() if p.is_dir()]):
        manifest_file = module_dir / "__manifest__.py"
        if not manifest_file.exists():
            continue
        summary["modules"] += 1
        module_name = module_dir.name
        details[module_name] = {"manifest": [], "xml": [], "csv": []}
        try:
            manifest = safe_load_manifest(manifest_file)
        except Exception as e:
            details[module_name]["manifest"].append(str(e))
            summary["manifest_problems"] += 1
            continue

        # Manifest referenced files
        m_problems = check_manifest_files(module_dir, manifest)
        details[module_name]["manifest"].extend(m_problems)
        summary["manifest_problems"] += len(m_problems)

        # XML parsing
        x_problems = check_views_xml(module_dir)
        details[module_name]["xml"].extend(x_problems)
        summary["xml_problems"] += len(x_problems)

        # Access CSV
        c_problems = check_access_csv(module_dir)
        details[module_name]["csv"].extend(c_problems)
        summary["csv_problems"] += len(c_problems)

    # Print concise report
    print("Odoo Manifests/XML Validation Summary")
    print("=" * 40)
    print(f"Modules scanned: {summary['modules']}")
    print(f"Manifest issues: {summary['manifest_problems']}")
    print(f"XML issues: {summary['xml_problems']}")
    print(f"Access CSV issues: {summary['csv_problems']}")

    if any(v > 0 for k, v in summary.items() if k != "modules"):
        print("\nDetails:")
        for module, probs in details.items():
            lines: List[str] = []
            for cat in ("manifest", "xml", "csv"):
                for msg in probs[cat]:
                    lines.append(f"- [{cat}] {msg}")
            if lines:
                print(f"\n[{module}]")
                for ln in lines:
                    print(ln)

    # Exit code 0 even with issues (non-destructive validation)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
