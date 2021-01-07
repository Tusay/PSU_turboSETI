#to combine all targets into a single dat file of hits for plotting purposes

import numpy as np
import glob
import pandas as pd
import os

# ColumnNames seems unnecessary at this point, but will leave it in for now.
ColumnNames = ["HitNum", "Drift_Rate", "SNR", "Uncorrected_Frequency", "Corrected_Frequency", "Index",
    "freq_start", "freq_end", "SEFD", "SEFD_freq", "Coarse_Channel_Number" , "Full_number_of_hits"]

def sort_by_file_id(file_list):
    # look for the observing sequence number in file name
    ids = []
    for file in file_list:
        ids.append(get_file_id(file))
    idx = np.argsort(ids)
    file_list = np.array(file_list)[idx]
    file_list = np.ndarray.tolist(file_list)
    return file_list

def get_file_id(filename):
    return str(str(filename).split("_")[0][-2:])

# remove old dat composites    
print("\nRemoving old dat concats...")
old_files = glob.glob(os.getcwd() + "/*_full.dat")
for file in old_files:
    os.remove(file)
    print("%s has been removed successfully" %file) 

# Open the file list and make it into an array
# NOTE: This requires a pre-made file listing all the .dat files you want to combine
# fil2dat.py should output the requisite dat*.lst files
dat_list = glob.glob("dat*.lst")
dat_list = sort_by_file_id(dat_list)
for file in dat_list:
	full_files = open('dat' + str(get_file_id(file)) + '_files.lst', 'r')
	files_array = full_files.read().splitlines()

	# Name the output file based on the sequence number
	output_file = './hits' + get_file_id(file) + '_full.dat'

	# Read the first .dat file in order to preserve the headers
	original_hits_df = pd.read_csv(files_array[0],index_col=False)

	# This for-loop adds the extra .dat files onto the first one while skipping the headers
	for file in files_array[1:]:
    		addendum_hits_df = pd.read_csv(file.strip(), skiprows=8, index_col=False)
    		frames = [original_hits_df, addendum_hits_df]

	    	# This next line forces the columns to match or else you get weird delimiter issues
    		addendum_hits_df.columns = original_hits_df.columns

	    	# This line adds each .dat file onto the last
    		original_hits_df = pd.concat(frames, ignore_index=True)
    		# print("original file name = " + file)

	# This produces the final hits**_full.dat file for each sequence number
	original_hits_df.to_csv(output_file, index=False)
	print("Merge File ID" + get_file_id(file) + "Complete")

