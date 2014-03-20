#!/usr/local/anaconda/bin/python
"""
Use to rebuild root cuts from matlab cut files.
Written for python 2.7. Currently must be run as production@cdmsmicro.
------------------------------------------------------------------------
This module is primarily designed to be run as a script (such as by a cron
job). To rebuild all cuts simply do: ('$' represents the bash prompt)

$ python make_cuts_classy.py

If you only want to rebuild some of the running modes those can be input
as command line arguments. For example to rebuild ba and cf cuts
the command would be:

$ python make_cuts_classy.py ba cf
"""
import os
import subprocess
import sys
import ROOT
import graphbuilder
import time
import memoize
import datetime
import shutil
try:
    import cPickle as pickle
except:
    import pickle


class rootcut(graphbuilder.depbuilder):

    """rootcut inherits from the depbulider class (which is found in the graphbuilder module).
    It is typically run as a script by calling its main method. From the python interpreter,
    that would look like:
        >>> from make_cuts_classy import rootcut
        >>> rc = rootcut() #rc is an rootcut object. Its default atributs can be modified at this time if desired
        >>> rc.main() #main method runs like a script"""

    def __init__(self):
        """The initialization method is called whenever a new rootcut object is created.
        It calls the 'cvs update' command (to get the newest matlab cut definitions)
        and sets some attributes which are fairly self explanatory"""

        self.force = False
        self.exclude = []
        # location of the root cuts (containing directories named for
        # data taking mode--like ba or bg_restricted etc.)
        self.root_cutdir = (
            '/tera2/data3/cdmsbatsProd/R133/dataReleases/Prodv5-3_June2013/merged/cuts/')
        # cut generation dir
        self.root_cutdir_gen = '/tera2/data3/cdmsbatsProd/processing/cuts'
        # location of checked out matlab cuts
        self.mat_cutdir = ('/tera2/data3/cdmsbatsProd/processing'
                           '/cdmstools/CAP/FCCS/cuts/Soudan/r133')
        # update cvs
        print "Updating cvs"
        self.ret = self.update_cvs(self.mat_cutdir)
        if self.ret == 0:
            print "cvs updated successfully"
        # run type list
        self.run_type_list = ['ba', 'cf', 'bg_restricted', 'bg_permitted']
        # make list of existing matlab cuts
        self.new_cut_list = [
            i.rstrip('m').rstrip('.')
            for i in (os.listdir(self.mat_cutdir) + os.listdir(
                self.mat_cutdir + '/Prodv5-3')) if i.split('.')[-1] == 'm']
        # make dict of cuts to update (a list for each running mode)
        self.update_dict = {}
        self.outdated_dict = {}
        self.old_version_dict = {}
        self.user_cuts = None
        self.ttime = '{:%Y-%m-%d-%H-%M-%S}'.format(
            datetime.datetime.fromtimestamp(time.time()))
        print "Initializing cut dependency graph..."
        graphbuilder.depbuilder.__init__(self)

#
#     Main method
#

    def main(self):
        """The main method. This is the method that is called that actually does everything.
        It builds a dictionary of old cut revision numbers (from the root cut files), and
        compares them to the new matlab cut revision numbers. It then builds a dictionary of
        cuts that are outdated (as well as any reverse dependencys for that cut) and hands
        the cuts off to matlab for generation. It then makes logs and preforms the hardlink."""

        # build ole root cut dictonary with keys that are the various running
        # mode and values that are lists of cuts
        self.root_cut_dict = self.build_cutlists(
            self.root_cutdir_gen,
            self.run_type_list)
        # make dict of cuts that need updating
        for h in self.root_cut_dict:
            # get new matlab cut list and check for new cuts
            cuts_to_update = []
            for i in list(set(self.new_cut_list) - set(self.root_cut_dict[h])):
                cuts_to_update.append(i)
            # make a list of all outdated cuts
            print "Building list of outdated cuts for {}".format(h)
            if self.user_cuts is None:
                self.outdated_dict[h] = self.make_cut_update_list(
                    self.mat_cutdir,
                    self.root_cut_dict[h],
                    h)
            else:
                self.outdated_dict[h] = self.user_cuts
            if self.outdated_dict[h] is None:
                self.outdated_dict[h] = []
            self.update_dict[h] = self.outdated_dict[h]
        # stop if there are no cuts to update
        if ([self.update_dict[i] for i in self.run_type_list] == [[] for i in self.run_type_list]):
            print "It looks like all the cuts are up to date"
            return 'It looks like all the cuts are up to date'
        else:
            print "The following cuts need to be updated:"
            for i in self.update_dict:
                print "{} cuts:".format(i)
                for j, k in self.update_dict[i]:
                    print "Cut {} will be updated to version {}".format(j, k)
            # kludge
            kludge = {
                i: {
                    j: k for j, k in self.update_dict[i]}
                for i in self.update_dict}
            # print kludge
            # hand cuts off to Matlab
            # try:
            print "Updating CAP"
            self.update_cvs(self.root_cutdir_gen + '/../cdmstools')
            print "Building FCCS tree"
            self.matlab_fork("makeCAPtree")
            mout = self.produce(kludge)

            return 'Matlab cut update script run and retuned ', mout

