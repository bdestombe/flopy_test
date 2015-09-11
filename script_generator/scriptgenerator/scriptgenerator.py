# -*- coding: utf-8 -*-
"""
Created on Wed Sep 02 11:08:13 2015

@author: Bas des Tombe, bdestombe@gmail.com

Creates a model script that uses flopy, for a quick transition from any
arbitrary modeling environment to flopy.

The values for the parameters are either loaded from a dictionary that contains
flopy package instances or values can be loaded directly from a nam-file. When
this packages is in c, but no values could be loaded, the default values are
being used.

When comment is set to True, one or two lines are provided for each parameter.
When unit is set to True, the possible dtypes of the parameter are printed as well.

Both comments and units currently only work for the modflow packages and some
mt3d packages

Remember that it matters in which order the packages are entered in c. For
that reason, packages need to be read from a list. Dict doesn't guarantee the
order.

Some possible entries for c:
'ml', 'bas6', 'nwt', 'pks', 'riv', 'sw', 'uzf', 'pval', 'sor', 'btn', 'swi2',
'adv', 'sip', 'chd', 'zone', 'rct', 'gmg', 'dsp', 'wel', 'rch', 'tob', 'pcg',
'phc', 'vdf', 'pcgn', 'upw', 'hfb6', 'mult', 'ssm', 'gcg', 'ml', 'oc', 'mt',
'vsc', 'ghb', 'drn', 'lpf', 'evt', 'dis']

# Todo:
- check paths in mac environment
- As soon as flopy supports loading of mt3d packages, include that as well.
- Find a more efficient way to process stress_period_data

BdT: 150902, 150906-150908
"""
import os
import flopy
import inspect
import numpy as np


class flopyinit():
    def __init__(self, c=['ml', 'bas6', 'dis'], ws = r'C:\\Users\\Bas\\Google Drive\\CiTG MSc\\CIE5060 - Thesis\\scripts\\', filename='test.py', comment=True, unit=True, load={}, verbose=False):
        '''
        Parameters
        ----------
        c : package list of type list
            The package list will be printed in the order entered in c. Upper
            or lower case can be used interchangeably.
        ws : Workspace
            Path where the output script + saved values (the large ones) are
            being saved
        filename : Filename of the to-be-constructed script
        comment : Desciption flag
            Flag whether description of parameters need to be printed. Read
            directly from the docs.
        unit : Dtype flag
            Flag whether the possible dtypes for the parameter need to be
            printed. Read directly from the docs.
        load : Load old model
            load can be a path string to a NAM file. It reads the namfile
                and uses the flopy load routine to load the individual packages
                Flopy currently only supports the loading of flopy pakcages.
            load can also be a dictionary of packages. The keywords should be
                as in c.
        '''

        self.ws = ws
        self.filename = filename
        fn = ws + filename
        self.comment = comment
        self.unit = unit
        self.verbose = verbose

        for i, string in enumerate(c):
            c[i] = string.lower()

