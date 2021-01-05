# imports
import numpy as np
import pandas as pd
import os
import sys
import pdb
import matplotlib.pyplot as plt
import astropy.coordinates as coord
import astropy.units as u
from astropy.coordinates import SkyCoord
from skyfield.api import load, Star, T0
from skyfield.data import hipparcos
from seti_lens.get_probe_coords import *
from seti_lens.download_data import *
from seti_lens.drift_rate import *


def parallax_mas_to_dist(parallax_mas):
    return 1.0 / (parallax_mas / 1000.0)


def get_hip_stars(max_dist=25.0):
    # get the hipparcos catalog
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)

    # filter on observable by GBT
    min_dec = -41.9017
    df = df[(-1.0 * df.dec_degrees) >= min_dec]

    # filter on distance (default <25 pc)
    df = df[parallax_mas_to_dist(df.parallax_mas) <= max_dist]
    return df


def read_btl_csv():
    # import the breakthrough archival data CSV
    infile = "/Users/mlp95/Desktop/bldb_files.csv"
    names = ["telescope", "datetime", "target", "ra", "dec", "derp", "datatype", "datasize", "checksum", "url"]
    df = pd.read_csv(infile, names=names)

    # only select filterbank GBT observations
    df = df[(df.telescope == "GBT") & ((df.datatype=="filterbank") | (df.datatype=="HDF5"))]
    return df


def plot_hipparcos_stars(hip_df, btl_df=None, antipode=False):
    # get coordinates
    ra_deg = hip_df.ra_degrees.to_numpy()
    dec_deg = hip_df.dec_degrees.to_numpy()

    if antipode:
        ra_deg = (ra_deg + 180.0) % 360
        dec_deg = -1.0 * dec_deg
        c = "tab:orange"
        filename = "/Users/mlp95/Desktop/hip_observable_antipode.pdf"
        label = "Hipparcos Antipodes"
    else:
        c = "tab:blue"
        filename = "/Users/mlp95/Desktop/hip_observable.pdf"
        label = "Hipparcos Stars"

    # convert to astropy units
    ra = coord.Angle(ra_deg * u.degree)
    ra = ra.wrap_at(180.0 * u.degree)
    dec = coord.Angle(dec_deg * u.degree)

    # plot it
    fig = plt.figure()
    ax = fig.add_subplot(111, projection="mollweide")
    ax.scatter(ra.radian, dec.radian, s=2, c=c, label=label)

    ncol = 1
    if btl_df is not None:
        ncol += 1

        # get coordinates
        ra_btl = btl_df.ra.to_numpy()
        dec_btl = btl_df.dec.to_numpy()

        # convert to astropy units
        ra = coord.Angle(ra_btl * u.deg)
        ra = ra.wrap_at(180.0 * u.deg)
        dec = coord.Angle(dec_btl * u.deg)

        # plot it
        ax.scatter(ra.radian, dec.radian, s=0.5, c="k", label="Breakthrough Listen")
        ax.set_xticklabels([])

    # save it and return
    ax.grid(True, linestyle=":")
    plt.legend(bbox_to_anchor=(0,1.02,1,0.2), loc="lower left", borderaxespad=1, ncol=1)
    fig.savefig(filename, bbox_inches="tight", dpi=125)
    plt.clf()
    plt.close()
    return None


def check_overlap(btl_df, hip_df, outfile=None, tol_angle=None, clobber=False, nrand=None):
    assert outfile is not None
    assert tol_angle is not None

    # check if outfile exists
    if os.path.isfile(outfile):
        if clobber == False:
            return outfile

    # take a random subset if nrand
    if nrand is not None:
        rand1 = np.random.randint(0, high=len(btl_df), size=(nrand,))
        rand2 = np.random.randint(0, high=len(hip_df), size=(nrand,))
        btl_df = btl_df.iloc[rand1, :]
        hip_df = hip_df.iloc[rand2, :]

    # now find overlap
    print("Searching for overlap...")
    overlap = []
    for index1, row1 in btl_df.iterrows():
        c1 = SkyCoord(row1.ra*u.deg, row1.dec*u.deg, frame='fk5')
        for index2, row2 in hip_df.iterrows():
            # flip the coords for antipodes
            ra = (row2.ra_degrees + 180.0) % 360
            dec = -1.0 * row2.dec_degrees
            c2 = SkyCoord(ra*u.deg, dec*u.deg, frame='icrs')

            # get the separation and check if it's within tolerance
            sep = c1.separation(c2)
            if sep.is_within_bounds(upper=tol_angle):
                print(index1)
                overlap.append((index1, index2))

    # write to file
    print("Writing to file...")
    with open(outfile, 'w') as f:
        for line in overlap:
            f.write("{}\n".format(line))
    return None


def main():
    # get dataframes with observations and hipparcos stars
    btl_df = read_btl_csv()
    hip_df = get_hip_stars()

    # plot hip stars and their antipodes
    # plot_hipparcos_stars(hip_df)
    # plot_hipparcos_stars(hip_df, btl_df=btl_df, antipode=True)

    # check for overlap and write results to file
    tol_angle = 1.0 * u.arcmin
    outfile = "/Users/mlp95/Desktop/overlap.txt"
    # outfile = "/storage/home/mlp95/work/overlap.txt"
    check_overlap(btl_df, hip_df, tol_angle=tol_angle,
                  outfile=outfile, nrand=500, clobber=True)

    return None


if __name__ == "__main__":
    main()
