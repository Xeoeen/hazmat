"""
Customisable progressbar decorator for iterators.
Includes a default (x)range iterator printing to stderr.

Usage:
  >>> from tqdm import trange[, tqdm]
  >>> for i in trange(10): #same as: for i in tqdm(xrange(10))
  ...     ...
"""
from __future__ import absolute_import
# integer division / : float, // : int
from __future__ import division
# native libraries
import sys
from platform import system as _curos
from numbers import Number
from threading import Thread
from time import time
from time import sleep
import os
import subprocess

__author__ = {"github.com/": ["noamraph", "obiwanus", "kmike", "hadim",
                              "casperdcl", "lrq3000"]}
__all__ = ['tqdm',
           'TqdmTypeError', 'TqdmKeyError', 'TqdmDeprecationWarning']


CUR_OS = _curos()
IS_WIN = CUR_OS in ['Windows', 'cli']
IS_NIX = (not IS_WIN) and any(
    CUR_OS.startswith(i) for i in
    ['CYGWIN', 'MSYS', 'Linux', 'Darwin', 'SunOS', 'FreeBSD', 'NetBSD'])


# Py2/3 compat. Empty conditional to avoid coverage
if True:  # pragma: no cover
    try:
        _range = xrange
    except NameError:
        _range = range

    try:
        _unich = unichr
    except NameError:
        _unich = chr

    try:
        _unicode = unicode
    except NameError:
        _unicode = str

    try:
        if IS_WIN:
            import colorama
            colorama.init()
        else:
            colorama = None
    except ImportError:
        colorama = None

    try:
        from weakref import WeakSet
    except ImportError:
        WeakSet = set

    try:
        _basestring = basestring
    except NameError:
        _basestring = str

    try:  # py>=2.7,>=3.1
        from collections import OrderedDict as _OrderedDict
    except ImportError:
        try:  # older Python versions with backported ordereddict lib
            from ordereddict import OrderedDict as _OrderedDict
        except ImportError:  # older Python versions without ordereddict lib
            # Py2.6,3.0 compat, from PEP 372
            from collections import MutableMapping

            class _OrderedDict(dict, MutableMapping):
                # Methods with direct access to underlying attributes
                def __init__(self, *args, **kwds):
                    if len(args) > 1:
                        raise TypeError('expected at 1 argument, got %d',
                                        len(args))
                    if not hasattr(self, '_keys'):
                        self._keys = []
                    self.update(*args, **kwds)

                def clear(self):
                    del self._keys[:]
                    dict.clear(self)

                def __setitem__(self, key, value):
                    if key not in self:
                        self._keys.append(key)
                    dict.__setitem__(self, key, value)

                def __delitem__(self, key):
                    dict.__delitem__(self, key)
                    self._keys.remove(key)

                def __iter__(self):
                    return iter(self._keys)

                def __reversed__(self):
                    return reversed(self._keys)

                def popitem(self):
                    if not self:
                        raise KeyError
                    key = self._keys.pop()
                    value = dict.pop(self, key)
                    return key, value

                def __reduce__(self):
                    items = [[k, self[k]] for k in self]
                    inst_dict = vars(self).copy()
                    inst_dict.pop('_keys', None)
                    return (self.__class__, (items,), inst_dict)

                # Methods with indirect access via the above methods
                setdefault = MutableMapping.setdefault
                update = MutableMapping.update
                pop = MutableMapping.pop
                keys = MutableMapping.keys
                values = MutableMapping.values
                items = MutableMapping.items

                def __repr__(self):
                    pairs = ', '.join(map('%r: %r'.__mod__, self.items()))
                    return '%s({%s})' % (self.__class__.__name__, pairs)

                def copy(self):
                    return self.__class__(self)

                @classmethod
                def fromkeys(cls, iterable, value=None):
                    d = cls()
                    for key in iterable:
                        d[key] = value
                    return d


def _is_utf(encoding):
    return encoding.lower().startswith('utf-') or ('U8' == encoding)


def _supports_unicode(file):
    return _is_utf(file.encoding) if (
        getattr(file, 'encoding', None) or
        # FakeStreams from things like bpython-curses can lie
        getattr(file, 'interface', None)) else False  # pragma: no cover


