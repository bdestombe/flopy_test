# flopy_test
Flopy helper scripts. Work in progress.

If a script is fully working, it will be moved to another repository

## Install
To install the flopy_test suite; all the tools:
pip install https://github.com/bdestombe/flopy_test/zipball/master/

## Scriptgenerator usage
from scriptgenerator.scriptgenerator import flopyinit

c=['ml', 'dis', 'bas6', 'lpf', 'wel', 'riv', 'oc', 'pcg', 'mt', 'btn',  'adv', 'dsp', 'ssm', 'rct', 'gcg', 'sw', 'vdf', 'vsc']
ws = 'C:\Users\Bas\Google Drive\CiTG MSc\CIE5060 - Thesis\scripts\\'
filename = 'test.py'
nampath = 'C:\\Users\\Bas\\Google Drive\\CiTG MSc\\Artesia\\mflab\\run\\swt_v4.NAM'

flopyinit(c=c, ws=ws, filename=filename, comment=False, unit=False, load=nampath, verbose=False)
