#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test script to run the command interface for testing."""
from __future__ import print_function
import sys
import os
import unicodedata
from unittest import TestCase
from tempfile import mkdtemp
from shutil import rmtree
import six
try:
    import sh
except ImportError:
    import pbs

    class Sh(object):
        """Sh style wrapper."""

        def __getattr__(self, attr):
            """Return command object like sh."""
            return pbs.Command(attr)

        # pylint: disable=invalid-name
        @staticmethod
        def Command(attr):
            """Return command object like sh."""
            for key in os.environ:
                if six.PY2 and not isinstance(os.environ[key], str):
                    print('Converting {} = {}({})'.format(key, type(os.environ[key]), os.environ[key]))
                    os.environ[key] = str(unicodedata.normalize('NFKD', os.environ[key]).encode('ascii', 'ignore'))
                    print('Converting {} = {}({})'.format(key, type(os.environ[key]), os.environ[key]))
            return pbs.Command(attr)
    sh = Sh()
import peewee
from pacifica.cartd.orm import DB
from pacifica.cartd.__main__ import cmd, main
from ..cart_db_setup_test import TestCartdBase


class TestAdminCmdBase(TestCase):
    """Test base class to setup update conditions."""

    virtualenv_dir = mkdtemp()

    @classmethod
    def setUpClass(cls):
        """Setup a virtualenv and install the original version."""
        python_cmd = sh.Command(sys.executable)
        python_exe = os.path.basename(sys.executable)
        python_cmd('-m', 'virtualenv', '--python', sys.executable, cls.virtualenv_dir)
        python_venv_cmd = None
        for exe_dir in ['bin', 'Scripts']:
            fpath = os.path.join(cls.virtualenv_dir, exe_dir, python_exe)
            if os.path.isfile(fpath) and os.access(fpath, os.X_OK):
                python_venv_cmd = sh.Command(fpath)
        python_venv_cmd('-m', 'pip', 'install', 'pacifica-cartd==0.2.0')
        if os.path.exists('db.sqlite3'):
            os.unlink('db.sqlite3')
        python_venv_cmd('-c', 'import sys; from pacifica.cartd.__main__ import cmd; sys.exit(cmd())', 'dbsync')

    @classmethod
    def tearDownClass(cls):
        """Remove the virtualenv dir."""
        rmtree(cls.virtualenv_dir)
        DB.close()
        os.unlink('db.sqlite3')


class TestAdminCmd(TestAdminCmdBase):
    """Test the admin commands for error conditions."""

    def test_dbchk(self):
        """Test that dbchk doesn't work."""
        self.assertEqual(cmd('dbchk'), -1)

    def test_dbchk_equal(self):
        """Test that dbchk doesn't work."""
        self.assertEqual(cmd('dbchk', '--equal'), -1)

    def test_main(self):
        """Test that dbchk doesn't work."""
        with self.assertRaises(peewee.OperationalError):
            main('--stop-after-a-moment')

    def test_dump(self):
        """test that the dump command works."""
        os.environ['VOLUME_PATH'] = '{}{}'.format(mkdtemp(), os.path.sep)
        tcb = TestCartdBase()
        tcb.setUp()
        cart = TestCartdBase.create_sample_cart('EFEFEFE')
        TestCartdBase.create_sample_file(cart)
        self.assertEqual(cmd('dump'), 0)
        self.assertEqual(cmd('dump', '--json'), 0)
        tcb.tearDown()


class TestAdminCmdSync(TestAdminCmdBase):
    """Test the database upgrade scripting."""

    def test_dbsync(self):
        """Run the update by calling dbsync."""
        self.assertEqual(cmd('dbsync'), 0)

    def test_main(self):
        """Test that dbchk doesn't work."""
        cmd('dbsync')
        cmd('dbsync')
        hit_exception = False
        try:
            main('--stop-after-a-moment', '--cpconfig', 'server.conf')
        # pylint: disable=broad-except
        except Exception:
            hit_exception = True
        self.assertFalse(hit_exception)
