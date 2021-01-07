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
from find_event_pipeline_piecemeal import find_event_pipeline
from plot_event_pipeline_piecemeal import plot_event_pipeline

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


def sort_by_file_id(file_list):
    # look for the observing sequence number in file name
    ids = []
    for file in file_list:
        ids.append(get_file_id(file))
    idx = np.argsort(ids)
    file_list = np.array(file_list)[idx]
    file_list = np.ndarray.tolist(file_list)
    return file_list


# def find_input_data(indir, zeros_only=True, sort_id=True):
#     # find the data first
#     if zeros_only:
#         file_list = glob.glob(indir + "*0000.fil")
#     else:
#         file_list = glob.glob(indir + "*.fil")

#     # sort by file IDs if true
#     assert len(file_list) >= 1
#     if sort_id:
#         file_list = sort_by_file_id(file_list)

#     # TODO: throw out 23 for X2
#     # TODO: this is hard-coded for now DONT FORGET DUMMY @MICHAEL
#     # only take the X3 on/off pointings
#     if "_X3_" in file_list[-2]:
#         file_list = file_list[-6:]
#     elif "_S_" in file_list[-1]:
#         file_list = file_list[-7:-1]

#     return file_list
    


def run_find_event_pipeline(datdir, SNR, filter_threshold=np.nan, number_in_cadence=np.nan):
    assert filter_threshold != np.nan
    assert number_in_cadence != np.nan
    #get list of files and sort by file ID
    dat_list = glob.glob(datdir + "*_full.dat")
    dat_list = sort_by_file_id(dat_list)
    # write to .lst, as required by find_event_pipeline
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
                        datdir,
                        SNR_cut=SNR, 
                        check_zero_drift=False, 
                        csv_name=csv_name,
                        filter_threshold=filter_threshold,
                        number_in_cadence=number_in_cadence)
    print("\n")
    return csv_name


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
    # if not os.path.isdir(outdir):
    #     os.mkdir(outdir)

    # get appropriate list of .fil files in directory
    # fil_list = find_input_data(indir)

    # write .fil files to .lst file for plot_event_pipeline later
    # lst_fil = outdir + "fil_files.lst"
    # with open(lst_fil, 'w') as f:
    #     for item in fil_list:
    #         f.write("%s\n" % item)
    # assert os.path.isfile(lst_fil)



    # call run_find_event_pipeline and make csv file
    SNR = 10
    filter_threshold = 1
    number_in_cadence = 3
    csv_file = run_find_event_pipeline(outdir,
                                       SNR,
                                       filter_threshold=filter_threshold,
                                       number_in_cadence=number_in_cadence)

    lst_fil = outdir + 'fil_files.lst'

    # now do the plotting
    # cross-reference the csv file above with the fil list in lst_fil
    print("\nRunning plot_event_pipeline...")
    plot_dir = outdir + "f" + str(filter_threshold) + "_plots/"
    plot_event_pipeline(csv_file, 
                        lst_fil,
                        plot_dir)

    return None


# run it!
if __name__ == "__main__":
    main()
