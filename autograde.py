"""Automated grading of programming assignments.
"""
__author__  = 'David Menendez'
__version__ = '1.0'

import os, os.path, sys
import logging, threading, subprocess, itertools, collections

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30

NORMAL, EXTRA, USER = range(3)
category_names = ['Points', 'Extra credit', 'User tests']

Score = collections.namedtuple('Score', 'category group given points')

class Error(Exception):
    pass

class CommandError(Error):
    def __init__(self, cmd, code, out=None):
        self.cmd = cmd
        self.code = code
        self.out = out

def run_command(cmd):
    logger.debug('Running %s', cmd)
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out,err)= p.communicate()

    if p.returncode != 0:
        raise CommandError(cmd, p.returncode, out)

class Test(object):
    def __init__(self, cmd, ref_code=0, timeout=DEFAULT_TIMEOUT):
        self.cmd = cmd
        self.ref_code = ref_code
        self.timeout = timeout

    def reference_output(self):
        return ''

    def compare_output(self, out):
        reflines = self.reference_output().split('\n')
        outlines = out.split('\n')
        errors = []
        for i,(refl,outl) in enumerate(itertools.izip_longest(reflines, outlines), 1):
            if outl is None:
                errors += [
                    'line ' + str(i),
                    '  expected: ' + repr(refl),
                    '  received nothing']
            elif refl is None:
                errors += ['extra lines in output']
                break
            elif outl != refl:
                errors += [
                    'line ' + str(i),
                    '  expected: ' + repr(refl),
                    '  received: ' + repr(outl)]

        return errors

    def run(self):
        logger.debug('Running %s', self.cmd)
        p = subprocess.Popen(self.cmd,
            stdin  = subprocess.PIPE,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT)

        timer = threading.Timer(self.timeout, p.kill)

        try:
            timer.start()
            out, err = p.communicate()
        finally:
            timer.cancel()

        logger.debug('Complete. Code %s\n%s', p.returncode, out)
        self.output = out.rstrip()
        self.returncode = p.returncode
        self.errors = []

        if p.returncode == -9:
            self.comment = 'timed out'
            return False
        if p.returncode != self.ref_code:
            self.comment = 'unexpected return code ' + str(p.returncode)
            return False

        errors = self.compare_output(self.output)
        if errors:
            self.comment = 'incorrect output'
            self.errors = errors
            return False

        self.comment = 'correct'
        return True

    def print_output(self):
        if not hasattr(self, 'output'):
            raise Exception('print_output called before run')

        print
        print 'output'
        print '------'
        print self.output
        print '------'

    def print_input(self):
        pass

class FileTest(Test):
    def __init__(self, cmd, ref_file, **kws):
        super(FileTest, self).__init__(cmd, **kws)
        self.ref_file = ref_file

    def reference_output(self):
        try:
            logger.debug('Opening reference file %r', self.ref_file)
            return open(self.ref_file).read().rstrip()
        except IOError as e:
            raise Error('Unable to open reference file {!r}: {}'.format(
                self.ref_file, e.strerror))

    def run(self):
        correct = super(FileTest,self).run()
        if not correct and self.returncode == 0:
            self.errors.insert(0, 'reference file: ' + repr(self.ref_file))

        return correct

class AbstractTestGroup(object):
    @classmethod
    def Project(cls, name, *args, **kws):
        tests = cls(*args, **kws)
        return Project(name, tests)

    def __init__(self, id=None, weight=1, name=None, category=NORMAL):
        self.id = id
        self.name = name or id
        self.weight = weight
        self.category = category

    def get_tests(self, prog, data_dir):
        raise NotImplementedError

class StringTests(AbstractTestGroup):
    """Look for tests in a file named <prefix><id><suffix>.
    """
    def __init__(self, prefix='tests', suffix='.txt', **kws):
        super(StringTests, self).__init__(**kws)
        self.file = prefix + (self.id or '') + suffix

    def get_tests(self, prog, data_dir):
        test_file = os.path.join(data_dir, self.file)

        if not os.path.exists(test_file):
            logger.warning('Test file not found: %r', test_file)
            return

        logger.debug('Opening tests file: %r', test_file)

        try:
            lines = open(test_file)

            while True:
                arg = next(lines).rstrip()
                ref = next(lines).rstrip()

                yield self.Test([prog, arg], ref)

        except StopIteration:
            return

    class Test(Test):
        def __init__(self, cmd, ref, **kws):
            super(StringTests.Test, self).__init__(cmd=cmd, **kws)
            self.ref = ref

        def reference_output(self):
            return self.ref

