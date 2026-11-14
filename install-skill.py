#!/usr/bin/env python3
"""Install this package into project skill directories for Codex and Claude Code."""
import argparse
from datetime import datetime
from pathlib import Path
import shutil
import sys

NAME = 'universal-orchestrator'
# Claude Code only: the skill loads on /universal-orchestrator, never on its own.
CLAUDE_FRONTMATTER = 'disable-model-invocation: true\n'


def claude_skill_text(text):
    if not text.startswith('---\n'):
        raise ValueError('SKILL.md must start with YAML frontmatter')
    end = text.index('\n---', 4)
    if 'disable-model-invocation:' in text[:end]:
        return text
    return text[:end + 1] + CLAUDE_FRONTMATTER + text[end + 1:]


def install(source, destination, host):
    shutil.copytree(source, destination)
    if host == '.claude':
        skill = destination / 'SKILL.md'
        skill.write_text(claude_skill_text(skill.read_text(encoding='utf-8')), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, help='Existing project directory')
    parser.add_argument('--upgrade', action='store_true',
                        help='Replace an existing install; the old copy goes to .skill-backups/')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / NAME
    root = Path(args.project).resolve(strict=True)
    if not root.is_dir() or not (source / 'SKILL.md').is_file():
        parser.error('Project directory or bundled skill is missing')
    targets = [(host, root / host / 'skills' / NAME) for host in ('.agents', '.claude')]
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    # Preflight every destination before changing anything.
    for _, destination in targets:
        if destination.is_symlink():
            parser.error(f'Refusing to replace a symlink: {destination}')
        if destination.exists():
            if not args.upgrade:
                parser.error(f'Destination already exists (use --upgrade): {destination}')
            if not (destination / 'SKILL.md').is_file():
                parser.error(f'Not a skill directory, refusing to replace: {destination}')
        if source == destination or source in destination.parents:
            parser.error('Cannot install a skill inside itself')
    for host, destination in targets:
        if destination.exists():
            # Backups live outside the skills directory so hosts never discover them as skills.
            backup = root / '.skill-backups' / f'{NAME}-{host.strip(".")}-{stamp}'
            print(('Would back up: ' if args.dry_run else 'Backed up: ') + f'{destination} -> {backup}')
            if not args.dry_run:
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(destination), str(backup))
        if not args.dry_run:
            install(source, destination, host)
        print(('Would install: ' if args.dry_run else 'Installed: ') + str(destination))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(2)
