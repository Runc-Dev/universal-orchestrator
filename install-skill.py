#!/usr/bin/env python3
"""Install this package into project skill directories for Codex and Claude Code."""
import argparse
from pathlib import Path
import shutil
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Existing project directory')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'universal-orchestrator'
    root = Path(args.project).resolve(strict=True)
    if not root.is_dir() or not (source / 'SKILL.md').is_file():
        parser.error('Project directory or bundled skill is missing')
    destinations = [root / host / 'skills' / source.name for host in ('.agents', '.claude')]
    # Preflight both destinations before copying either. Never overwrite a skill.
    for destination in destinations:
        if destination.exists() or destination.is_symlink():
            parser.error(f'Destination already exists: {destination}')
        if source == destination or source in destination.parents:
            parser.error('Cannot install a skill inside itself')
    for destination in destinations:
        if not args.dry_run:
            shutil.copytree(source, destination)
        print(('Would install: ' if args.dry_run else 'Installed: ') + str(destination))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except OSError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(2)
