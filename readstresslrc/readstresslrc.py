# -*- coding: utf-8 -*-
"""
Created on Thu Sep 10 12:00:12 2015

@author: Bas des Tombe, bdestombe@gmail.com

LRC == kij
"""
import numpy as np


class readstresslrc(object):
    def __init__(self, pack):
        import flopy

        assert isinstance(pack.parent, flopy.modflow.mf.Modflow),\
            "%r is not a modflow package" % pack

        nper = len(pack.stress_period_data.data)

        reclen = [len(pack.stress_period_data.data[i]) for i in pack.stress_period_data.data]

        ifrom = np.cumsum([0] + reclen[:-1])
        ito = np.cumsum(reclen)

        if np.sum(reclen) != (len(pack.stress_period_data.data[0]) * nper):
            print "Not every bcn is defined for each stress period"

        self.arr = np.recarray(np.sum(reclen),
                               pack.stress_period_data.data[0].dtype)
        self.arr = np.lib.recfunctions.append_fields(self.arr, 'it',
                                                 np.ones(5110, dtype=np.int),
                                                 usemask=False, asrecarray=True)

        for i in xrange(nper):
            self.arr[ifrom[i]:ito[i]] = pack.stress_period_data.data[i]
            self.arr[ifrom[i]:ito[i]]['it'] = i

        a = np.vstack((self.arr.k, self.arr.i, self.arr.j)).T
        ind = np.lexsort(a.T)
        kij = a[ind[np.concatenate(([True], np.any(a[ind[1:]] != a[ind[:-1]],
                                    axis=1)))]]

        self.k = kij[:, 0]
        self.i = kij[:, 1]
        self.j = kij[:, 2]

        self.len = kij.shape[0]

    def getkijkey(self, k, i, j, key):
        mask = np.logical_and(self.arr.k == k, self.arr.i == i,
                              self.arr.j == j)
        return (self.arr[mask]['it'], self.arr[mask][key])
