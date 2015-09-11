# -*- coding: utf-8 -*-
"""
Created on Thu Sep 03 13:24:14 2015

@author: Bas des Tombe, bdestombe@gmail.com
"""


def delnam(fn='', extraext=['MAS', 'CNF', 'CBC', 'DDN', 'HDS', 'p00', 'OC', 'UCN', 'VDF', 'VSC', 'nam_swt', 'nam_mt3dms', 'nam', 'bas', 'rct']):
    import os
    dic = namdict(fn=fn)
    if dic is not False:
        extraext = extraext + dic.keys()

        extraext = [x.lower() for x in extraext] + [x.upper() for x in extraext]
        path = os.path.dirname(os.path.abspath(fn))

    #    for i, key in enumerate(dic):
    #        os.remove(os.path.join(path, dic[key]))

        for root, dirs, files in os.walk(path):
            for currentFile in files:
                if any(currentFile.endswith(ext) for ext in extraext):
                    os.remove(os.path.join(root, currentFile))
    else:
        print 'Not deleted any MF files as part of the cleanup'


def namdict(fn=''):
    import os.path
    if os.path.isfile(fn):
        f = open(fn)
        txt = f.readlines()
        f.close()
        txt2 = [x for x in txt if x[0] != '#']
        txt2 = [x.strip('\n') for x in txt2]
        txt2 = [x.replace('\t', ' ') for x in txt2]
        txt3 = [x.split() for x in txt2]

        out = {}
        for i, val in enumerate(txt3):
            out[val[0]] = val[2]
        return out
    else:
        return False


def running():
    import psutil

    exe = ['mf2005.exe', 'swt_v4.exe']

    for p in psutil.process_iter():
        if p.name() in exe:
            print p.name(), ' is still running'
            print 'Has the following files open: ', p.open_files()
            print 'Now closing ', p.name(), '...'
            p.terminate()