#
#       Helper methods
#
    def produce(self, kludge):
        """A wrapper method that contains the matlab interface. This is where the structure of my script's
        concurrency can be changed (what loops when and where.). It also calls the two rsync commands that get the cuts
        to the correct directories."""

        for types in self.run_type_list:
            print "Updating {} cuts:".format(types)
            arg1 = '/tera2/data3/cdmsbatsProd/R133/dataReleases/Prodv5-3_June2013/merged/byseries/{}'.format(
                types)
            arg2 = '/tera2/data3/cdmsbatsProd/processing/cuts/{}'.format(types)
            arg3 = kludge[types]
            print "Removing cuts no longer in CVS..."
            for old_cut in (cut for cut in os.listdir(self.root_cutdir_gen + "/{}".format(types)) if cut not in self.new_cut_list):
                print "Removing {}".format(old_cut)
                shutil.rmtree(
                    self.root_cutdir_gen +
                    '/{}/{}'.format(
                        types,
                        old_cut))

            def mapper(cvb):
                c, v, b = cvb

                print "===> {}".format(c)
                if b == 'before':
                    # if old cuts exist, delete them
                    direc = self.root_cutdir_gen + "/{}/{}".format(types, c)
                    if os.path.isdir(direc):
                        print "-> Removing old {} cuts...".format(c)
                        shutil.rmtree(direc)
                # print "-> Generating new {} cuts ...".format(c)
                else:
                    if (mout == 0) and (self.version_from_rootfile(c, self.root_cutdir_gen, types) == v):
                        mresult = '{} build: Success!'.format(c)
                    else:
                        mresult = '{} build: Failure!'.format(c)
                    print "-> {}".format(mresult)
            cvlist = []
            for c, v in arg3.iteritems():
                cvlist.append(c)
                cvlist.append(v)

            map(mapper, ((c, v, 'before') for c, v in arg3.iteritems()))
            print "Handing cuts off to MATLAB for production."
            arguements = [arg1, arg2] + cvlist
            mout = self.matlab_fork("makeROOTcut", *arguements)
            map(mapper, ((c, v, 'after') for c, v in arg3.iteritems()))
        self.make_logs(self.update_dict, self.root_cutdir_gen)
        self.hlinker(self.root_cutdir_gen, self.root_cutdir)
        self.linkupdate()
        self.rsyncer()

    def linkupdate(self):
        """Softlinks current directory to point to most recent cuts"""

        ndir = max([i for i in os.listdir(self.root_cutdir) if 'c' not in i])
        os.chdir(self.root_cutdir)
        if os.path.islink(self.root_cutdir + '/' + "current"):
            ret1 = subprocess.call(["rm", "current"])
        ret = subprocess.call(["ln", "-s", ndir, "current"])
        return ret, ret1

    def rsyncer(self):
        """Calls the rsync command to copy the data to nero"""

        print "rsync'ing data to nero..."

        ret1 = subprocess.call([
            "rsync",
            "-arH",
            "--delete",
            self.root_cutdir,
            "cdmsonly@nero.stanford.edu:/data/R133/dataReleases/Prodv5-3_June2013/merged/cuts/"
        ])

        print "rsync'ing data to galba..."
        ret2 = subprocess.call([
            "rsync",
            "-arH",
            "--delete",
            self.root_cutdir,
            "cdmsonly@galba.stanford.edu:/data/R133/dataReleases/Prodv5-3_June2013/merged/cuts/"
        ])
        if ret1 == 1 or ret2 ==1:
            raise Exception('rsync subprocess failure')
        return ret1, ret2

    def update_cvs(self, mat_cut_dir):
        """Calls the 'cvs update' command in a subprocess. If the subprocess
        reports an error, it logs the error. Otherwise it returns to the
        main method with a success."""

        os.chdir(mat_cut_dir)
        ret = subprocess.call(["cvs", "-Q", "update", "-d"])
        if ret == 1:
            print "Error updateing cvs. logging error in {}".format(self.root_cutdir_gen + '/.log/')
            ttime = '{:%Y-%m-%d-%H-%M-%S}'.format(
                datetime.datetime.fromtimestamp(time.time()))
            with open(
                self.root_cutdir + '/.log/' +
                    'CVS_ERROR' + ttime + '.log', 'w') as fyle:
                fyle.write('CVS has failed to update.'
                           ' Please manually debug.')
            raise Exception("cvs faild to update")
        return ret

    def build_cutlists(self, root_cutdir, run_type_list):
        """This method retruns a dictionary of all the currently generated
        root cuts. The keys are the running modes (like cf or ba) and the
        values are lists off all the cuts currently generated for that
        running mode."""

        return {i: [
            j for j in os.listdir(root_cutdir + '/' + i)
            if j in self.new_cut_list]
            for i in run_type_list}

    @staticmethod
    def check_eq(iterator):
        """A static method that takes an iterable object (like a list)
        and retruns True if every element of that list is the same. It
        is used in the version_from_rootfile method to make sure that every
        ROOT cut file for a specific cut is using the same cvs revision number."""

        try:
            iterator = iter(iterator)
            succeed = next(iterator)
            return all(succeed == element for element in iterator)
        except StopIteration:
            return True

    def version_from_rootfile(self, cut, root_cut_dir, run_type):
        """This method takes a particular cut (and running mode such as ba or cf),
        inspects the ROOT cut files and returns the cvs revision number for that
        particular cut. If for some reason the revision number is indeterminate (if say
        not all file have the same revision number), then the revision number will be
        set to '0.0' which will force them all to be regenerated."""
        
        try:
            rev_chain = ROOT.TChain()
            rev_chain.Add(
                root_cut_dir + '/' +
                run_type + '/' +
                cut + '/*.root/cutInfoDir/cvsInfo')
            cvs_rev_list = [i.cvsRevision.split('\x00')[0] for i in rev_chain]
            #fixes no directory crash
            if not os.path.isdir('{}/{}/{}'.format(root_cut_dir, run_type, cut)):
                return '0.0'
            #fixes empty directory crash
            elif os.listdir('{}/{}/{}'.format(root_cut_dir, run_type, cut)) == []:
                return '0.0'
            elif self.check_eq(cvs_rev_list):
                return cvs_rev_list[0]
            else:
                return '0.0'
        except:
            return 'error'

    @memoize.Memoize
    def version_from_cvs(self, cut, mat_cut_dir):
        """This method calls the 'cvs status' command for the given cut
        argument. It returns the revision number of the current checked out
        matlab cut. the memoization decorator just speeds things up by attaching
        a persistent dictionary to the method that remembers the return value for
        any arguments that have previously been called."""

        os.chdir(mat_cut_dir)
        if "v53" in cut:
            prefix = "Prodv5-3/"
        else:
            prefix = ""
        a = subprocess.Popen(
            ["cvs", "status", prefix + cut + '.m'], stdout=subprocess.PIPE)
        b, c = a.communicate()
        return (b.split("Working revision:\t")[1].split("\n")[0])

    def matlab_fork(self, func, *args):
        """This calls matlab in a subprocess. It dumps the standard output
        to /dev/null but should return StandardError in a usable fashion. Needs more
        error recovery."""

        if args:
            caller = "{}({});exit".format(
                func,
                ",".join(["\'{}\'".format(i) for i in args]))
        else:
            caller = "{};exit".format(func)

        with open(self.root_cutdir_gen + '/.log/' + self.ttime + 'MatlabDump.log', 'a') as fp:
            ret = subprocess.call(
                ["/usr/local/MATLAB/R2012b/bin/matlab",
                    "-nodisplay", "-nosplash", "-r", caller],
                stdout=fp)
            if ret == 1:
                raise Exception('MATLAB subprocess failure')
        return ret

    def make_cut_update_list(self, mat_cutdir, root_cut_list, run_type):
        """This is the largest helper method. It is called once per run type. It
        takes a list of all the old root cuts and returns a list of the cuts that are
        outdated, do not exist, or depend on such a cut."""

        # get new matlab cut list and check for new cuts
        if root_cut_list == None:
            root_cut_list = []
        cuts_to_update = []
        cut_rev_dict = {}
        old_version_inner = {}
        missing_cuts = [j for j in self.new_cut_list if j not in root_cut_list + self.exclude]
        # make a list of all outdated cuts
        for i in self.new_cut_list:
            if self.domain[i] == ['all'] or run_type in self.domain[i]:
                # find revision number of newly updated matlab cuts
                rev_num_new = self.version_from_cvs(
                    i, self.mat_cutdir)
                cut_rev_dict[i] = rev_num_new
                if i in missing_cuts:
                    cuts_to_update.append((i, rev_num_new))
                    old_version_inner[i] = "*newly created cut*"
                else:
                    # find revision number of old root cuts
                    rev_num_old = self.version_from_rootfile(
                        i,
                        self.root_cutdir_gen,
                        run_type)
                    old_version_inner[i] = rev_num_old
                    # print rev_num_new, rev_num_old, (rev_num_new != rev_num_old)
                    # append outdated cut to list
                    if i not in self.exclude:
                        if (rev_num_new != rev_num_old) or self.force:
                            cuts_to_update.append((i, rev_num_new))
        # deal with reverse deps
        for (i, j) in cuts_to_update:
            for dep in self.parents(i):
                t = (dep, cut_rev_dict[dep])
                if t not in cuts_to_update:
                    if dep not in self.exclude:
                        cuts_to_update.append(t)
            self.old_version_dict[run_type] = old_version_inner
        return cuts_to_update

    def make_logs(self, update_dict, root_cutdir):
        """This simply makes logs."""

        with open(
            root_cutdir + "/.log/pickles/" +
                self.ttime + '.p', 'w') as fyle:
            pickle.dump(update_dict, fyle)
        with open(
            root_cutdir + '/.log/' +
                self.ttime + '.log', 'w') as fyle:
            for h in update_dict:
                fyle.write(
                    '=========================\n'
                    '\n {} cuts updated\n'
                    '=========================\n'.format(h))
                for c in update_dict[h]:
                    try:
                        name, num = c
                    except:
                        name, num = c, "*cant retrive CVSinfo*"
                    try:
                        old = self.old_version_dict[h][name]
                    except:
                        old = 'N/A'
                    if old == num:
                        fyle.write(
                            '{} updated from revision {}'
                            ' to revision {}'
                            ' **rebuilt due to dependency**\n'.format(
                                name, old, num))
                    else:
                        fyle.write(
                            '{} updated from revision {}'
                            ' to revision {}\n'.format(name, old, num))

    def hlinker(self, cutgendir, rootcutdir):
        """Calls Ben's hardlink script in a subprocess"""

        print "Calling Ben's snapshot script in a subprocess"
        ret = subprocess.call(
            ["sh", self.root_cutdir_gen + "/../src/take_cuts_snapshot.sh", cutgendir,
             rootcutdir])
        if ret == 1:
            print "Error with Ben's snapshot and hardlink bash script"

        return ret

