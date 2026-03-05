#!/usr/bin/env python3
"""
ScummVM WASM Asset Downloader

Downloads all ScummVM WebAssembly assets from scummvm.kuendig.io:
  - scummvm.wasm (core engine ~37 MB)
  - scummvm.js (JS glue code ~9 MB)
  - All engine plugins (~100+ .so files)
  - All engine data files (.dat, .cpt, .tbl, .zip)

These assets are required by pack_scummvm_game.py to create offline HTML games.

Usage:
    python3 download_scummvm_assets.py
    python3 download_scummvm_assets.py --output-dir /path/to/docs/data/scummvm
    python3 download_scummvm_assets.py --plugins-only
    python3 download_scummvm_assets.py --status

Source: https://scummvm.kuendig.io (ScummVM WASM by kuendig.io)
"""

import os
import sys
import json
import argparse
import hashlib
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================================
# Configuration
# ============================================================================

BASE_URL = "https://scummvm.kuendig.io"
DATA_URL = f"{BASE_URL}/data"
PLUGINS_URL = f"{DATA_URL}/plugins"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, '..', '..'))
DEFAULT_OUTPUT = os.path.join(REPO_ROOT, 'docs', 'data', 'scummvm')

# Core files (always needed)
CORE_FILES = {
    'scummvm.wasm': f'{BASE_URL}/scummvm.wasm',
    'scummvm.js':   f'{BASE_URL}/scummvm.js',
}

# ============================================================================
# Helpers
# ============================================================================

def download_file(url, dest_path, label=None):
    """Download a file with progress indication."""
    if os.path.isfile(dest_path) and os.path.getsize(dest_path) > 0:
        return True, f"✓ {label or os.path.basename(dest_path)} (cached)"

    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    name = label or os.path.basename(dest_path)

    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'portable-retro-games ScummVM packer'
        })
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
        with open(dest_path, 'wb') as f:
            f.write(data)
        size_kb = len(data) / 1024
        if size_kb > 1024:
            size_str = f"{size_kb/1024:.1f} MB"
        else:
            size_str = f"{size_kb:.0f} KB"
        return True, f"✓ {name} ({size_str})"
    except Exception as e:
        return False, f"✗ {name}: {e}"


def fetch_json(url):
    """Fetch and parse a JSON URL."""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'portable-retro-games ScummVM packer'
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))


# ============================================================================
# Main download logic
# ============================================================================