def _environ_cols_wrapper():  # pragma: no cover
    """
    Return a function which gets width and height of console
    (linux,osx,windows,cygwin).
    """
    _environ_cols = None
    if IS_WIN:
        _environ_cols = _environ_cols_windows
        if _environ_cols is None:
            _environ_cols = _environ_cols_tput
    if IS_NIX:
        _environ_cols = _environ_cols_linux
    return _environ_cols


def _environ_cols_windows(fp):  # pragma: no cover
    try:
        from ctypes import windll, create_string_buffer
        import struct
        from sys import stdin, stdout

        io_handle = None
        if fp == stdin:
            io_handle = -10
        elif fp == stdout:
            io_handle = -11
        else:  # assume stderr
            io_handle = -12

        h = windll.kernel32.GetStdHandle(io_handle)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (_bufx, _bufy, _curx, _cury, _wattr, left, _top, right, _bottom,
             _maxx, _maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            # nlines = bottom - top + 1
            return right - left  # +1
    except:
        pass
    return None


def _environ_cols_tput(*args):  # pragma: no cover
    """ cygwin xterm (windows) """
    try:
        import shlex
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        # rows = int(subprocess.check_call(shlex.split('tput lines')))
        return cols
    except:
        pass
    return None


def _environ_cols_linux(fp):  # pragma: no cover

    try:
        from termios import TIOCGWINSZ
        from fcntl import ioctl
        from array import array
    except ImportError:
        return None
    else:
        try:
            return array('h', ioctl(fp, TIOCGWINSZ, '\0' * 8))[1]
        except:
            try:
                from os.environ import get
            except ImportError:
                return None
            else:
                return int(get('COLUMNS', 1)) - 1


def _term_move_up():  # pragma: no cover
    return '' if (os.name == 'nt') and (colorama is None) else '\x1b[A'


class TqdmTypeError(TypeError):
    pass


class TqdmKeyError(KeyError):
    pass


class TqdmDeprecationWarning(Exception):
    # not suppressed if raised
    def __init__(self, msg, fp_write=None, *a, **k):
        if fp_write is not None:
            fp_write("\nTqdmDeprecationWarning: " + str(msg).rstrip() + '\n')
        else:
            super(TqdmDeprecationWarning, self).__init__(msg, *a, **k)


class TMonitor(Thread):
    # internal vars for unit testing
    _time = None
    _sleep = None

    def __init__(self, tqdm_cls, sleep_interval):
        # setcheckinterval is deprecated
        getattr(sys, 'setswitchinterval',
                getattr(sys, 'setcheckinterval'))(100)
        Thread.__init__(self)
        self.daemon = True  # kill thread when main killed (KeyboardInterrupt)
        self.was_killed = False
        self.woken = 0  # last time woken up, to sync with monitor
        self.tqdm_cls = tqdm_cls
        self.sleep_interval = sleep_interval
        if TMonitor._time is not None:
            self._time = TMonitor._time
        else:
            self._time = time
        if TMonitor._sleep is not None:
            self._sleep = TMonitor._sleep
        else:
            self._sleep = sleep
        self.start()

    def exit(self):
        self.was_killed = True
        # self.join()  # DO NOT, blocking event, slows down tqdm at closing
        return self.report()

    def run(self):
        cur_t = self._time()
        while True:
            # After processing and before sleeping, notify that we woke
            # Need to be done just before sleeping
            self.woken = cur_t
            # Sleep some time...
            self._sleep(self.sleep_interval)
            # Quit if killed
            # if self.exit_event.is_set():  # TODO: should work but does not...
            if self.was_killed:
                return
            # Then monitor!
            cur_t = self._time()
            # Check for each tqdm instance if one is waiting too long to print
            # NB: copy avoids size change during iteration RuntimeError
            for instance in self.tqdm_cls._instances.copy():
                # Only if mininterval > 1 (else iterations are just slow)
                # and last refresh was longer than maxinterval in this instance
                if instance.miniters > 1 and \
                        (cur_t - instance.last_print_t) >= instance.maxinterval:
                    # We force bypassing miniters on next iteration
                    # dynamic_miniters should adjust mininterval automatically
                    instance.miniters = 1
                    # Refresh now! (works only for manual tqdm)
                    instance.refresh()

    def report(self):
        # return self.is_alive()  # TODO: does not work...
        return not self.was_killed


class tqdm(object):
    monitor_interval = 10  # set to 0 to disable the thread
    monitor = None

    @staticmethod
    def format_sizeof(num, suffix='', divisor=1000):
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 999.95:
                if abs(num) < 99.95:
                    if abs(num) < 9.995:
                        return '{0:1.2f}'.format(num) + unit + suffix
                    return '{0:2.1f}'.format(num) + unit + suffix
                return '{0:3.0f}'.format(num) + unit + suffix
            num /= divisor
        return '{0:3.1f}Y'.format(num) + suffix

    @staticmethod
    def format_interval(t):
        mins, s = divmod(int(t), 60)
        h, m = divmod(mins, 60)
        if h:
            return '{0:d}:{1:02d}:{2:02d}'.format(h, m, s)
        else:
            return '{0:02d}:{1:02d}'.format(m, s)

    @staticmethod
    def status_printer(file):
        fp = file
        fp_flush = getattr(fp, 'flush', lambda: None)  # pragma: no cover

        def fp_write(s):
            fp.write(_unicode(s))
            fp_flush()

        last_len = [0]

        def print_status(s):
            len_s = len(s)
            fp_write('\r' + s + (' ' * max(last_len[0] - len_s, 0)))
            last_len[0] = len_s
        return print_status

    @staticmethod
    def format_meter(n, total, elapsed, ncols=None, prefix='',
                     ascii=False, unit='it', unit_scale=False, rate=None,
                     bar_format=None, postfix=None, unit_divisor=1000):

        # sanity check: total
        if total and n > total:
            total = None

        format_interval = tqdm.format_interval
        elapsed_str = format_interval(elapsed)

        # if unspecified, attempt to use rate = average speed
        # (we allow manual override since predicting time is an arcane art)
        if rate is None and elapsed:
            rate = n / elapsed
        inv_rate = 1 / rate if (rate and (rate < 1)) else None
        format_sizeof = tqdm.format_sizeof
        rate_fmt = ((format_sizeof(inv_rate if inv_rate else rate)
                    if unit_scale else
                    '{0:5.2f}'.format(inv_rate if inv_rate else rate))
                    if rate else '?') \
            + ('s' if inv_rate else unit) + '/' + (unit if inv_rate else 's')

        if unit_scale:
            n_fmt = format_sizeof(n, divisor=unit_divisor)
            total_fmt = format_sizeof(total, divisor=unit_divisor) \
                if total else None
        else:
            n_fmt = str(n)
            total_fmt = str(total)

        # total is known: we can predict some stats
        if total:
            # fractional and percentage progress
            frac = n / total
            percentage = frac * 100

            remaining_str = format_interval((total - n) / rate) \
                if rate else '?'

            # format the stats displayed to the left and right sides of the bar
            l_bar = (prefix if prefix else '') + \
                '{0:3.0f}%|'.format(percentage)
            r_bar = '| {0}/{1} [{2}<{3}, {4}{5}]'.format(
                    n_fmt, total_fmt, elapsed_str, remaining_str, rate_fmt,
                    ', ' + postfix if postfix else '')

            if ncols == 0:
                return l_bar[:-1] + r_bar[1:]

            if bar_format:
                # Custom bar formatting
                # Populate a dict with all available progress indicators
                bar_args = {'n': n,
                            'n_fmt': n_fmt,
                            'total': total,
                            'total_fmt': total_fmt,
                            'percentage': percentage,
                            'rate': rate if inv_rate is None else inv_rate,
                            'rate_noinv': rate,
                            'rate_noinv_fmt': ((format_sizeof(rate)
                                               if unit_scale else
                                               '{0:5.2f}'.format(rate))
                                               if rate else '?') + unit + '/s',
                            'rate_fmt': rate_fmt,
                            'elapsed': elapsed_str,
                            'remaining': remaining_str,
                            'l_bar': l_bar,
                            'r_bar': r_bar,
                            'desc': prefix if prefix else '',
                            'postfix': ', ' + postfix if postfix else '',
                            # 'bar': full_bar  # replaced by procedure below
                            }

                # Interpolate supplied bar format with the dict
                if '{bar}' in bar_format:
                    # Format left/right sides of the bar, and format the bar
                    # later in the remaining space (avoid breaking display)
                    l_bar_user, r_bar_user = bar_format.split('{bar}')
                    l_bar = l_bar_user.format(**bar_args)
                    r_bar = r_bar_user.format(**bar_args)
                else:
                    # Else no progress bar, we can just format and return
                    return bar_format.format(**bar_args)

            # Formatting progress bar
            # space available for bar's display
            N_BARS = max(1, ncols - len(l_bar) - len(r_bar)) if ncols \
                else 10

            # format bar depending on availability of unicode/ascii chars
            if ascii:
                bar_length, frac_bar_length = divmod(
                    int(frac * N_BARS * 10), 10)

                bar = '#' * bar_length
                frac_bar = chr(48 + frac_bar_length) if frac_bar_length \
                    else ' '

            else:
                bar_length, frac_bar_length = divmod(int(frac * N_BARS * 8), 8)

                bar = _unich(0x2588) * bar_length
                frac_bar = _unich(0x2590 - frac_bar_length) \
                    if frac_bar_length else ' '

            # whitespace padding
            if bar_length < N_BARS:
                full_bar = bar + frac_bar + \
                    ' ' * max(N_BARS - bar_length - 1, 0)
            else:
                full_bar = bar + \
                    ' ' * max(N_BARS - bar_length, 0)

            # Piece together the bar parts
            return l_bar + full_bar + r_bar

        # no total: no progressbar, ETA, just progress stats
        else:
            return (prefix if prefix else '') + '{0}{1} [{2}, {3}{4}]'.format(
                n_fmt, unit, elapsed_str, rate_fmt,
                ', ' + postfix if postfix else '')

    def __new__(cls, *args, **kwargs):
        # Create a new instance
        instance = object.__new__(cls)
        # Add to the list of instances
        if "_instances" not in cls.__dict__:
            cls._instances = WeakSet()
        cls._instances.add(instance)
        # Create the monitoring thread
        if cls.monitor_interval and (cls.monitor is None or
                                     not cls.monitor.report()):
            cls.monitor = TMonitor(cls, cls.monitor_interval)
        # Return the instance
        return instance

    @classmethod
    def _get_free_pos(cls, instance=None):
        """ Skips specified instance """
        try:
            return max(inst.pos for inst in cls._instances
                       if inst is not instance) + 1
        except ValueError as e:
            if "arg is an empty sequence" in str(e):
                return 0
            raise  # pragma: no cover

    @classmethod
    def _decr_instances(cls, instance):
        try:  # in case instance was explicitly positioned, it won't be in set
            cls._instances.remove(instance)
            for inst in cls._instances:
                if inst.pos > instance.pos:
                    inst.pos -= 1
            # Kill monitor if no instances are left
            if not cls._instances and cls.monitor:
                cls.monitor.exit()
                try:
                    del cls.monitor
                except AttributeError:
                    pass
                cls.monitor = None
        except KeyError:
            pass

    @classmethod
    def write(cls, s, file=None, end="\n"):
        fp = file if file is not None else sys.stdout

        # Clear all bars
        inst_cleared = []
        for inst in getattr(cls, '_instances', []):
            # Clear instance if in the target output file
            # or if write output + tqdm output are both either
            # sys.stdout or sys.stderr (because both are mixed in terminal)
            if inst.fp == fp or all(f in (sys.stdout, sys.stderr)
                                    for f in (fp, inst.fp)):
                inst.clear()
                inst_cleared.append(inst)
        # Write the message
        fp.write(s)
        fp.write(end)
        # Force refresh display of bars we cleared
        for inst in inst_cleared:
            # Avoid race conditions by checking that the instance started
            if hasattr(inst, 'start_t'):  # pragma: nocover
                inst.refresh()
        # TODO: make list of all instances incl. absolutely positioned ones?

    @classmethod
    def pandas(tclass, *targs, **tkwargs):
        from pandas.core.frame import DataFrame
        from pandas.core.series import Series
        from pandas.core.groupby import DataFrameGroupBy
        from pandas.core.groupby import SeriesGroupBy
        from pandas.core.groupby import GroupBy
        from pandas.core.groupby import PanelGroupBy
        from pandas import Panel

        deprecated_t = [tkwargs.pop('deprecated_t', None)]

        def inner_generator(df_function='apply'):
            def inner(df, func, *args, **kwargs):
                """
                Parameters
                ----------
                df  : (DataFrame|Series)[GroupBy]
                    Data (may be grouped).
                func  : function
                    To be applied on the (grouped) data.
                *args, *kwargs  : optional
                    Transmitted to `df.apply()`.
                """
                # Precompute total iterations
                total = getattr(df, 'ngroups', None)
                if total is None:  # not grouped
                    total = len(df) if isinstance(df, Series) \
                        else df.size // len(df)
                else:
                    total += 1  # pandas calls update once too many

                # Init bar
                if deprecated_t[0] is not None:
                    t = deprecated_t[0]
                    deprecated_t[0] = None
                else:
                    t = tclass(*targs, total=total, **tkwargs)

                # Define bar updating wrapper
                def wrapper(*args, **kwargs):
                    t.update()
                    return func(*args, **kwargs)

                # Apply the provided function (in *args and **kwargs)
                # on the df using our wrapper (which provides bar updating)
                result = getattr(df, df_function)(wrapper, *args, **kwargs)

                # Close bar and return pandas calculation result
                t.close()
                return result
            return inner

        # Monkeypatch pandas to provide easy methods
        # Enable custom tqdm progress in pandas!
        Series.progress_apply = inner_generator()
        SeriesGroupBy.progress_apply = inner_generator()
        Series.progress_map = inner_generator('map')
        SeriesGroupBy.progress_map = inner_generator('map')

        DataFrame.progress_apply = inner_generator()
        DataFrameGroupBy.progress_apply = inner_generator()
        DataFrame.progress_applymap = inner_generator('applymap')

        Panel.progress_apply = inner_generator()
        PanelGroupBy.progress_apply = inner_generator()

        GroupBy.progress_apply = inner_generator()
        GroupBy.progress_aggregate = inner_generator('aggregate')
        GroupBy.progress_transform = inner_generator('transform')

    def __init__(self, iterable=None, desc=None, total=None, leave=True,
                 file=None, ncols=None, mininterval=0.1,
                 maxinterval=10.0, miniters=None, ascii=None, disable=False,
                 unit='it', unit_scale=False, dynamic_ncols=False,
                 smoothing=0.3, bar_format=None, initial=0, position=None,
                 postfix=None, unit_divisor=1000,
                 gui=False, **kwargs):

        if disable is None and hasattr(file, "isatty") and not file.isatty():
            disable = True

        if disable:
            self.iterable = iterable
            self.disable = disable
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            return

        if file is None:
            file = sys.stderr

        if kwargs:
            self.disable = True
            self.pos = self._get_free_pos(self)
            self._instances.remove(self)
            raise (TqdmDeprecationWarning("""\
`nested` is deprecated and automated. Use position instead for manual control.
""", fp_write=getattr(file, 'write', sys.stderr.write))
                if "nested" in kwargs else
                TqdmKeyError("Unknown argument(s): " + str(kwargs)))

        # Preprocess the arguments
        if total is None and iterable is not None:
            try:
                total = len(iterable)
            except (TypeError, AttributeError):
                total = None

        if ((ncols is None) and (file in (sys.stderr, sys.stdout))) or \
                dynamic_ncols:  # pragma: no cover
            if dynamic_ncols:
                dynamic_ncols = _environ_cols_wrapper()
                if dynamic_ncols:
                    ncols = dynamic_ncols(file)
                # elif ncols is not None:
                #     ncols = 79
            else:
                _dynamic_ncols = _environ_cols_wrapper()
                if _dynamic_ncols:
                    ncols = _dynamic_ncols(file)
                # else:
                #     ncols = 79

        if miniters is None:
            miniters = 0
            dynamic_miniters = True
        else:
            dynamic_miniters = False

        if mininterval is None:
            mininterval = 0

        if maxinterval is None:
            maxinterval = 0

        if ascii is None:
            ascii = not _supports_unicode(file)

        if bar_format and not ascii:
            # Convert bar format into unicode since terminal uses unicode
            bar_format = _unicode(bar_format)

        if smoothing is None:
            smoothing = 0

        # Store the arguments
        self.iterable = iterable
        self.desc = desc + ': ' if desc else ''
        self.total = total
        self.leave = leave
        self.fp = file
        self.ncols = ncols
        self.mininterval = mininterval
        self.maxinterval = maxinterval
        self.miniters = miniters
        self.dynamic_miniters = dynamic_miniters
        self.ascii = ascii
        self.disable = disable
        self.unit = unit
        self.unit_scale = unit_scale
        self.unit_divisor = unit_divisor
        self.gui = gui
        self.dynamic_ncols = dynamic_ncols
        self.smoothing = smoothing
        self.avg_time = None
        self._time = time
        self.bar_format = bar_format
        self.postfix = None
        if postfix:
            self.set_postfix(**postfix)

        # Init the iterations counters
        self.last_print_n = initial
        self.n = initial

        # if nested, at initial sp() call we replace '\r' by '\n' to
        # not overwrite the outer progress bar
        if position is None:
            self.pos = self._get_free_pos(self)
        else:
            self.pos = position
            self._instances.remove(self)

        if not gui:
            # Initialize the screen printer
            self.sp = self.status_printer(self.fp)
            if self.pos:
                self.moveto(self.pos)
            self.sp(self.format_meter(self.n, total, 0,
                    (dynamic_ncols(file) if dynamic_ncols else ncols),
                    self.desc, ascii, unit, unit_scale, None, bar_format,
                    self.postfix, unit_divisor))
            if self.pos:
                self.moveto(-self.pos)

        # Init the time counter
        self.last_print_t = self._time()
        # NB: Avoid race conditions by setting start_t at the very end of init
        self.start_t = self.last_print_t

    def __len__(self):
        return self.total if self.iterable is None else \
            (self.iterable.shape[0] if hasattr(self.iterable, "shape")
             else len(self.iterable) if hasattr(self.iterable, "__len__")
             else self.total)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False

    def __del__(self):
        self.close()

    def __repr__(self):
        return self.format_meter(self.n, self.total,
                                 self._time() - self.start_t,
                                 self.dynamic_ncols(self.fp)
                                 if self.dynamic_ncols else self.ncols,
                                 self.desc, self.ascii, self.unit,
                                 self.unit_scale, 1 / self.avg_time
                                 if self.avg_time else None, self.bar_format,
                                 self.postfix)

    def __lt__(self, other):
        return self.pos < other.pos

    def __le__(self, other):
        return (self < other) or (self == other)

    def __eq__(self, other):
        return self.pos == other.pos

    def __ne__(self, other):
        return not (self == other)

    def __gt__(self, other):
        return not (self <= other)

    def __ge__(self, other):
        return not (self < other)

    def __hash__(self):
        return id(self)

    def __iter__(self):
        ''' Backward-compatibility to use: for x in tqdm(iterable) '''

        # Inlining instance variables as locals (speed optimisation)
        iterable = self.iterable

        # If the bar is disabled, then just walk the iterable
        # (note: keep this check outside the loop for performance)
        if self.disable:
            for obj in iterable:
                yield obj
        else:
            ncols = self.ncols
            mininterval = self.mininterval
            maxinterval = self.maxinterval
            miniters = self.miniters
            dynamic_miniters = self.dynamic_miniters
            unit = self.unit
            unit_scale = self.unit_scale
            unit_divisor = self.unit_divisor
            ascii = self.ascii
            start_t = self.start_t
            last_print_t = self.last_print_t
            last_print_n = self.last_print_n
            n = self.n
            dynamic_ncols = self.dynamic_ncols
            smoothing = self.smoothing
            avg_time = self.avg_time
            bar_format = self.bar_format
            _time = self._time
            format_meter = self.format_meter

            try:
                sp = self.sp
            except AttributeError:
                raise TqdmDeprecationWarning("""\
Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`
""", fp_write=getattr(self.fp, 'write', sys.stderr.write))

            for obj in iterable:
                yield obj
                # Update and print the progressbar.
                # Note: does not call self.update(1) for speed optimisation.
                n += 1
                # check the counter first (avoid calls to time())
                if n - last_print_n >= self.miniters:
                    miniters = self.miniters  # watch monitoring thread changes
                    delta_t = _time() - last_print_t
                    if delta_t >= mininterval:
                        cur_t = _time()
                        delta_it = n - last_print_n
                        elapsed = cur_t - start_t  # optimised if in inner loop
                        # EMA (not just overall average)
                        if smoothing and delta_t and delta_it:
                            avg_time = delta_t / delta_it \
                                if avg_time is None \
                                else smoothing * delta_t / delta_it + \
                                (1 - smoothing) * avg_time

                        if self.pos:
                            self.moveto(self.pos)

                        # Printing the bar's update
                        sp(format_meter(
                            n, self.total, elapsed,
                            (dynamic_ncols(self.fp) if dynamic_ncols
                             else ncols),
                            self.desc, ascii, unit, unit_scale,
                            1 / avg_time if avg_time else None, bar_format,
                            self.postfix, unit_divisor))

                        if self.pos:
                            self.moveto(-self.pos)

                        # If no `miniters` was specified, adjust automatically
                        # to the max iteration rate seen so far between 2 prints
                        if dynamic_miniters:
                            if maxinterval and delta_t >= maxinterval:
                                # Adjust miniters to time interval by rule of 3
                                if mininterval:
                                    # Set miniters to correspond to mininterval
                                    miniters = delta_it * mininterval / delta_t
                                else:
                                    # Set miniters to correspond to maxinterval
                                    miniters = delta_it * maxinterval / delta_t
                            elif smoothing:
                                # EMA-weight miniters to converge
                                # towards the timeframe of mininterval
                                miniters = smoothing * delta_it * \
                                    (mininterval / delta_t
                                     if mininterval and delta_t
                                     else 1) + \
                                    (1 - smoothing) * miniters
                            else:
                                # Maximum nb of iterations between 2 prints
                                miniters = max(miniters, delta_it)

                        # Store old values for next call
                        self.n = self.last_print_n = last_print_n = n
                        self.last_print_t = last_print_t = cur_t
                        self.miniters = miniters

            # Closing the progress bar.
            # Update some internal variables for close().
            self.last_print_n = last_print_n
            self.n = n
            self.miniters = miniters
            self.close()

    def update(self, n=1):
        if self.disable:
            return

        if n < 0:
            raise ValueError("n ({0}) cannot be negative".format(n))
        self.n += n

        if self.n - self.last_print_n >= self.miniters:
            # We check the counter first, to reduce the overhead of time()
            delta_t = self._time() - self.last_print_t
            if delta_t >= self.mininterval:
                cur_t = self._time()
                delta_it = self.n - self.last_print_n  # should be n?
                # elapsed = cur_t - self.start_t
                # EMA (not just overall average)
                if self.smoothing and delta_t and delta_it:
                    self.avg_time = delta_t / delta_it \
                        if self.avg_time is None \
                        else self.smoothing * delta_t / delta_it + \
                        (1 - self.smoothing) * self.avg_time

                if not hasattr(self, "sp"):
                    raise TqdmDeprecationWarning("""\
Please use `tqdm_gui(...)` instead of `tqdm(..., gui=True)`
""", fp_write=getattr(self.fp, 'write', sys.stderr.write))

                if self.pos:
                    self.moveto(self.pos)

                # Print bar's update
                self.sp(self.__repr__())

                if self.pos:
                    self.moveto(-self.pos)

                # If no `miniters` was specified, adjust automatically to the
                # maximum iteration rate seen so far between two prints.
                # e.g.: After running `tqdm.update(5)`, subsequent
                # calls to `tqdm.update()` will only cause an update after
                # at least 5 more iterations.
                if self.dynamic_miniters:
                    if self.maxinterval and delta_t >= self.maxinterval:
                        if self.mininterval:
                            self.miniters = delta_it * self.mininterval \
                                / delta_t
                        else:
                            self.miniters = delta_it * self.maxinterval \
                                / delta_t
                    elif self.smoothing:
                        self.miniters = self.smoothing * delta_it * \
                            (self.mininterval / delta_t
                             if self.mininterval and delta_t
                             else 1) + \
                            (1 - self.smoothing) * self.miniters
                    else:
                        self.miniters = max(self.miniters, delta_it)

                # Store old values for next call
                self.last_print_n = self.n
                self.last_print_t = cur_t

    def close(self):
        """
        Cleanup and (if leave=False) close the progressbar.
        """
        if self.disable:
            return

        # Prevent multiple closures
        self.disable = True

        # decrement instance pos and remove from internal set
        pos = self.pos
        self._decr_instances(self)

        # GUI mode
        if not hasattr(self, "sp"):
            return

        # annoyingly, _supports_unicode isn't good enough
        def fp_write(s):
            self.fp.write(_unicode(s))

        try:
            fp_write('')
        except ValueError as e:
            if 'closed' in str(e):
                return
            raise  # pragma: no cover

        if pos:
            self.moveto(pos)

        if self.leave:
            if self.last_print_n < self.n:
                cur_t = self._time()
                # stats for overall rate (no weighted average)
                self.sp(self.format_meter(
                    self.n, self.total, cur_t - self.start_t,
                    (self.dynamic_ncols(self.fp) if self.dynamic_ncols
                     else self.ncols),
                    self.desc, self.ascii, self.unit, self.unit_scale, None,
                    self.bar_format, self.postfix, self.unit_divisor))
            if pos:
                self.moveto(-pos)
            else:
                fp_write('\n')
        else:
            self.sp('')  # clear up last bar
            if pos:
                self.moveto(-pos)
            else:
                fp_write('\r')

    def unpause(self):
        """
        Restart tqdm timer from last print time.
        """
        cur_t = self._time()
        self.start_t += cur_t - self.last_print_t
        self.last_print_t = cur_t

    def set_description(self, desc=None):
        """
        Set/modify description of the progress bar.
        """
        self.desc = desc + ': ' if desc else ''

    def set_postfix(self, ordered_dict=None, **kwargs):
        """
        Set/modify postfix (additional stats)
        with automatic formatting based on datatype.
        """
        # Sort in alphabetical order to be more deterministic
        postfix = _OrderedDict([] if ordered_dict is None else ordered_dict)
        for key in sorted(kwargs.keys()):
            postfix[key] = kwargs[key]
        # Preprocess stats according to datatype
        for key in postfix.keys():
            # Number: limit the length of the string
            if isinstance(postfix[key], Number):
                postfix[key] = '{0:2.3g}'.format(postfix[key])
            # Else for any other type, try to get the string conversion
            elif not isinstance(postfix[key], _basestring):
                postfix[key] = str(postfix[key])
            # Else if it's a string, don't need to preprocess anything
        # Stitch together to get the final postfix
        self.postfix = ', '.join(key + '=' + postfix[key].strip()
                                 for key in postfix.keys())

    def moveto(self, n):
        self.fp.write(_unicode('\n' * n + _term_move_up() * -n))

    def clear(self, nomove=False):
        """
        Clear current bar display
        """
        if self.disable:
            return

        if not nomove:
            self.moveto(self.pos)
        # clear up the bar (can't rely on sp(''))
        self.fp.write('\r')
        self.fp.write(' ' * (self.ncols if self.ncols else 10))
        self.fp.write('\r')  # place cursor back at the beginning of line
        if not nomove:
            self.moveto(-self.pos)

    def refresh(self):
        """
        Force refresh the display of this bar
        """
        if self.disable:
            return

        self.moveto(self.pos)
        # clear up this line's content (whatever there was)
        self.clear(nomove=True)
        # Print current/last bar state
        self.fp.write(self.__repr__())
        self.moveto(-self.pos)
