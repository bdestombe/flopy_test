# -*- coding: utf-8 -*-
"""
Created on Fri Sep 18 10:48:26 2015

@author: Bas des Tombe, bdestombe@gmail.com
"""

import numpy as np


class diver(object):

    def __init__(self, filepathname):
        import os
        import io
        from datetime import datetime
        from collections import OrderedDict as od

        self.path, self.fn = os.path.split(filepathname)
        fp = os.path.join(self.path, self.fn)
        _, self.ext = os.path.splitext(self.fn)

        if self.ext == '.MON' or self.ext == '.mon':
            with io.open(fp, 'r') as f:
                for _ in xrange(2):
                    next(f)

                self.metalog = od()
                for il, line in enumerate(f):
                    key, value = map(str.strip, line.encode('utf8').split(":", 1))
                    self.metalog[key.replace(' ', '_')] = value
                    if il is 5: break

                for _ in xrange(2):
                    next(f)

                for il, line in enumerate(f):
                    key, value = map(str.strip, line.encode('utf8').split("=", 1))
                    self.metalog[key.replace(' ', '_')] = value
                    if il is 8: break

                self.metalog['chname'] = []
                next(f)

                for ich in xrange(int(self.metalog['Number_of_channels'])):
                    for line in f:
                        chkey, chval = map(str.strip, line.encode('utf8').split("=", 1))
                        break
                    self.metalog['chname'].append(chval)
                    # dat[chval] = od()
                    chset = {}

                    for line in f:
                        if line.startswith('[') or not line.encode('utf8').strip(): break
                        key, value = map(str.strip, line.encode('utf8').split("=", 1))
                        chset[key] = value

                    chset['unit'] = chset['Reference level'].split(' ', 1)[-1].strip()
                    setattr(self, 'META_' + chval, chset)

                for _ in xrange(2):
                    next(f)

                for il, line in enumerate(f):
                    key, value = map(str.strip, line.encode('utf8').split("=", 1))
                    self.metalog[key.replace(' ', '_')] = value
                    if il is 6: break

                for line in f:
                    if line.startswith('[Data]'): break

                for line in f:
                    self.metalog['Number_of_measurements'] = int(line)
                    break

                f.seek(0)

                for il, line in enumerate(f):
                    if line.startswith('[Data]'):
                        self.skip_header = il + 2
                        break

                self.dtype = np.dtype({'names': ['date', 'time'] +
                                       self.metalog['chname'],
                                       'formats': ['O'] * 2 + [np.float] *
                                       int(self.metalog['Number_of_channels'])})

                f.close()

                for ich in xrange(int(self.metalog['Number_of_channels'])):
                    setattr(self, self.metalog['chname'][ich],
                            np.NaN)

        elif self.ext == '.NC' or self.ext == '.nc':
            raise ValueError('I dont understand the file extension')
        else:
            raise ValueError('I dont understand the file extension')


    def getnpdata(self):
        import os
        from datetime import datetime

        def convertDay(dstr):
            return datetime.date(datetime.strptime(dstr, '%Y/%m/%d'))

        def convertTime(dstr):
            return datetime.time(datetime.strptime(dstr, '%H:%M:%S.%f'))

        fp = os.path.join(self.path, self.fn)
        arr = np.genfromtxt(fp,
                            skip_header=self.skip_header, skip_footer=2,
                            dtype=self.dtype, converters={0: convertDay,
                                                          1: convertTime})

        dtcombineVec = np.vectorize(datetime.combine)
        self.date = dtcombineVec(arr['date'], arr['time'])

        for ich in xrange(int(self.metalog['Number_of_channels'])):
            setattr(self, self.metalog['chname'][ich],
                    arr[self.metalog['chname'][ich]])

    def getpddata(self):
        import os
        import numpy as np
        import pandas as pd
        from datetime import datetime

        def parse_datetime(dt_array):
            date_time = np.empty(dt_array.shape[0], dtype=object)
            for i, (d_str, t_str) in enumerate(dt_array):
                year, month, day = (int(d_str[:4]), int(d_str[5:7]),
                                    int(d_str[8:11]))
                hour, minute, sec = (int(t_str[:2]), int(t_str[3:5]),
                                     int(t_str[6:8]))
                date_time[i] = datetime(year, month, day, hour, minute, sec)
            return pd.to_datetime(date_time)

        fp = os.path.join(self.path, self.fn)
        tab = pd.read_csv(fp, names=['date', 'time'] + self.metalog['chname'],
                          delimiter=r"\s+", skiprows=self.skip_header,
                          error_bad_lines=False, warn_bad_lines=False,
                          nrows=self.metalog['Number_of_measurements'])
        tab['date_time'] = parse_datetime(tab.loc[:, ['date', 'time']].values)
        tab.drop(['date', 'time'], axis=1, inplace=True)
        tab.set_index('date_time')

        for ich in xrange(int(self.metalog['Number_of_channels'])):
            nam = self.metalog['chname'][ich]
            setattr(self, nam,
                    pd.DataFrame(data={nam: tab.loc[:, nam].values},
                                 index=tab.loc[:, 'date_time']))
        setattr(self, 'date_time',
                pd.DataFrame(data={'date_time': tab.loc[:, 'date_time'].values}))

    def writenc(self, fncpath):
        import netCDF4 as nc
        import numpy as np
        from timetools.timetools import py2mat

        globalsRef = {  # fromfield,tofield
                        'ID': '',
                        'name': self.metalog['Location'],
                        'tnocode': '',
                        'filtnr': '',
                        'xcoord': '',
                        'ycoord': '',
                        'upfiltlev': '',
                        'lowfiltlev': '',
                        'surflev': '',
                        'measpointlev': '',
                        'sedsumplength': '',
                        'datlog_serial': self.metalog['Serial_number'],
                        'datlog_depth': '',
                        'date': self.metalog['Start_date_/_time'],
                        'handmeas': '',
                        'vegtype': '',
                        'area': '',
                        'layercode': '',
                        'tranche': '',
                        'oldmetadata': str(self.metalog.items()),
                        'diver_files': ''
                       }
        # to netCDF
        ncf = nc.Dataset(fncpath, mode='w')

        for key, val in globalsRef.iteritems():
            setattr(ncf, key, val)

        # Time
        ncf.createDimension('time', self.metalog['Number_of_measurements'])
        t = ncf.createVariable('time', np.float64, ('time',))
        t.units = 'days'
        t.long_name = 'matlab ISO Gregorian calendar: days since midnight on Jan 1st, 0 AD'
        t[:] = py2mat(self.date_time.values)

        # Channel
        for ich in xrange(int(self.metalog['Number_of_channels'])):
            nam = self.metalog['chname'][ich]
            at = ncf.createVariable(nam, np.float64, ('time',))
            at.units = getattr(self, 'META_' + nam)['unit']
            at[:] = getattr(self, nam).loc[:, nam].values

        ncf.close()