# Module to script trick. If the file is run from the command line
# as a script, then the following section of code will be executed.
# Extra command line arguments will be treated as running types. The
# default is all running types.
if __name__ == "__main__":
    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument(
        "mode",
        metavar="MODE",
        nargs='*',
        help="List of running modes (bg_permitted cf ...) to be rebuilt.")
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        dest="force",
        default=False,
        help="Force all cuts to be rebuild")
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        dest="batch",
        default=False,
        help="Directs script standard output to a log file")
    parser.add_argument(
        "-c",
        "--cuts",
        help="List of cuts to be rebuilt. Will only build these cuts.",
        nargs='*')
    parser.add_argument(
        "-x",
        "--exclude",
        help="List of cuts to be excluded. Overrides the -f option.",
        nargs="*")
    args = parser.parse_args()
    t1 = time.time()
    geterdone = rootcut()
    if args.batch:
        sys.stdout = open(geterdone.root_cutdir_gen + '/.log/' + geterdone.ttime + 'PythonDump.log', 'a')
    if args.mode is not None:
        geterdone.run_type_list = args.mode
    geterdone.force = args.force
    geterdone.exclude = args.exclude
    if args.cuts is not None:
        kludge = [(c, geterdone.version_from_cvs(c, geterdone.mat_cutdir))
                  for c in args.cuts]
        geterdone.user_cuts = kludge
    try:
        goterdid = geterdone.main()
        t2 = time.time()
        print goterdid, t2 - t1
    finally:
        if args.batch:
            sys.stdout.close()

