python cut tera
===============

This is a script (and supporting files) to automatically generate ROOT cuts from MATLAB cuts.
It is run as production@cdmstera2 where it is located in $PROC/src. This should be in production's
$PATH so the script can be called from anywhere.

Example script usage
-------------

To rebuild all outdated barium cuts (and all cuts that depend on such a cuts):

```shell
make_cuts_classy.py ba
```

To force a rebuild of all californium and all low background:

```shell
make_cuts_classy.py bg_permitted cf -f
```

To just build cGood events and cRandom for californium and barium (no dependencies):

```shell
make_cuts_classy.py cf ba -c cGoodEv_133 cRandom_133
```

All of the script functionality can also be used from python. The above example is:

```python
from make_cuts_classy import rootcut
rc = rootcut() #rc builds a dependency graph of most recent cuts
rc.run_type_list = ['cf', 'ba'] #set the data types to build
rc.user_cuts = ['cGoodEv_133', 'cRandom_133'] #build only these cuts
rc.main() #build the cuts!
```

As usual, to display all options use the -h flag

```shell
$ make_cuts_classy.py -h
usage: make_cuts_classy.py [-h] [-f] [-b] [-c [CUTS [CUTS ...]]]
                           [MODE [MODE ...]]

positional arguments:
  MODE                  List of running modes (bg_permitted cf ...) to be
                        rebuilt.

optional arguments:
  -h, --help            show this help message and exit
  -f, --force           Force all cuts to be rebuild
  -b, --batch           Directs script standard output to a log file
  -c [CUTS [CUTS ...]], --cuts [CUTS [CUTS ...]]
                        List of cuts to be rebuilt. Will only build these
                        cuts.
```
Automatic dispatch
------------------

To have the cuts be continuously built you can use my dispatch script that is included in $PROC/src. A simple:

```shell
cd $PROC/src
python dispatch.py
```

Will schedule the cuts to be rebuilt every six hours. If they are currently in the process of building, the script
will wait another six hours before trying again. This should be run using vnc or screen (or similar) so it can stay
running at all times.
