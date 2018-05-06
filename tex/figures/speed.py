"""Starry speed tests."""
import starry
import timeit
try:
    import builtins
except ImportError:
    import __builtin__ as builtins
import matplotlib.pyplot as pl
from tqdm import tqdm
from scipy.integrate import dblquad
import numpy as np
np.random.seed(1234)


def GridFlux(I, b, r, res=100):
    """Compute the flux by brute-force grid integration."""
    flux = 0
    dA = np.pi / (res ** 2)
    for x in np.linspace(-1, 1, res):
        for y in np.linspace(-1, 1, res):
            if (x ** 2 + y ** 2 > 1):
                continue
            elif ((y - b) ** 2 + x ** 2 < r ** 2):
                continue
            else:
                flux += I(y, x) * dA
    return flux


def NumericalFlux(I, b, r, epsabs=1e-8, epsrel=1e-8):
    """Compute the flux by numerical integration of the surface integral."""
    # I'm only coding up a specific case here
    assert (b >= 0) and (r <= 1), "Invalid range."

    # Total flux
    total, _ = dblquad(I, -1, 1, lambda x: -np.sqrt(1 - x ** 2),
                       lambda x: np.sqrt(1 - x ** 2),
                       epsabs=epsabs, epsrel=epsrel)
    if b >= 1 + r:
        return total

    # Get points of intersection
    if b > 1 - r:
        yi = (1. + b ** 2 - r ** 2) / (2. * b)
        xi = (1. / (2. * b)) * np.sqrt(4 * b ** 2 - (1 + b ** 2 - r ** 2) ** 2)
    else:
        yi = np.inf
        xi = r

    # Lower integration limit
    def y1(x):
        if yi <= b:
            # Lower occultor boundary
            return b - np.sqrt(r ** 2 - x ** 2)
        elif b <= 1 - r:
            # Lower occultor boundary
            return b - np.sqrt(r ** 2 - x ** 2)
        else:
            # Tricky: we need to do this in two parts
            return b - np.sqrt(r ** 2 - x ** 2)

    # Upper integration limit
    def y2(x):
        if yi <= b:
            # Upper occulted boundary
            return np.sqrt(1 - x ** 2)
        elif b <= 1 - r:
            # Upper occultor boundary
            return b + np.sqrt(r ** 2 - x ** 2)
        else:
            # Tricky: we need to do this in two parts
            return np.sqrt(1 - x ** 2)

    # Compute the total flux
    flux, _ = dblquad(I, -xi, xi, y1, y2, epsabs=epsabs, epsrel=epsrel)

    # Do we need to solve additional integrals?
    if not (yi <= b) and not (b <= 1 - r):

        def y1(x):
            return b - np.sqrt(r ** 2 - x ** 2)

        def y2(x):
            return b + np.sqrt(r ** 2 - x ** 2)

        additional_flux1, _ = dblquad(I, -r, -xi, y1, y2,
                                      epsabs=epsabs, epsrel=epsrel)
        additional_flux2, _ = dblquad(I, xi, r, y1, y2,
                                      epsabs=epsabs, epsrel=epsrel)

        flux += additional_flux1 + additional_flux2

    return total - flux


