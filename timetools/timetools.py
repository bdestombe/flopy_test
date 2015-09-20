# -*- coding: utf-8 -*-
"""
Created on Thu Aug 20 13:58:18 2015

@author: Bas des Tombe, bdestombe@gmail.com

Python np timestamp to MATLAB time stamp


"""
import numpy as np
from datetime import datetime as dt
from datetime import timedelta


def py2mat(tpy):
    '''
    expects a ndarray with dtype datetime objects or datetime64
    returns ndarray with matlab timestamps
    '''

    a = tpy.astype('datetime64[s]').astype('d')

    secs_per_day = 24 * 60 * 60    # hours * mins * secs

    dateconv = np.vectorize(dt.fromordinal)
    dateconv2 = np.vectorize(dt.toordinal)
    stamptodtobj = np.vectorize(dt.fromtimestamp)
    np_tot_sec = np.vectorize(timedelta.total_seconds)

    days = dateconv2(stamptodtobj(a) + timedelta(days=366)).astype(np.float)
    ddays = np_tot_sec(stamptodtobj(a) - \
            dateconv(dateconv2(stamptodtobj(a)))) / secs_per_day

    return days + ddays


def mat2py(tmat):
    '''
    expects ndarray with matlab timestamps
    returns ndarray with dtype datetime-object
    '''
    dateconv = np.vectorize(dt.fromordinal)
    tdelconv = np.vectorize(timedelta)
    return dateconv(tmat.astype(np.int)) + tdelconv(days=tmat%1) - timedelta(days=366)
