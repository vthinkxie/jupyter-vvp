import os
import unittest

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

from vvpmagics import vvpmagics

travis = os.environ.get('TRAVIS', False)

def run_notebook(notebook_path):
    nb_name, _ = os.path.splitext(os.path.basename(notebook_path))
    dirname = os.path.dirname(notebook_path)

    with open(notebook_path) as f:
        nb = nbformat.read(f, as_version=4)

    proc = ExecutePreprocessor(timeout=600)
    proc.allow_errors = True

    proc.preprocess(nb, {'metadata': {'path': '/'}})
    output_path = os.path.join(dirname, '{}_all_output.ipynb'.format(nb_name))

    with open(output_path, mode='wt') as f:
        nbformat.write(nb, f)
    errors = []
    for cell in nb.cells:
        for output in cell.get('outputs', []):
            if output.output_type == 'error':
                errors.append(output)
    return nb, errors


class IntegrationTest(unittest.TestCase):

    @unittest.skipIf(travis, 'Requires locally running VVP backend.')
    def test_connect_notebook(self):
        nb, errors = run_notebook('ConnectToVVP.ipynb')
        self.assertEqual(errors, [])


if __name__ == '__main__':
    unittest.main()