class FileTests(AbstractTestGroup):
    """Look for pairs of test files containin the input and reference output.

    If id is None, they are named:
        <prefix><test><arg_suffix>
        <prefix><test><ref_suffix>

    Otherwise, they are named:
        <prefix><id>.<test><arg_suffix>
        <prefix><id>.<test><ref_suffix>
    """
    def __init__(self, prefix='test.', arg_suffix='.txt', ref_suffix='.ref.txt', **kws):
        super(FileTests, self).__init__(**kws)
        self.arg_suffix = arg_suffix
        self.ref_suffix = ref_suffix

        if self.id:
            self.prefix = prefix + self.id + '.'
        else:
            self.prefix = prefix

    def get_tests(self, prog, data_dir):
        # gather the names of the reference files in data_dir
        fnames = [fname for fname in os.listdir(data_dir)
                    if fname.startswith(self.prefix)
                    and fname.endswith(self.ref_suffix)]
        fnames.sort()

        # for each reference name, check for the corresponding input file
        for ref_name in fnames:
            # swap ref_suffix for input suffix
            arg_name = ref_name[:-len(self.ref_suffix)] + self.arg_suffix
            arg = os.path.join(data_dir, arg_name)

            # skip this name if no input file exists
            if not os.path.exists(arg):
                logger.warning('Unmatched reference file: %s', ref_name)
                continue

            ref = os.path.join(data_dir, ref_name)

            yield self.Test(prog, arg, ref)


    class Test(FileTest):
        def __init__(self, prog, arg, ref_file, **kws):
            super(FileTests.Test, self).__init__(cmd=[prog, arg], ref_file=ref_file, **kws)
            self.input_file = arg

        def print_input(self):
            try:
                logger.debug('Opening input file %r', self.input_file)
                input = open(self.input_file).read().rstrip()

                print
                print 'input'
                print '-----'
                print input
                print '-----'

            except IOError as e:
                raise Error('Unable to open input file {}: {}'.format(
                    self.input_file, e.strerror))


class AbstractProject(object):
    def get_scores(self, src_dir, data_dir, **kws):
        raise NotImplementedError(type(self).__name__ +
            ' does not implement get_scores')

    def grade(self, src_dir, data_dir, **kws):
        """Test this project using get_scores and print out the results.
        """

        scores = collections.defaultdict(list)
        name_width = 5

        for score in self.get_scores(src_dir, data_dir, **kws):
            logger.debug('Got score %s', score)
            scores[score.category].append(score)
            name_width = max(name_width, len(score.group))

        for category, catscores in scores.iteritems():
            total_score = 0
            total_points = 0

            print
            print category_names[category]
            print '{0:{1}} Score   Max'.format(' ', name_width)
            for score in catscores:
                print '{0.group:{1}} {0.given:5.1f} {0.points:5.1f}'.format(score, name_width)
                total_score  += score.given
                total_points += score.points

            if len(catscores) > 1:
                print '-' * name_width, '-----', '-----'
                print '{0:{1}} {2:5.1f} {3:5.1f}'.format('Total',
                    name_width, total_score, total_points)

    def grade_archive(self, archive, src_subdir, data_dir, **kws):
        """Unpack a Tar archive to a temporary directory, then use grade
        to test the project and print out scores.
        """
        import tempfile, shutil

        archive = os.path.realpath(archive)
        logger.debug('Archive path: %r', archive)
        if not os.path.exists(archive):
            raise Error('archive not found: ' + repr(archive))

        temp_dir = tempfile.mkdtemp()
        try:
            logger.debug('Created temporary directory: %r', temp_dir)

            os.chdir(temp_dir)
            run_command(['tar', 'xf', archive])

            if not os.path.isdir(src_subdir):
                raise Error('archive does not contain directory ' +
                    repr(src_subdir))

            src_dir = os.path.realpath(src_subdir)

            self.grade(src_dir, data_dir, **kws)

        finally:
            logger.debug('Deleting temporary directory')
            shutil.rmtree(temp_dir)


