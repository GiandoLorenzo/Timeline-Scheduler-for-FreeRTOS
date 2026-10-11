import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import os

ROOT = Path(__file__).resolve().parents[2]

def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'Tools' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

generator = load('scheduler_generator')
runner = load('run_qemu_test')

class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / 'Tools/system_config.json').read_text())

    def validate(self, config):
        with contextlib.redirect_stdout(io.StringIO()):
            return generator.validate_schedule(config)

    def test_example(self):
        self.assertTrue(self.validate(self.config))

    def test_malformed_inputs(self):
        invalid = [None, [], {}, dict(self.config, timeline_period=0),
                   dict(self.config, timeline_period=True), dict(self.config, tick_rate_hz=-1),
                   dict(self.config, tasks=[]), dict(self.config, tasks=[None]),
                   dict(self.config, tasks=self.config['tasks'] * 3)]
        for key, value in [('name', 'A"; injected(); //'), ('type', 'INVALID'),
                           ('stack_size', -1), ('stack_size', True), ('start_tick', 1.5),
                           ('start_tick', -1), ('end_tick', 1001), ('end_tick', 0)]:
            changed = copy.deepcopy(self.config)
            changed['tasks'][0][key] = value
            invalid.append(changed)
        for config in invalid:
            with self.subTest(config=config):
                self.assertFalse(self.validate(config))

    def test_duplicates_and_overlaps(self):
        self.config['tasks'][1]['name'] = self.config['tasks'][0]['name']
        self.assertFalse(self.validate(self.config))
        self.config['tasks'][1]['name'] = 'Other'
        self.config['tasks'][1]['type'] = 'HARD'
        self.config['tasks'][1]['start_tick'] = 50
        self.assertFalse(self.validate(self.config))

    def test_escaping_and_configuration_guards(self):
        self.config['system_name'] = '*/ "quoted" \\ name'
        self.assertTrue(self.validate(self.config))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'main.c'
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertTrue(generator.generate_c_code(self.config, output))
            source = output.read_text()
            self.assertIn('configTIMELINE_PERIOD == 1000', source)
            self.assertIn('configTICK_RATE_HZ == 1000', source)
            self.assertIn(json.dumps('System: ' + self.config['system_name'] + '\r\n'), source)
            self.assertNotIn(self.config['system_name'], source.split('#include')[0])

    def test_failed_write_returns_nonzero(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'Tools/scheduler_generator.py'),
                                     '-c', str(ROOT / 'Tools/system_config.json'),
                                     '-o', str(Path(directory) / 'missing/main.c')], capture_output=True)
            self.assertNotEqual(result.returncode, 0)

class ResultTests(unittest.TestCase):
    def test_exact_result_required(self):
        self.assertTrue(runner.check_log('TEST_RESULT 6 PASS\r\n', 6))
        for log in ['TEST PASSED', 'TEST_RESULT 5 PASS', 'TEST_RESULT 6 PASS_suffix',
                    'TEST_RESULT 6 PASS\nTEST_RESULT 6 FAIL', 'ERROR: crash\nTEST_RESULT 6 PASS']:
            with self.subTest(log=log):
                self.assertFalse(runner.check_log(log, 6))

    def test_emulator_early_exit_is_not_success(self):
        self.run_child('print("TEST_RESULT 6 PASS", flush=True)', expected=1)

    def test_intentional_timeout_with_explicit_pass(self):
        self.run_child('import time; print("TEST_RESULT 6 PASS", flush=True); time.sleep(10)', expected=0)

    def run_child(self, source, expected):
        # Exercise real pipe handling and timeout behavior without needing QEMU.
        original_popen = subprocess.Popen
        def child(_command, **kwargs):
            return original_popen([sys.executable, '-c', source], **kwargs)
        previous = Path.cwd()
        with tempfile.TemporaryDirectory() as directory:
            try:
                os.chdir(directory)
                with mock.patch.object(sys, 'argv', ['checker', '--project', 'DemoTest', '--test', '6', '--timeout', '0.5']), \
                     mock.patch.object(runner.subprocess, 'Popen', side_effect=child), \
                     contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(runner.main(), expected)
                self.assertTrue(Path('artifacts/test6.log').exists())
            finally:
                os.chdir(previous)

if __name__ == '__main__':
    unittest.main()