def download_all(output_dir, plugins_only=False, max_workers=8):
    """Download all ScummVM WASM assets."""

    plugins_dir = os.path.join(output_dir, 'plugins')
    data_dir = os.path.join(output_dir, 'data')
    os.makedirs(plugins_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    errors = []

    # --- Step 1: Core files (wasm + js) ---
    if not plugins_only:
        print("\n━━━ Core Files ━━━")
        for filename, url in CORE_FILES.items():
            dest = os.path.join(output_dir, filename)
            ok, msg = download_file(url, dest)
            print(f"  {msg}")
            if not ok:
                errors.append(msg)

    # --- Step 2: Fetch plugin index ---
    print("\n━━━ Fetching indexes ━━━")
    try:
        plugin_index = fetch_json(f"{PLUGINS_URL}/index.json")
        print(f"  ✓ Plugin index: {len(plugin_index)} engines found")
    except Exception as e:
        print(f"  ✗ Failed to fetch plugin index: {e}")
        return False

    try:
        data_index = fetch_json(f"{DATA_URL}/index.json")
        print(f"  ✓ Data index loaded")
    except Exception as e:
        print(f"  ✗ Failed to fetch data index: {e}")
        return False

    # --- Step 3: Download engine plugins ---
    print(f"\n━━━ Engine Plugins ({len(plugin_index)} files) ━━━")
    plugin_tasks = []
    for plugin_name, size in sorted(plugin_index.items()):
        url = f"{PLUGINS_URL}/{plugin_name}"
        dest = os.path.join(plugins_dir, plugin_name)
        plugin_tasks.append((url, dest, plugin_name))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(download_file, url, dest, label): label
            for url, dest, label in plugin_tasks
        }
        done_count = 0
        for future in as_completed(futures):
            done_count += 1
            ok, msg = future.result()
            print(f"  [{done_count}/{len(plugin_tasks)}] {msg}")
            if not ok:
                errors.append(msg)

    # --- Step 4: Download data files ---
    if not plugins_only:
        # Filter data files from the index (exclude nested objects like 'plugins', 'games', etc.)
        data_files = {}
        for key, value in data_index.items():
            if isinstance(value, int):  # actual files have integer sizes
                data_files[key] = value

        print(f"\n━━━ Engine Data Files ({len(data_files)} files) ━━━")
        data_tasks = []
        for filename, size in sorted(data_files.items()):
            url = f"{DATA_URL}/{filename}"
            dest = os.path.join(data_dir, filename)
            data_tasks.append((url, dest, filename))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(download_file, url, dest, label): label
                for url, dest, label in data_tasks
            }
            done_count = 0
            for future in as_completed(futures):
                done_count += 1
                ok, msg = future.result()
                print(f"  [{done_count}/{len(data_tasks)}] {msg}")
                if not ok:
                    errors.append(msg)

    # --- Summary ---
    print(f"\n{'='*60}")
    if errors:
        print(f"⚠ Completed with {len(errors)} error(s):")
        for e in errors:
            print(f"  {e}")
    else:
        print("✅ All ScummVM WASM assets downloaded successfully!")

    # Calculate total size
    total = 0
    for root, dirs, files in os.walk(output_dir):
        for f in files:
            total += os.path.getsize(os.path.join(root, f))

    print(f"\n  Output:     {output_dir}")
    print(f"  Total size: {total/1024/1024:.1f} MB")

    # Count by category
    n_plugins = len([f for f in os.listdir(plugins_dir) if f.endswith('.so')]) if os.path.exists(plugins_dir) else 0
    n_data = len(os.listdir(data_dir)) if os.path.exists(data_dir) else 0
    print(f"  Plugins:    {n_plugins}")
    print(f"  Data files: {n_data}")
    print(f"  Core:       scummvm.wasm + scummvm.js")

    return len(errors) == 0


def show_status(output_dir):
    """Show what's currently downloaded."""
    print(f"\nScummVM assets status: {output_dir}\n")

    # Core files
    for name in ['scummvm.wasm', 'scummvm.js']:
        path = os.path.join(output_dir, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            print(f"  ✓ {name}: {size/1024/1024:.1f} MB")
        else:
            print(f"  ✗ {name}: MISSING")

    # Plugins
    plugins_dir = os.path.join(output_dir, 'plugins')
    if os.path.isdir(plugins_dir):
        plugins = [f for f in os.listdir(plugins_dir) if f.endswith('.so')]
        total = sum(os.path.getsize(os.path.join(plugins_dir, f)) for f in plugins)
        print(f"  ✓ plugins/: {len(plugins)} engines ({total/1024/1024:.1f} MB)")
    else:
        print(f"  ✗ plugins/: MISSING")

    # Data files
    data_dir = os.path.join(output_dir, 'data')
    if os.path.isdir(data_dir):
        files = os.listdir(data_dir)
        total = sum(os.path.getsize(os.path.join(data_dir, f)) for f in files)
        print(f"  ✓ data/: {len(files)} files ({total/1024/1024:.1f} MB)")
    else:
        print(f"  ✗ data/: MISSING")


# ============================================================================
# Entry point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Download ScummVM WASM assets for the game packer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--output-dir', '-o', default=DEFAULT_OUTPUT,
        help=f'Output directory (default: {DEFAULT_OUTPUT})'
    )
    parser.add_argument(
        '--plugins-only', action='store_true',
        help='Only download engine plugins (skip core + data)'
    )
    parser.add_argument(
        '--status', action='store_true',
        help='Show current download status and exit'
    )
    parser.add_argument(
        '--workers', type=int, default=8,
        help='Number of parallel download workers (default: 8)'
    )

    args = parser.parse_args()

    if args.status:
        show_status(args.output_dir)
        return

    print("ScummVM WASM Asset Downloader")
    print(f"Source: {BASE_URL}")
    print(f"Output: {args.output_dir}")

    success = download_all(
        output_dir=args.output_dir,
        plugins_only=args.plugins_only,
        max_workers=args.workers,
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