#        if 'load' in kwargs:
        if isinstance(load, dict):
            self.load = {}
            for i, p in enumerate(load):
                self.load[p.lower()] = load[p]
        elif isinstance(load, str):
            print 'load Nam..'
            dic = self.loadvar(load)
            self.load = {}
            for i, p in enumerate(dic):
                self.load[p.lower()] = dic[p]
            print 'loaded the following files: ', dic.keys()
        else:
            raise Exception('I dont understand the entered load keyword')


        # Construct complete package list p, that includes the package constructor
        p = flopy.modflow.Modflow().mfnam_packages
        p['ml'] = flopy.modflow.Modflow
        p.update(self.namfilesmt3d())
        p.update(self.namfilessw())

        # Write introduction
        header = 'Written by flopy init script'
        f = open(fn, 'w')
        f.write('# ' + header + '\n\n')
        f.write('import numpy as np\n')
        f.write('import os\n')
        f.write('import flopy\n\n')
        f.write('# Workspace where parameters are saved\n')
        f.write("wsPar = '" + self.ws + "\\'\n\n")
        f.write('# In[Configure packages]\n')

        for ipack, packstr in enumerate(c):
            par = -1
            success, par = self.getdoc(p[packstr])
            if not success and self.verbose:
                print 'Unable to read documentation for package: ', packstr
            self.writepars(f, packstr, p, par)
            self.writepackage(f, packstr, p)

        self.writewrite(f, c, p)
        self.writerunfiles(f, c, p)

        f.close()

    def tostr(self, tbstr, packstr, arg):
        '''
        From variable to string.

        Specific variables require specific treatment. If arrays do not contain
        a unique value the entire array is written to file.

        The package string and the parameter name are included to construct a
        filename. The variables can be read directly using np.load('.npy').

        Todo:
        - efficient mflist implementation

        '''
        import numpy as np
        import flopy

        if isinstance(tbstr, str):
            return "'" + tbstr + "'"

        elif isinstance(tbstr, np.ndarray):
            if len(np.unique(tbstr)) != 1:
                path = os.path.join(self.ws, packstr + '_' + arg)
                np.save(path, tbstr)
                string = "np.load(os.path.join(wsPar, '" + packstr + '_' + arg + ".npy'))"
            else:
                string = str(np.unique(tbstr))
            return string

        elif isinstance(tbstr, flopy.utils.util_array.util_3d) or isinstance(tbstr, flopy.utils.util_array.util_2d):
            if len(np.unique(tbstr.array)) != 1:
                np.save(self.ws + packstr + '_' + arg, tbstr.array)
                string = "np.load(os.path.join(wsPar, '" + packstr + '_' + arg + ".npy'))"
            else:
                string = str(np.unique(tbstr.array)[0])
            return string

        elif isinstance(tbstr, flopy.utils.util_list.mflist):
            np.save(self.ws + packstr + '_' + arg, tbstr.data)
            string = "np.load(os.path.join(wsPar, '" + packstr + '_' + arg + ".npy')).all()"
            return string

        elif isinstance(tbstr, dict):
            if len(tbstr.keys()) > 20:
                np.save(self.ws + packstr + '_' + arg, tbstr)
                string = "np.load(os.path.join(wsPar, '" + packstr + '_' + arg + ".npy')).all()"
                return string
            else:
                return str(tbstr)

        elif isinstance(tbstr, np.dtype):
            return 'np.dtype(' + str(tbstr) + ')'

        else:
            return str(tbstr)

    def getdoc(self, func):
        '''
        Interpretates the documentation and reshapes it into something useful.

        Creates a dictionary with an entry for each package. Each package entry
        contains a dictionary for each parameter. Each parameter entry contains
        a dictionary with 'description' entry and a 'unit' entry.
        The description entry contains a couple of lines describing the
        parameter
        The unit entry describes the possible dtypes
        '''
        doc = inspect.getdoc(func)
        if doc is None:
            doc = ''

        dl = doc.splitlines()
        dl = [x for x in dl if x != '.']

        for il, line in enumerate(iter(dl)):
            if line == 'Parameters':
                lPar = il
            if line == 'Attributes':
                lAtt = il
                break

        if 'lPar' in locals() and 'lAtt' in locals():
            parBool = []
            for il, line in enumerate(iter(dl[lPar+2:lAtt-2])):
                parBool.append(line[:2] != '  ')

            par = {}
            for il, line in enumerate(iter(dl[lPar+2:lAtt-2])):
                if parBool[il]:
                    try:
                        varname = line.split(None, 1)[0]
                        par[varname] = {}
                        par[varname]['unit'] = line.split(' : ')[1]
                        par[varname]['desc'] = ''

                        for iil, iline in enumerate(iter(dl[lPar+2:lAtt-2])):
                            if np.cumsum(parBool)[il] == np.cumsum(parBool)[iil] and not parBool[iil]:
                                par[line.split(None,1)[0]]['desc'] += iline[4:] + ' '
                    except:
                        continue
            return (True, par)
        else:
            return (False, -1)

    def writepackage(self, fh, packstr, p):
        '''
        Writes the line of code that construct the package. dis = mf.dis(....)
        '''
        argsin, varargs, key, defaults = inspect.getargspec(p[packstr].__init__)
        fh.write('\n# Write package: ' + packstr + '\n')
        fh.write(packstr + ' = ' + str(p[packstr].__module__) + '.' + str(p[packstr].__name__))
        fh.write('(')

        for iarg, arg in enumerate(argsin):
            if arg != 'self' and arg != 'model':
                fh.write(arg+'='+arg)
                if iarg != len(argsin)-1:
                    fh.write(', ')
            elif arg == 'model':
                if p[packstr].__module__[:9] == 'flopy.mod':
                    arg2 = 'ml'
                elif p[packstr].__module__[:9] == 'flopy.mt3':
                    arg2 = 'mt'
                elif p[packstr].__module__[:9] == 'flopy.sea':
                    arg2 = 'sw'

                fh.write(arg+'='+arg2)
                if iarg != len(argsin)-1:
                    fh.write(', ')

        fh.write(')\n\n')

    def writepars(self, fh, packstr, p, par):
        '''
        Writes the 'parameter = value' to the script. If values were loaded
        from modflow input files, those values are used. Otherwise the default
        values.
        If comment is set to True, a description is printed.
        If unit is set to True, the possible dtypes are printed.
        '''

        # Write the introduction
        fh.write('\n' + '#'*78 + '\n')
        fh.write('# ' + packstr + '\n')

        # Examine package constructor
        args, varargs, key, defaults = inspect.getargspec(p[packstr].__init__)
        nrkwargs = len(defaults)

        # Non-keyword arguments
        for iarg, arg in enumerate(args[:-nrkwargs]):
            '''
            Write away the args (garanteed to be first arguments). In practise
            only the model parameter.
            '''
            if arg == 'model':
                '''
                The model parameter can have a different value for different
                packages.
                '''
                if p[packstr].__module__[:9] == 'flopy.mod':
                    arg2 = 'ml'
                elif p[packstr].__module__[:9] == 'flopy.mt3':
                    arg2 = 'mt'
                elif p[packstr].__module__[:9] == 'flopy.sea':
                    arg2 = 'sw'
            else:
                arg2 = arg
            if isinstance(par, dict) and arg != 'self':
                if arg in par:
                    if self.comment:
                        fh.write('# ' + par[arg]['desc'] + '\n')

                    fh.write(arg + ' = ' + arg2)

                    if self.unit:
                        fh.write('  # ' +  par[arg]['unit'] + '\n')
                    else:
                        fh.write('\n')

                else:
                    if self.verbose:
                        print 'no descr of:', packstr, ':', arg
                    fh.write(arg + ' = ' + arg2 + '\n')

        # Keyword arguments (kwargs)
        for iarg, arg in enumerate(args[-nrkwargs:]):
            '''
            Write away the keyword args (garanteed to be last arguments). In
            practise every parameter except model
            '''
            if arg == 'model':
                '''
                The model parameter can have a different value for different
                packages.
                '''
                if p[packstr].__module__[:9] == 'flopy.mod':
                    arg2 = 'ml'
                elif p[packstr].__module__[:9] == 'flopy.mt3':
                    arg2 = 'mt'
                elif p[packstr].__module__[:9] == 'flopy.sea':
                    arg2 = 'sw'
            else:
                arg2 = arg

            if arg != 'self':
                if isinstance(par, dict) and arg != 'self':
                    if self.comment and arg in par:
                        fh.write('# ' + par[arg]['desc'] + '\n')

                    if packstr in self.load:
                        '''
                        If the requested package is in the loaded dict,
                        and that package contains the keyword. If the requested
                        package is in the dict, but the parameter isn't, use
                        the default value.
                        '''
                        value = self.tostr(getattr(self.load[packstr], arg,
                                                   defaults[iarg]), packstr, arg)
                        fh.write(arg + ' = ' + value)
                    else:
                        '''
                        Else use the default value
                        '''
                        fh.write(arg + ' = ' +  self.tostr(defaults[iarg],
                                                           packstr, arg))

                    if self.unit and arg in par:
                        fh.write('  # ' +  par[arg]['unit'] + '\n')
                    else:
                        fh.write('\n')

                else:
                    if self.verbose:
                        print 'no descr of:', packstr, ':', arg
                    fh.write(arg + ' = ' +  self.tostr(defaults[iarg], packstr,
                                                       arg) + '\n')

    def writewrite(self, fn, c, p):
        '''
        Writes the 'write' constructors to the script.
        '''
        fn.write('\n# In[Write input files]\n')
        if 'ml' in c:
            fn.write('ml.write_input()\n')
        if 'mt' in c:
            fn.write('mt.write_input()\n')
        if 'sw' in c:
            fn.write('sw.write_input()\n')

    def writerunfiles(self, fn, c, p):
        '''
        Writes the run command to the script. The order matters.
        '''
        fn.write('\n# In[Run model]\n')
        if 'sw' in c:
            stri = 'sw.run_model(silent=False)'
        elif 'mt' in c:
            stri = 'mt.run_model(silent=False)'
        elif 'ml' in c:
            stri = 'ml.run_model(silent=False)'
        else:
            stri = 'model.run_model(silent=False)'

        fn.write('success, buff = ' + stri + '\n')

    def namfilesmt3d(self):
        '''
        The package list for MT3D
        '''
        out = {
                'mt': flopy.mt3d.mt.Mt3dms,
                'adv': flopy.mt3d.mtadv.Mt3dAdv,
                'btn': flopy.mt3d.mtbtn.Mt3dBtn,
                'dsp': flopy.mt3d.mtdsp.Mt3dDsp,
                'gcg': flopy.mt3d.mtgcg.Mt3dGcg,
                'phc': flopy.mt3d.mtphc.Mt3dPhc,
                'rct': flopy.mt3d.mtrct.Mt3dRct,
                'ssm': flopy.mt3d.mtssm.Mt3dSsm,
                'tob': flopy.mt3d.mttob.Mt3dTob
                }
        return out

    def namfilessw(self):
        '''
        The package list for SEAWAT
        '''
        out = {
                'sw': flopy.seawat.swt.Seawat,
                'vdf': flopy.seawat.swtvdf.SeawatVdf,
                'vsc': flopy.seawat.swtvsc.SeawatVsc
                }
        return out

    def loadvar(self, nampath):
        '''
        Creates a dictionary with package instances. Nampath is the path plus
        filename of the NAM file. configured to use the modflow load machine.
        When the loading of MT3D and SEAWAT packages is supported by flopy,
        This function need to be adapted accordingly
        '''
        import os
        path, fn = os.path.split(nampath)

        m = flopy.modflow.Modflow.load(os.path.join(path, fn),
                                       version='mf2005', model_ws=path,
                                       verbose=self.verbose)
        mflst = m.get_package_list()

        dic = {}

        for ip, p in enumerate(mflst):
            dic[p] = m.get_package(p)

        return dic