def compare_to_numerical():
    """Compare to different numerical integration schemes."""
    lmax = 6
    number = 1
    res = 300
    nstarry = 1000
    ylm = starry.Map(lmax)
    ylm_grad = starry.grad.Map(lmax)
    X, Y = np.meshgrid(np.linspace(-1, 1, res), np.linspace(-1, 1, res))

    class Funcs(object):

        def fnumer(self):
            self.vnumer = NumericalFlux(lambda y, x:
                                        ylm.evaluate(x=x, y=y), b, r)

        def fstar(self):
            self.vstar = ylm.flux(xo=np.zeros(nstarry), yo=b, ro=r)[0]

        def fgrad(self):
            self.vgrad = ylm_grad.flux(xo=np.zeros(nstarry), yo=b, ro=r)[0]

        def fmesh(self):
            self.vmesh = ylm.flux_numerical(yo=b, ro=r)

        def fgrid(self):
            self.vgrid = GridFlux(lambda y, x:
                                  ylm.evaluate(x=x, y=y), b, r)

    funcs = Funcs()
    time_starry = np.zeros(lmax + 1)
    time_grad = np.zeros(lmax + 1)
    time_numer = np.zeros(lmax + 1)
    time_mesh = np.zeros(lmax + 1)
    time_grid = np.zeros(lmax + 1)
    error_numer = np.zeros(lmax + 1)
    error_mesh = np.zeros(lmax + 1)
    error_grid = np.zeros(lmax + 1)
    for l in range(lmax + 1):
        # Randomize a map and occultor properties
        b = np.random.random()
        r = np.random.random()
        for m in range(-l, l + 1):
            c = np.random.random()
            ylm[l, m] = c
            ylm_grad[l, m] = c
        # Time the runs
        builtins.__dict__.update(locals())
        time_starry[l] = timeit.timeit('funcs.fstar()', number=1) / nstarry
        time_grad[l] = timeit.timeit('funcs.fgrad()', number=1) / nstarry
        time_numer[l] = timeit.timeit('funcs.fnumer()', number=1)
        time_mesh[l] = timeit.timeit('funcs.fmesh()', number=1)
        time_grid[l] = timeit.timeit('funcs.fgrid()', number=1)
        # Compute the fractional error
        error_numer[l] = np.abs(funcs.vnumer / funcs.vstar - 1)
        error_mesh[l] = np.abs(funcs.vmesh / funcs.vstar - 1)
        error_grid[l] = np.abs(funcs.vgrid / funcs.vstar - 1)

    # Marker size is proportional to log error
    def ms(error):
        return 18 + np.log10(error)

    # Plot it
    fig = pl.figure(figsize=(7, 4))
    ax = pl.subplot2grid((2, 5), (0, 0), colspan=4, rowspan=2)
    axleg1 = pl.subplot2grid((2, 5), (0, 4))
    axleg2 = pl.subplot2grid((2, 5), (1, 4))
    axleg1.axis('off')
    axleg2.axis('off')
    ax.set_xlabel('Spherical harmonic degree', fontsize=14, fontweight='bold')
    ax.set_xticks(range(lmax + 1))
    for tick in ax.get_xticklabels():
        tick.set_fontsize(12)
    ax.set_ylabel('Evaluation time [seconds]', fontsize=14, fontweight='bold')

    # Starry
    ax.plot(range(lmax + 1), time_starry, 'o', color='C0', ms=2)
    ax.plot(range(lmax + 1), time_starry, '-', color='C0', lw=1, alpha=0.25)

    # Starry.grad
    ax.plot(range(lmax + 1), time_grad, 'o', color='C4', ms=2)
    ax.plot(range(lmax + 1), time_grad, '-', color='C4', lw=1, alpha=0.25)

    # Mesh
    for l in range(lmax + 1):
        ax.plot(l, time_mesh[l], 'o', color='C1', ms=ms(error_mesh[l]))
    ax.plot(range(lmax + 1), time_mesh, '-', color='C1', lw=1, alpha=0.25)

    # Grid
    for l in range(lmax + 1):
        ax.plot(l, time_grid[l], 'o', color='C2', ms=ms(error_grid[l]))
    ax.plot(range(lmax + 1), time_grid, '-', color='C2', lw=1, alpha=0.25)

    # Numerical
    for l in range(lmax + 1):
        ax.plot(l, time_numer[l], 'o', color='C3', ms=ms(error_numer[l]))
    ax.plot(range(lmax + 1), time_numer, '-', color='C3', lw=1, alpha=0.25)
    ax.set_yscale('log')

    axleg1.plot([0, 1], [0, 1], color='C0', label='starry')
    axleg1.plot([0, 1], [0, 1], color='C4', label='starry.grad')
    axleg1.plot([0, 1], [0, 1], color='C1', label='mesh')
    axleg1.plot([0, 1], [0, 1], color='C2', label='grid')
    axleg1.plot([0, 1], [0, 1], color='C3', label='dblquad')
    axleg1.set_xlim(2, 3)
    axleg1.legend(loc='center', frameon=False, title=r'\textbf{method}')

    for logerr in [-16, -12, -8, -4, 0]:
        axleg2.plot([0, 1], [0, 1], 'o', color='gray',
                    ms=ms(10 ** logerr),
                    label=r'$%3d$' % logerr)
    axleg2.set_xlim(2, 3)
    leg = axleg2.legend(loc='center', labelspacing=1, frameon=False,
                        title=r'\textbf{log error}')

    fig.savefig("compare_to_numerical.pdf", bbox_inches='tight')


