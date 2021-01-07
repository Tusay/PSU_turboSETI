These are the files I have made/used for a more general application of turboSETI on the PSU cluster.

fil2dat.py converts filterbank ".fil" files into ".h5," ".dat," and ".log" files. It will also output a "fil_files.lst" file with a list of all the corresponding filterbank ".fil" files that it worked on. It requires in input directory argument when run to tell it where the ".fil" files are stored. The output files are placed in a folder labeled "processed" in the input directory. 

FileCombiner.py must be run in the output "processed" directory where all the ".dat" files are. This concatenates all the dats with the same ID number in their filename into a single ".dat" file. It also produces a ".lst" file listing all the ".dat" files that it combined and sorts them by "blc" number in each filename.

hits.py runs the combined ".dat" files through turboSETI's find_event_pipeline and returns a pared down ".csv" file with the hits based on the filter_threshold. It then creates plots of the hits in the list and outputs the plots in a newly created plot folder within the output "processed" directory.
