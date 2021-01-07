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
    return int(filename.split(".")[0][-4:])


def sort_by_file_id(file_list):
    # look for the observing sequence number in file name
    ids = []
    for file in file_list:
        ids.append(get_file_id(file))
    idx = np.argsort(ids)
    file_list = np.array(file_list)[idx]
    file_list = np.ndarray.tolist(file_list)
    return file_list


def find_input_data(indir, zeros_only=True, sort_id=True):
    # find the data first
    if zeros_only:
        file_list = glob.glob(indir + "*0000.fil")
    else:
        file_list = glob.glob(indir + "*.fil")

    # sort by file IDs if true
    assert len(file_list) >= 1
    if sort_id:
        file_list = sort_by_file_id(file_list)

    # TODO: throw out 23 for X2
    # TODO: this is hard-coded for now DONT FORGET DUMMY @MICHAEL
    # only take the X3 on/off pointings
    if "_X3_" in file_list[-2]:
        file_list = file_list[-6:]
    elif "_S_" in file_list[-1]:
        file_list = file_list[-7:-1]

    return file_list


def convert_to_h5(file, outdir="./", clobber=False):
    # check if the file already exists
    pre, ext = os.path.splitext(os.path.basename(file))
    out_file = outdir + pre + ".h5"
    if os.path.isfile(out_file):
        if clobber == False:
            print("\n" + pre + ".h5" + " already exists. Moving on...")
            return out_file
        else:
            os.remove(out_file)

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


def run_find_event_pipeline(datdir, filter_threshold=np.nan, number_in_cadence=np.nan):
    assert filter_threshold != np.nan
    assert number_in_cadence != np.nan

    # get list of files and sort by file ID
    dat_list = glob.glob(datdir + "*.dat")
    dat_list = sort_by_file_id(dat_list)

    # write to .lst, as required by find_event_pipeline
    # TODO: throw out 23 for X3 obs
    lst_dat = datdir + "dat_files.lst"
    if os.path.isfile(lst_dat):
        os.remove(lst_dat)
    with open(lst_dat, 'w') as f:
        for item in dat_list:
            f.write("%s\n" % item)
    assert os.path.isfile(lst_dat)

    # construct csv file name
    csv_name = datdir + "events_f_" + str(filter_threshold) + ".csv"

    # run find_event_pipeline
    print("\nRunning find event pipeline...")
    find_event_pipeline(lst_dat,
                        csv_name=csv_name,
                        filter_threshold=filter_threshold,
                        number_in_cadence=number_in_cadence)
    print("\n")
    return csv_name


def main():
    # parse the command line arguments
    cmd_args = parse_args()

    # get the input data directory
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
        old_files = glob.glob("outdir/*")
        for file in old_files:
            os.remove(file)

    # get appropriate list of .fil files in directory
    fil_list = find_input_data(indir)

    # write .fil files to .lst file for plot_event_pipeline later
    lst_fil = outdir + "fil_files.lst"
    if os.path.isfile(lst_fil):
        os.remove(lst_fil)
    with open(lst_fil, 'w') as f:
        for item in fil_list:
            f.write("%s\n" % item)
    assert os.path.isfile(lst_fil)

    # loop over input files, do reduction to .dat file
    drift_factor = 2.0
    for fil in fil_list:
        # convert filterbank file to HDF5
        outfile = convert_to_h5(fil, outdir=outdir, clobber=clobber)

        # get the drift rate in Hz/s
        print("\nGetting max drift rate...")
        drift_rate = sl.get_drift_for_probe(outfile)
        print("Max drift rate (pre factor) is " + str(drift_rate))
        drift_rate *= drift_factor

        # call FindDoppler
        datfile = run_turbo_seti(outfile,
                                 min_snr=5.0,
                                 outdir=outdir,
                                 clobber=clobber,
                                 max_drift=drift_rate,
                                 gpu_backend=gpu_backend)


    # call run_find_event_pipeline
    filter_threshold = 1
    number_in_cadence = 6
    csv_file = run_find_event_pipeline(outdir,
                                       filter_threshold=filter_threshold,
                                       number_in_cadence=number_in_cadence)

    # now do the plotting
    print("\nRunning plot_event_pipeline...")
    plot_dir = indir + "plots/"
    plot_event_pipeline(csv_file, lst_fil,
                        filter_level=filter_threshold,
                        plot_dir=plot_dir)

    return None


# run it!
if __name__ == "__main__":
    main()
