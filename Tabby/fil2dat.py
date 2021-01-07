# imports n stuff
import numpy as np
import os
import sys
import pdb
import glob
import time
import argparse
import turbo_seti
import blimpy as bp
import seti_lens as sl
from turbo_seti.find_doppler.find_doppler import FindDoppler
from turbo_seti.find_event.find_event_pipeline import find_event_pipeline
from turbo_seti.find_event.plot_event_pipeline import plot_event_pipeline

def parse_args():
    parser = argparse.ArgumentParser(description='Process GBT Breakthrough data.')
    parser.add_argument('indir', metavar='indir', type=str, nargs=1,
                        help='directory containing the .fil files')
    parser.add_argument('--clobber', action='store_true',
                        help='overwrite files if they already exist')
    parser.add_argument('--gpu', action='store_true',
                        help='use GPU acceleration if possible')
    args = parser.parse_args()

    # check for trailing slash
    odict = vars(args)
    indir = odict["indir"][0]
    if indir[-1] != "/":
        indir += "/"
    odict["indir"] = indir
    return odict


def get_file_id(filename):
    return str(filename.split(".")[0][-2:])


def get_blc(filename):
    return str(filename.split("_")[0][-2:])


def sort_by_file_id(file_list):
    # look for the observing sequence number in file name
    ids = []
    for file in file_list:
        ids.append(get_file_id(file))
    idx = np.argsort(ids)
    file_list = np.array(file_list)[idx]
    file_list = np.ndarray.tolist(file_list)
    return file_list


def sort_by_blc(file_list):
    # look for the blc node in the file name
    ids = []
    for file in file_list:
        ids.append(get_blc(file))
    idx = np.argsort(ids)
    file_list = np.array(file_list)[idx]
    file_list = np.ndarray.tolist(file_list)
    return file_list


def find_input_data(indir, suffix, zeros_only=True, sort_id=True):
    # find the data first
    if zeros_only:
        file_list = glob.glob(indir + "*0000" + suffix)
    else:
        file_list = glob.glob(indir + "*" + suffix)
    # sort by file IDs if true
    assert len(file_list) >= 1
    if sort_id:
        file_list = sort_by_file_id(file_list)
    return file_list


def convert_to_h5(file, outdir="./", clobber=False):
    # check if the file already exists
    pre, ext = os.path.splitext(os.path.basename(file))
    out_file = outdir + pre + ".h5"
    if os.path.isfile(out_file):
        if clobber == False:
            print("\n" + pre + ".h5" + " already exists. Moving on...")
            return out_file

    # else do the conversion and return new file name
    print("\nconverting " + file + " to HDF5")
    bp.fil2h5.make_h5_file(file, out_dir=outdir)
    print("finished " + out_file)
    return out_file


def run_turbo_seti(file, max_drift=np.nan, min_snr=10.0, outdir="./", clobber=False, gpu_backend=False):
    assert max_drift != np.nan

    # check if the file already exists
    pre, ext = os.path.splitext(os.path.basename(file))
    out_file = outdir + pre + ".dat"
    if os.path.isfile(out_file):
        if clobber == False:
            print("\n" + pre + ".dat" + " already exists. Moving on...")
            return out_file
        else:
            os.remove(out_file)

    # call FindDoppler
    print("\nrun_turbo_seti: Calling FindDoppler({})".format(file))
    fdop = FindDoppler(datafile=file, max_drift=max_drift,
                       snr=min_snr, out_dir=outdir, min_drift=-max_drift,
                       gpu_backend=gpu_backend)

    # search for hits and report elapsed time.
    print("\nPlease wait ...")
    t0 = time.time()
    fdop.search()
    et = time.time() - t0
    print("run_turbo_seti: search() elapsed time = {} seconds".format(et))
    print("\n")

    # return the .dat file name
    return out_file


def main():
    # parse the command line arguments
    cmd_args = parse_args()

    # get the input data directory and the clobber value
    indir = cmd_args["indir"]
    if not os.path.isdir(indir):
        print("\n Specified directory does not exist. Exiting... \n")
        sys.exit()

    # deal with GPU stuff
    gpu_backend = cmd_args["gpu"]
    if gpu_backend:
        import cupy
        outdir = indir + "processed_gpu/"
    else:
        outdir = indir + "processed/"

    # make the "processed" directory if needed
    if not os.path.isdir(outdir):
        os.mkdir(outdir)

    # delete old output if clobber is true
    clobber = cmd_args["clobber"]
    if clobber:
        print("\nRemoving old files...")
        old_files = glob.glob(outdir + "*")
        for file in old_files:
            os.remove(file)
            print("%s has been removed successfully" %file) 

    # get appropriate list of .fil files in directory
    fil_list = find_input_data(indir, '.fil')

    # write .fil files to .lst file for plot_event_pipeline later
    lst_fil = outdir + "fil_files.lst"
    if os.path.isfile(lst_fil):
        os.remove(lst_fil)
    with open(lst_fil, 'w') as f:
        for item in fil_list:
            f.write("%s\n" % item)
    assert os.path.isfile(lst_fil)

    # loop over input files, do reduction to .dat file
    for fil in fil_list:
        # convert filterbank file to HDF5
        outfile = convert_to_h5(fil, outdir=outdir, clobber=clobber)

        # set drift_rate and SNR here for now
        # need to change this later as an input parameter
        drift_rate = 4
        min_SNR = 10

        # call FindDoppler
        datfile = run_turbo_seti(outfile,
                                 min_snr=min_SNR,
                                 outdir=outdir,
                                 clobber=clobber,
                                 max_drift=drift_rate,
                                 gpu_backend=gpu_backend)

    # remove old dat lists even if clobber off    
    print("\nRemoving old dat lists...")
    old_files = glob.glob(outdir + "dat*.lst")
    for file in old_files:
        os.remove(file)
        print("%s has been removed successfully" %file) 


    # get appropriate list of .dat files in directory
    dat_list = find_input_data(outdir, '.dat')
    dat_list = sort_by_file_id(dat_list)

    for file in dat_list:
        # write .dat files to .lst file for FileCombiner.py
        file_id = str(get_file_id(file))
        lst_dat = outdir + "dat" + file_id + "_files.lst"
        f = open(lst_dat,'a+')
        f.write("%s\n" %file)
        f = open(lst_dat,'r')
        dlist = f.read().splitlines()
        if len(dlist) > 1:
            dlist = sort_by_blc(dlist)
            f = open(lst_dat,'w')
            for item in dlist:
                f.write("%s\n" %item)
    # erroneous dat_files.lst being made. Not sure why. Let's just delete it.            
    os.remove(outdir + "dat_files.lst")

    return None


# run it!
if __name__ == "__main__":
    main()
