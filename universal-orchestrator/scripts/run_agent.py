#!/usr/bin/env python3
"""Bounded CLI worker launcher. No SDKs, credentials, quota scraping or scheduler."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time


ROLES = {
    'planner': ('claude', 'claude-opus-5-5', (2, 1, 280)),
    'coder': ('codex', 'gpt-6.1-sol', None),
    'scout': ('agy', 'gemini-3.8-flash-low', None),
    'advisor': ('claude', 'claude-fable-5-2', (2, 1, 321)),
    'helper': ('claude', 'claude-sonnet-5-5', (2, 1, 284)),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def save_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def resolve_cli(name):
    if os.name != 'nt':
        found = shutil.which(name)
        if found:
            return str(Path(found).resolve())
    else:
        # Respect PATH order instead of selecting a later bundled native binary.
        found = shutil.which(name)
        if found:
            candidate = Path(found)
            if candidate.suffix.lower() in ('.exe', '.ps1'):
                return str(candidate.resolve())
            if candidate.suffix.lower() == '.cmd' and candidate.with_suffix('.ps1').is_file():
                return str(candidate.with_suffix('.ps1').resolve())
    raise ValueError(f'{name}: native executable or supported launcher not found on PATH')


def launch_command(executable, arguments, cwd, stdin_file, folder):
    """Keep task text out of shell syntax and OS command-line arguments."""
    if os.name == 'nt' and Path(executable).suffix.lower() == '.ps1':
        pwsh = shutil.which('pwsh.exe')
        if not pwsh:
            raise ValueError('PowerShell 7.3+ (pwsh.exe) is needed for npm .ps1 launchers')
        spec = folder / 'invocation.json'
        save_json(spec, {'executable': executable, 'arguments': arguments,
                         'cwd': str(cwd), 'stdin_file': str(stdin_file) if stdin_file else None})
        return [pwsh, '-NoProfile', '-NonInteractive', '-File',
                str(Path(__file__).with_name('invoke.ps1')), '-SpecPath', str(spec)], False
    return [executable, *arguments], bool(stdin_file)


def stop_tree(process):
    if process.poll() is not None:
        return
    if os.name == 'nt':
        result = subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                                capture_output=True, timeout=15)
        if result.returncode and process.poll() is None:
            raise RuntimeError(f'Could not stop process tree {process.pid}')
    else:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
    process.wait(timeout=10)


def process_options():
    if os.name == 'nt':
        return {'creationflags': subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP}
    return {'start_new_session': True}


def version_info(name):
    executable = resolve_cli(name)
    with tempfile.TemporaryDirectory(prefix='orchestrator-probe-') as temp:
        command, _ = launch_command(executable, ['--version'], Path.cwd(), None, Path(temp))
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, **process_options())
        try:
            stdout, stderr = process.communicate(timeout=20)
        except (subprocess.TimeoutExpired, KeyboardInterrupt):
            stop_tree(process)
            raise ValueError(f'{name}: version probe interrupted or timed out')
    output = (stdout + stderr).decode('utf-8', errors='replace').strip()
    if process.returncode:
        raise ValueError(f'{name}: version probe failed: {output[:500]}')
    match = re.search(r'\b(\d+)\.(\d+)\.(\d+)\b', output)
    if not match:
        raise ValueError(f'{name}: unrecognized version: {output[:200]}')
    return executable, tuple(map(int, match.groups())), output


def doctor():
    report = {'checked_at': utc_now(), 'quota_status': 'unknown', 'clis': {}}
    for name in ('codex', 'claude', 'agy'):
        try:
            executable, version, output = version_info(name)
            entry = {'path': executable, 'version': output}
            if name == 'claude':
                entry['role_compatible'] = {
                    role: version >= minimum for role, (cli, _, minimum) in ROLES.items()
                    if cli == 'claude'
                }
            report['clis'][name] = entry
        except (ValueError, OSError) as error:
            report['clis'][name] = {'error': str(error)}
    installed = all('error' not in value for value in report['clis'].values())
    compatible = all(report['clis'].get('claude', {}).get('role_compatible', {}).values())
    report['workflow_ready'] = installed and compatible
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['workflow_ready'] else 2


def configuration(args):
    cli, model, minimum = ROLES[args.role]
    if args.model:
        if args.role == 'scout':
            if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]*', args.model):
                raise ValueError('Invalid scout model identifier')
        elif args.role == 'helper' and args.model in ('claude-sonnet-5-5', 'claude-opus-5-5'):
            minimum = (2, 1, 280) if args.model == 'claude-opus-5-5' else (2, 1, 284)
        else:
            raise ValueError('Only scout/helper models may change; planner/coder/advisor are pinned')
        model = args.model
    if not 0 < args.timeout <= 86400:
        raise ValueError('timeout must be between 1 and 86400 seconds')
    if args.max_budget_usd is not None and (cli != 'claude' or not 0 < args.max_budget_usd < float('inf')):
        raise ValueError('A positive finite max-budget-usd is supported only for Claude roles')
    return cli, model, minimum


def cli_arguments(cli, model, output, args):
    if cli == 'codex':
        return ['exec', '--model', model, '--sandbox', 'workspace-write', '--json',
                '--output-last-message', str(output / 'answer.txt'), '-']
    if cli == 'agy':
        return ['--model', model, '--mode', 'plan', '--disable-slash-commands',
                '--output-format', 'json', '--print-timeout', f'{args.timeout}s',
                '--print', 'Complete the task supplied on stdin. Do not change source files.']
    result = ['--model', model, '--tools', '', '--strict-mcp-config', '--mcp-config',
              '{"mcpServers":{}}', '--disable-slash-commands', '--output-format', 'json',
              '--print', 'Use only the supplied context. Return analysis or decisions, never code or patches.']
    if args.max_budget_usd is not None:
        result.extend(['--max-budget-usd', str(args.max_budget_usd)])
    return result


def run_agent(args):
    cli, model, minimum = configuration(args)
    worktree = Path(args.worktree).resolve(strict=True)
    if not worktree.is_dir():
        raise ValueError('worktree must be a directory')
    prompt_path = Path(args.prompt).resolve(strict=True)
    task = prompt_path.read_text(encoding='utf-8-sig')
    if not task.strip():
        raise ValueError('prompt file is empty')
    output = Path(args.out).resolve()
    if output == worktree or worktree in output.parents:
        raise ValueError('out must be outside the worker worktree')
    if output.exists():
        raise ValueError('out already exists; use a unique directory for each invocation')
    executable, version, version_text = version_info(cli)
    arguments = cli_arguments(cli, model, output, args)
    request = {'role': args.role, 'cli': cli, 'requested_model': model,
               'cli_version': version_text, 'executable': executable, 'arguments': arguments,
               'worktree': str(worktree), 'out': str(output), 'timeout_seconds': args.timeout,
               'version_compatible': minimum is None or version >= minimum,
               'minimum_version': '.'.join(map(str, minimum)) if minimum else None}
    if args.dry_run:
        print(json.dumps(request, ensure_ascii=False, indent=2))
        return 0 if request['version_compatible'] else 2
    if not request['version_compatible']:
        raise ValueError(f'{model} needs {cli} >= {request["minimum_version"]}; found {version_text}')
    output.mkdir(parents=True, exist_ok=False)
    save_json(output / 'request.json', request)
    marker = 'advisor' if args.role in ('planner', 'advisor', 'helper') else 'worker'
    policy = (f'WORKFLOW_ROLE={marker}\nAssigned role: {args.role}. Do not spawn other agents.\n'
              'Do not change files, produce code or patches.\n' if marker == 'advisor' else
              'WORKFLOW_ROLE=worker\nDo not spawn other agents. Follow the assigned file scope.\n')
    (output / 'prompt.txt').write_text(policy + '\n' + task, encoding='utf-8')
    record = {'status': 'starting', 'started_at': utc_now(), 'requested_model': model,
              'effective_model': 'not_verified', 'task_accepted': False}
    save_json(output / 'result.json', record)
    process = None
    started = time.monotonic()
    exit_code = 1
    try:
        command, direct_stdin = launch_command(executable, arguments, worktree, output / 'prompt.txt', output)
        with (output / 'prompt.txt').open('rb') as input_file, (output / 'stdout.log').open('wb') as stdout, (output / 'stderr.log').open('wb') as stderr:
            process = subprocess.Popen(command, cwd=worktree,
                                       stdin=input_file if direct_stdin else subprocess.DEVNULL,
                                       stdout=stdout, stderr=stderr, **process_options())
            record.update(status='running', pid=process.pid)
            save_json(output / 'result.json', record)
            try:
                exit_code = process.wait(timeout=args.timeout)
                record['status'] = 'exited' if exit_code == 0 else 'failed'
            except subprocess.TimeoutExpired:
                stop_tree(process)
                exit_code = 124
                record['status'] = 'timed_out'
            except KeyboardInterrupt:
                stop_tree(process)
                exit_code = 130
                record['status'] = 'cancelled'
    except Exception as error:
        if process is not None and process.poll() is None:
            stop_tree(process)
        record.update(status='launcher_error', error=str(error))
    finally:
        record.update(exit_code=exit_code, finished_at=utc_now(),
                      elapsed_seconds=round(time.monotonic() - started, 2))
        save_json(output / 'result.json', record)
    print(json.dumps({'out': str(output), **record}, ensure_ascii=False, indent=2))
    return exit_code if 0 <= exit_code <= 255 else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('doctor', help='Check installed versions without a model request')
    run = commands.add_parser('run', help='Run one bounded worker in an existing worktree')
    run.add_argument('--role', choices=ROLES, required=True)
    for name in ('worktree', 'prompt', 'out'):
        run.add_argument('--' + name, required=True)
    run.add_argument('--model')
    run.add_argument('--timeout', type=int, default=900)
    run.add_argument('--max-budget-usd', type=float)
    run.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    try:
        return doctor() if args.command == 'doctor' else run_agent(args)
    except (ValueError, OSError) as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
