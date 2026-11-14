import argparse
from contextlib import redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('launcher', ROOT / 'universal-orchestrator/scripts/run_agent.py')
launcher = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(launcher)


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='skill-check-')
        self.root = Path(self.temp.name)
        self.tree = self.root / 'tree space & value'
        self.tree.mkdir()
        self.prompt = self.root / 'task & literal.txt'
        self.prompt.write_text('Türkçe görev\n$(echo INJECTED) & `literal` "quoted"', encoding='utf-8')
        self.output = self.root / 'run space & value'
        (self.root / 'heartbeat_child.py').write_text('import pathlib,time\np=pathlib.Path("heartbeat")\nwhile True:\n p.write_text(str(time.time()))\n time.sleep(.1)\n', encoding='utf-8')
        self.fixture = self.root / 'fake_cli.py'
        self.fixture.write_text('''import json, os, pathlib, subprocess, sys, time
if '--version' in sys.argv:
    print('2.1.999')
    sys.exit(0)
if os.environ.get('FIXTURE_SLEEP'):
    subprocess.Popen([sys.executable, str(pathlib.Path(__file__).with_name('heartbeat_child.py'))])
    time.sleep(30)
data = {'args':sys.argv[1:], 'stdin':sys.stdin.read(), 'cwd':os.getcwd()}
print(json.dumps(data, ensure_ascii=False))
if '--output-last-message' in sys.argv:
    pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text('fixture answer', encoding='utf-8')
''', encoding='utf-8')
        self.shim = self.root / 'fake_cli.ps1'
        python_path = sys.executable.replace("'", "''")
        self.shim.write_text("$OutputEncoding=[System.Text.UTF8Encoding]::new($false)\n"
                             f"$input | & '{python_path}' (Join-Path $PSScriptRoot 'fake_cli.py') @args\n"
                             'exit $LASTEXITCODE\n', encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def args(self, **overrides):
        values = dict(role='coder', worktree=str(self.tree), prompt=str(self.prompt),
                      out=str(self.output), model=None, timeout=10,
                      max_budget_usd=None, dry_run=False)
        values.update(overrides)
        return argparse.Namespace(**values)

    def invoke(self, args):
        if os.name == 'nt':
            executable = str(self.shim)
            argument_patch = None
        else:
            executable = sys.executable
            original = launcher.cli_arguments
            argument_patch = patch.object(launcher, 'cli_arguments', side_effect=lambda *a: [str(self.fixture), *original(*a)])
        with patch.object(launcher, 'version_info', return_value=(executable, (2, 1, 999), '2.1.999')), redirect_stdout(io.StringIO()):
            if argument_patch:
                with argument_patch:
                    return launcher.run_agent(args)
            return launcher.run_agent(args)

    def test_coder_stdin_paths_and_logs(self):
        self.assertEqual(self.invoke(self.args()), 0)
        data = json.loads((self.output / 'stdout.log').read_text(encoding='utf-8-sig'))
        self.assertIn('Türkçe görev', data['stdin'])
        self.assertIn('$(echo INJECTED)', data['stdin'])
        self.assertEqual(Path(data['cwd']), self.tree)
        self.assertEqual((self.output / 'answer.txt').read_text(), 'fixture answer')
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['status'], 'exited')
        self.assertFalse(result['task_accepted'])

    def test_advisor_has_empty_tools_argument(self):
        self.assertEqual(self.invoke(self.args(role='advisor')), 0)
        data = json.loads((self.output / 'stdout.log').read_text(encoding='utf-8-sig'))
        self.assertEqual(data['args'][data['args'].index('--tools') + 1], '')
        self.assertIn('WORKFLOW_ROLE=advisor', data['stdin'])
        self.assertIn('claude-fable-5-2', data['args'])

    def test_existing_output_not_overwritten(self):
        self.output.mkdir()
        sentinel = self.output / 'user.txt'
        sentinel.write_text('preserve')
        with self.assertRaises(ValueError):
            self.invoke(self.args())
        self.assertEqual(sentinel.read_text(), 'preserve')

    def test_old_claude_blocked_before_invocation(self):
        with patch.object(launcher, 'version_info', return_value=('not-launched', (2, 1, 206), '2.1.206')):
            with self.assertRaisesRegex(ValueError, '2.1.321'):
                launcher.run_agent(self.args(role='advisor'))
        self.assertFalse(self.output.exists())

    def test_dry_run_writes_no_run_files(self):
        self.assertEqual(self.invoke(self.args(dry_run=True)), 0)
        self.assertFalse(self.output.exists())

    def test_pinned_model_cannot_silently_change(self):
        with self.assertRaises(ValueError):
            self.invoke(self.args(model='another-model'))

    def test_logs_cannot_pollute_worker_tree(self):
        with self.assertRaises(ValueError):
            self.invoke(self.args(out=str(self.tree / 'logs')))

    def test_timeout_stops_descendants(self):
        with patch.dict(os.environ, {'FIXTURE_SLEEP': '1'}):
            self.assertEqual(self.invoke(self.args(timeout=3)), 124)
        result = json.loads((self.output / 'result.json').read_text())
        self.assertEqual(result['status'], 'timed_out')
        heartbeat = self.tree / 'heartbeat'
        self.assertTrue(heartbeat.exists())
        before = heartbeat.read_text()
        time.sleep(.4)
        self.assertEqual(heartbeat.read_text(), before)

    def test_installer_copies_both_hosts_and_refuses_overwrite(self):
        install = ROOT / 'install-skill.py'
        result = subprocess.run([sys.executable, str(install), '--project', str(self.tree), '--dry-run'], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.tree / '.agents').exists())
        result = subprocess.run([sys.executable, str(install), '--project', str(self.tree)], capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        for host in ('.agents', '.claude'):
            copied = self.tree / host / 'skills/universal-orchestrator/SKILL.md'
            self.assertEqual(copied.read_bytes(), (ROOT / 'universal-orchestrator/SKILL.md').read_bytes())
        result = subprocess.run([sys.executable, str(install), '--project', str(self.tree)], capture_output=True)
        self.assertEqual(result.returncode, 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
