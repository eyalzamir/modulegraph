"""
Tests that deal with setuptools namespace
packages, and in particular the installation
flavour used by pip
"""
import os
import shutil
import sys
import subprocess
import unittest
import textwrap

from modulegraph import modulegraph

gRootDir = os.path.dirname(os.path.abspath(__file__))
gSrcDir = os.path.join('testpkg-setuptools-namespace')

def install_testpkg(test_dir):
    p = subprocess.Popen([
        sys.executable, 'setup.py', 'install', 
            '--install-lib', test_dir, 
            '--single-version-externally-managed', 
            '--record', os.path.join(test_dir, 'record.lst'),
        ], cwd=gSrcDir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    
    data = p.communicate()[0]

    exit = p.wait()
    return exit


class TestPythonBehaviour (unittest.TestCase):
    def setUp(self):
        test_dir = os.path.join(gRootDir, 'test.dir')
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        os.mkdir(test_dir)
        exit = install_testpkg(test_dir)
        self.assertEquals(exit, 0)

    def tearDown(self):
        test_dir = os.path.join(gRootDir, 'test.dir')
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

    def importModule(self, name):
        test_dir = os.path.join(gRootDir, 'test.dir')
        if '.' in name:
            script = textwrap.dedent("""\
                import site
                site.addsitedir(%r)
                try:
                    import %s
                except ImportError:
                    import %s
                print (%s.__name__)
            """) %(test_dir, name, name.rsplit('.', 1)[0], name)
        else:
            script = textwrap.dedent("""\
                import site
                site.addsitedir(%r)
                import %s
                print (%s.__name__)
            """) %(test_dir, name, name)

        p = subprocess.Popen([sys.executable, '-c', script], 
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    'testpkg-relimport'),
        )
        data = p.communicate()[0]
        if sys.version_info[0] != 2:
            data = data.decode('UTF-8')
        data = data.strip()

        sts = p.wait()

        if sts != 0:
            print data
            self.fail("import of %r failed"%(name,))

        return data

    def testToplevel(self):
        m = self.importModule('nspkg.module')
        self.assertEquals(m, 'nspkg.module')

    def testSub(self):
        m = self.importModule('nspkg.nssubpkg.sub')
        self.assertEquals(m, 'nspkg.nssubpkg.sub')

class TestModuleGraphImport (unittest.TestCase):
    if not hasattr(unittest.TestCase, 'assertIsInstance'):
        def assertIsInstance(self, value, types):
            if not isinstance(value, types):
                self.fail("%r is not an instance of %r", value, types)

    def setUp(self):
        test_dir = os.path.join(gRootDir, 'test.dir')
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)

        os.mkdir(test_dir)
        exit = install_testpkg(test_dir)
        self.assertEquals(exit, 0)

        self.mf = modulegraph.ModuleGraph(path=[ test_dir ] + sys.path)

    def tearDown(self):
        test_dir = os.path.join(gRootDir, 'test.dir')
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)


    def testRootPkg(self):
        self.mf.import_hook('nspkg')

        node = self.mf.findNode('nspkg')
        self.assertIsInstance(node, modulegraph.Package)
        self.assertEquals(node.identifier, 'nspkg')

    def testRootPkgModule(self):
        self.mf.import_hook('nspkg.module')

        node = self.mf.findNode('nspkg.module')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'nspkg.module')

    def testSubRootPkgModule(self):
        self.mf.import_hook('nspkg.nssubpkg.sub')

        node = self.mf.findNode('nspkg.nssubpkg.sub')
        self.assertIsInstance(node, modulegraph.SourceModule)
        self.assertEquals(node.identifier, 'nspkg.nssubpkg.sub')

if __name__ == "__main__":
    unittest.main()