#!/usr/bin/python
import autograde
import os, os.path

assignment_name = 'PA2'
release='1'

class MLTests(autograde.AbstractTestGroup):
    def get_tests(self, prog, data_dir):
        prefix = 'test.'
        if self.name:
            prefix = prefix + self.name + '.'

        train_suffix = '.train.txt'
        data_suffix = '.data.txt'
        ref_suffix = '.ref.txt'

        fnames = [fname for fname in os.listdir(data_dir)
                   if fname.startswith(prefix) and fname.endswith(train_suffix)]
        fnames.sort()

        for fname in fnames:
            id = fname[:-len(train_suffix)]
            data_name = id + data_suffix
            ref_name = id + ref_suffix

            train = os.path.join(data_dir, fname)

            data = os.path.join(data_dir, data_name)
            if not os.path.exists(data):
                autograde.logger.warning('Missing data file %r', data_name)
                continue

            ref = os.path.join(data_dir, ref_name)
            if not os.path.exists(ref):
                autograde.logger.warning('Missing reference file %r', ref_name)
                continue

            yield autograde.FileTest(cmd = [prog, train, data], ref_file = ref)


assignment = MLTests.Project('learn', weight=4)

if __name__ == '__main__':
    autograde.main(assignment_name, assignment, release)
