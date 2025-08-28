#!/usr/bin/env python3
import os
import sys
import importlib

def main():
    addons_dir = '/mnt/extra-addons'
    if not os.path.isdir(addons_dir):
        print(f"ERROR: Addons dir not found: {addons_dir}")
        return 1

    modules = []
    for name in sorted(os.listdir(addons_dir)):
        path = os.path.join(addons_dir, name)
        if not os.path.isdir(path):
            continue
        if not os.path.exists(os.path.join(path, '__manifest__.py')):
            continue
        modules.append(name)

    print(f"Modules with __manifest__: {len(modules)}")

    sys.path.insert(0, addons_dir)
    ok, fail = [], []
    for m in modules:
        try:
            importlib.import_module(m)
            ok.append(m)
        except Exception as e:
            fail.append((m, str(e)))

    print(f"Imported OK: {len(ok)}")
    for m in ok:
        print(f"  + {m}")

    if fail:
        print(f"Failed imports: {len(fail)}")
        for m, e in fail:
            print(f"  - {m} -> {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())

