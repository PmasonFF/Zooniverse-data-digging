### [generate_metadata_x_ref_from_data_export_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/generate_metadata_x_ref_from_data_export_generic.py)

Neither of the caesar data exports contains the metadata for the zooniverse subjects – the only link is the zooniverse subject number.  Internal_id and group_id are not given in either output.   To link these fields and other metadata it is necessary to extract this information from elsewhere, and pull it into the reconcile text output files.  There are several ways this can be done – from a subject export file, or from a full data export of the raw data from the workflow.   Of these two sources, the data export is by far larger and more cumbersome to work with but has the advantage that every subject ever classified will be in the export and as well we can obtain other information not in the subject export - specifically image width which is needed to scale the clustering algorithms appropriately.  

So this script uses a full data export or a workflow classification export to obtain a list of all the zooniverse subject_ids, their metadata, and raw image width for a given workflow.  For most projects the number of subjects is not so large that this file is consumes too much memory, but if that were the case a minor change to the selection logic in line 24 could be added to restrict the output to a range of subject_ids.  As written it acquires all the subjects classified in the workflow specified in the parameters.

The version in this repository acquires both metadata field’s group_id, and internal_id which are required fields for a line transcription tool to be used with ALICE.  It also extracts the raw image width.   Additional metadata fields can be extracted but adding code blocks as indicated in the script in line 38: 

````
try:  
     output_row["field_name"] = subject_metadata_["field_name”]
 except KeyError:
     output_row["field_name"] = ''
````

Also add the additional field_names to the list of output fields in line 13

It would be very easy to modify this script to extract the metadata for any set of subjects in a more general usage.
 

#### Environment:

Recommend Python 3.9 or later though any python 3+ should work.

No additional packages needed beyond built-in modules

#### Inputs:

The project data export.csv file - either the full data export or the required workflow classifications downloaded via the project builder.  This file must be from an export that is known to include all the subjects that may appear in the corresponding caesar data downloads.

The workflow_id for the Line transcription workflow and caesar set-up of interest.
	

#### Parameter help:

usage: generate_metadata_x_ref_from_data_export.py [-h] [-d DIRECTORY]
                                                   [-s DATA_EXPORT]
                                                   [-w WORKFLOW]

The first step is to define the input file and path for the 
data_export using parameters.  This is done by giving 
the script two parameters, one a working directory path where the 
subject export used to build the x_ref, and the output file will 
reside, and two, the id of the workflow the x-ref will include. 

options:

  -h, --help            show this help message and exit
  
  -d DIRECTORY, --directory DIRECTORY
                        The path and directory where the input and output
                        files, are located. It defaults to the directory where
                        this script is running. example '-d
                        C:\py\BMT_collections'
                        
  -f DATA_EXPORT, --data_export DATA_EXPORT
                        The project data export.csv file which is used to
                        generate a cross-reference between the zooniverse
                        subject id and the subject metadata. It must be in the
                        working directory and is either the full data export
                        or classifications by workflow downloaded via the
                        project builder. example: "-f transcribing-birmingham-
                        museums-accession-registers-classifications.csv"
                        
  -w WORKFLOW, --workflow WORKFLOW
                        The transcription based workflow_id that is to be
                      		parsed. example: "-w 25224

Example: -d C:\py\BMT_collections -f transcribing-birmingham-museums-handwritten-accession-registers-classifications.csv -w 26197

#### Output:

One .csv file named "metadata_crossreference_XXXXXX.csv” where XXXXXX is the workflow_id of interest.  The file has at least the following columns:

subject_id, group_id, internal_id, image_width

and can have additional metadata fields if these have been added to the script as indicated above.



