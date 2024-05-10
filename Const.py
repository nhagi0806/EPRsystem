"""
Constant types in Python.
"""

class _const:
    class ConstError(TypeError):
        pass

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise self.ConstError("Can't rebind const (%s)" % name)
        self.__dict__[name] = value


A_hfs = 1.011911 * 10**9  # Hz
I = 5 / 2
g_s = 2.002331
mu_B = 9.927401 * 10**-24  # J/T
mu_0 = 4 * np.pi * 10**-7
mu_129 = -3.929344 * 10**-27  # N/A**2
kapper_0 = 518
B_0 = 1.6133 * 10**-3  # T
h = 6.62607015 * 10**-34
num_129 = 7.32 * 10**25