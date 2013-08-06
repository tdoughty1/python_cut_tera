python cut tera
===============

This is a script (and supporting files) to automatically generate ROOT cuts from MATLAB cuts.
It is run as production@cdmstera2 where it is located in $PROC/src.

Example usage
-------------

To rebuild all outdated barium cuts (and all cuts that depend on such a cuts):
'''shell
python make_cuts_classy.py ba
'''

To force a rebuild of all californium and all low background:
'''shell
python make_cuts_classy.py bg_permitted cf -f
'''

To just build cGood events and cRandom for californium and barium (no dependencies):
'''shell
python make_cuts_classy.py cf ba -c cGoodEv_133 cRandom_133
'''

All of the script functionality can also be used from python. The above example is:
'''python
from make_cuts_classy import rootcut
rc = rootcut() #rc builds a dependency graph of most recent cuts
rc.run_type_list = ['cf', 'ba'] #set the data types to build
rc.user_cuts = ['cGoodEv_133', 'cRandom_133'] #build only these cuts
rc.main() #build the cuts!
'''