class Project(AbstractProject):
    def __init__(self, name, *groups, **kws):
        self.name = name
        self.groups = groups
        self.prog = kws.get('prog_name', name)
        self.timeout = kws.get('timeout', DEFAULT_TIMEOUT)

        user_class = kws.get('user_class', type(groups[0]))
        if user_class is None:
            self.user_group = None
        else:
            self.user_group = user_class(category=USER)

        # make sure the groups have distinct ids
        groupids = collections.Counter(g.id for g in groups)
        if len(groupids) < len(groups):
            raise ValueError('Duplicate test group ids: ' +
                    str([g for g in groupids if groupids[g] > 1]))

    def build(self):
        run_command(['make', 'clean'])

        if os.path.exists(self.prog):
            raise Error('not removed by "make clean"')

        run_command(['make'])

        if not os.path.exists(self.prog):
            raise Error('not created by "make"')

    def get_group_score(self, group, prog, test_dir, verbosity, scores, points):
        name = self.name if group.name is None else \
            self.name + ':' + group.name

        num_correct = 0
        num_tested = 0
        for test in group.get_tests(prog, test_dir):
            num_tested += 1
            if test.run():
                num_correct += 1

                if verbosity < 2:
                    continue

            print
            print '{0}: {1}'.format(self.name, test.comment)
            print '  called as', test.cmd

            if verbosity < 0:
                continue

            for line in test.errors:
                print ' ', line

            if verbosity < 1:
                continue

            test.print_input()
            test.print_output()

        score = num_correct * group.weight
        point = num_tested * group.weight
        logger.info('Group %s. Correct %s/%s. Score %s/%s',
            name, num_correct, num_tested, score, point)

        scores[group.category][name] += score
        points[group.category][name] += point

        return num_tested


    def get_scores(self, src_dir, data_dir, verbosity=0, requests=None, **kws):
        logger.info('Grading %r', self.name)

        # check for src_dir
        if not os.path.isdir(src_dir):
            logger.info('Source dir not found: %r', src_dir)
            return []

        # check for data_dir
        if not os.path.isdir(data_dir):
            raise Error('Data directory not found: ' + repr(data_dir))

        logger.debug('Requests: %s', requests)
        groups = self.groups
        if requests and self.name not in requests:
            groups = [g for g in self.groups
                if g.name is not None and self.name + ':' + g.name in requests]

        if not groups:
            return []

        prog = './' + self.prog

        try:
            os.chdir(src_dir)
            self.build()

            scores = collections.defaultdict(collections.Counter)
            points = collections.defaultdict(collections.Counter)
            num_tests = 0

            for group in groups:
                num_tests += self.get_group_score(group, prog, data_dir, verbosity, scores, points)

            if self.user_group and os.path.isdir('test'):
                num_tests += self.get_group_score(
                    self.user_group, prog, 'test', verbosity, scores, points)

            print
            print "{0}: {1} tests complete".format(self.name, num_tests)
            return [
                Score(category=category, group=group, given=catscores[group],
                    points=points[category][group])
                    for category,catscores in scores.iteritems()
                    for group in sorted(catscores.keys())]

        except EnvironmentError as e:
            print
            print '{0}: {1}'.format(self.name, e.strerror)
            if e.filename:
                print ' ', e.filename

        except CommandError as e:
            print
            print '{0}: error running {1.cmd[0]!r} (return code {1.code})'.format(self.name, e)
            if len(e.cmd) > 1:
                print '  arguments:', e.cmd[1:]
            if e.out is not None:
                print e.out

        except Error as e:
            logger.info('%s failed: %s', self.name, e)
            print
            print '{0}: {1}'.format(self.name, e)


        try:
            points = collections.defaultdict(collections.Counter)
            for group in self.groups:
                name = self.name if group.name is None else self.name + ':' + group.name
                points[group.category][name] += \
                    sum(1 for _ in group.get_tests(prog, data_dir)) * group.weight

            return [
                Score(category=category, group=group, given=0,
                    points=points[category][group])
                for category,catpoints in points.iteritems()
                for group in sorted(catpoints.keys())]

        except Error as e:
            logger.info('%s failed again: %s', self.name, e)
            print
            print '{0}: unable to determine number of tests'.format(self.name)
            return []



class MultiProject(Project):
    def __init__(self, *projects):
        self.projects = projects

    def get_scores(self, src_dir, data_dir, **kws):
        for p in self.projects:
            src  = os.path.join(src_dir, p.name)
            data = os.path.join(data_dir, p.name)

            for score in p.get_scores(src, data, **kws):
                yield score

logcfg = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'normal': { 'format': '%(asctime)s %(levelname)-8s %(message)s' },
    },
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            #'filename': 'autograder.log',
            'filename': os.path.join(sys.path[0], 'autograder.log'),
            'mode': 'a',
            'formatter': 'normal',
            'delay': True,
        },
    },
    'root': {
        'handlers': ['file'],
    },
}

def main(name, assignment, release=1,
        src_subdir='src',
        data_subdir='data',
        logcfg=logcfg):
    import argparse, logging.config, tempfile
    argp = argparse.ArgumentParser()
    argp.add_argument('-v', '--verbose', action='count', default=0,
        help='Print more output')
    argp.add_argument('-q', '--quiet', action='count', default=0,
        help='Print less output')
    argp.add_argument('-s', '--src', metavar='dir', default=src_subdir,
        help='Directory containing program files')
    argp.add_argument('-a', '--archive', metavar='tar',
        help='Archive containing program files (overrides -s)')
    argp.add_argument('-d', '--debug', action='store_true',
        help='Increase logging')
    argp.add_argument('program', nargs='*',
        help='Name of program to grade')

    args = argp.parse_args()

    if logcfg:
        logging.config.dictConfig(logcfg)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    logger.info('Starting autograder %s release %s. Library %s',
        name, release, __version__)

    # data directory is relative to grader
    data_dir = os.path.join(sys.path[0], data_subdir)

    logger.debug('Data directory: %r', data_dir)

    kws = {
        'verbosity': args.verbose - args.quiet,
        'requests': set(args.program),
    }

    try:
        print name, 'Auto-grader, Release', release

        if args.archive:
            assignment.grade_archive(args.archive, src_subdir, data_dir, **kws)
        else:
            src_dir = os.path.realpath(args.src)

            logger.debug('Source directory: %r', src_dir)

            if not os.path.isdir(src_dir):
                raise Error('invalid src directory: ' + repr(src_dir))

            assignment.grade(src_dir, data_dir, **kws)

    except Error as e:
        print "grader:", e
        exit(1)
    except Exception as e:
        logger.exception('Uncaught exception: %s', e)
        print "grader: internal error"
        exit(1)