def speed():
    """Run the main speed tests for phase curves and occultations."""
    # Constants
    number = 3
    lmax = 5
    nN = 8
    Nmax = 5
    time_phase = np.zeros((lmax + 1, 2 * lmax + 1, nN))
    time_occ = np.zeros((lmax + 1, 2 * lmax + 1, nN))
    Narr = np.logspace(1, Nmax, nN)

    # Loop over number of cadences
    for i, N in tqdm(enumerate(Narr), total=nN):

        # Compute for each Ylm
        theta = np.linspace(0, 2 * np.pi, N)
        xo = np.linspace(-1., 1., N)
        for l in range(lmax + 1):
            ylm = starry.Map(l)
            for m in range(-l, l + 1):
                ylm.reset()
                ylm[l, m] = 1
                builtins.__dict__.update(locals())

                # Phase curve
                time_phase[l, m, i] = timeit.timeit(
                    'ylm.flux(axis=[0,1,0], theta=theta)',
                    number=number) / number

                # Occultation (no rotation)
                time_occ[l, m, i] = timeit.timeit(
                    'ylm.flux(xo=xo, yo=0.5, ro=0.1)',
                    number=number) / number

    # Plot
    fig, ax = pl.subplots(2, 2, figsize=(7, 5))
    ax = ax.flatten()
    for l in range(lmax + 1):
        time_phasel = np.zeros(nN)
        time_occl = np.zeros(nN)
        for m in range(-l, l + 1):
            time_phasel += time_phase[l, m]
            time_occl += time_occ[l, m]
        time_phasel /= (2 * l + 1)
        time_occl /= (2 * l + 1)
        color = 'C%d' % l
        ax[0].plot(Narr, time_phasel, 'o', ms=2, color=color)
        ax[0].plot(Narr, time_phasel, '-',
                   lw=0.5, color=color, label=r"$l = %d$" % l)
        ax[1].plot(Narr, time_occl, 'o', ms=2, color=color)
        ax[1].plot(Narr, time_occl, '-',
                   lw=0.5, color=color, label=r"$l = %d$" % l)

    l = 5
    for m in range(l + 1):
        color = 'C%d' % m
        ax[2].plot(Narr, time_phase[l, m], 'o', ms=2, color=color)
        ax[2].plot(Narr, time_phase[l, m], '-',
                   lw=0.5, color=color, label=r"$m = %d$" % m)
        ax[3].plot(Narr, time_occ[l, m], 'o', ms=2, color=color)
        ax[3].plot(Narr, time_occ[l, m], '-',
                   lw=0.5, color=color, label=r"$m = %d$" % m)

    # Tweak and save
    ax[0].legend(fontsize=7, loc='upper left')
    ax[1].legend(fontsize=7, loc='upper left')
    ax[2].legend(fontsize=7, loc='upper left')
    ax[3].legend(fontsize=7, loc='upper left')
    ax[0].set_ylabel("Time [s]", fontsize=10)
    ax[2].set_ylabel("Time [s]", fontsize=10)
    ax[2].set_xlabel("Number of points", fontsize=10)
    ax[3].set_xlabel("Number of points", fontsize=10)
    ax[0].set_title('Phase curves')
    ax[1].set_title('Occultations')
    for axis in ax:
        axis.grid(True)
        for line in axis.get_xgridlines() + axis.get_ygridlines():
            line.set_linewidth(0.2)
        axis.set_xscale('log')
        axis.set_yscale('log')
        axis.set_ylim(1e-5, 1e0)
    fig.savefig("speed.pdf", bbox_inches='tight')


if __name__ == "__main__":
    compare_to_numerical()
    speed()
