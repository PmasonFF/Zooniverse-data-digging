### [parse_alice_exports_with BOM.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/parse_alice_exports_with%20BOM.py)

This is a generic version of a script written for Documentation Detectives.  It is a simple Python script requiring no additional packages, running a list of parameters. Basically it is given as inputs the top directory path and name for the ALICE output for the subject set, and returns one .csv file with the full consensus text and metadata for each subject in the ALICE group.  It does not keep any information as to the level of consensus, the other versions or the positional information for the individual lines of the full text.  It is by listed by subject, though variations of the script exist that sort by items in the subject metadata, such as a natural sort on the “internal_id” field which is a required field for the ALICE tool.  The BOM character placed at the beginning of the output .csv file allows this file to be opened directly in EXCEL with uft-8 encoding, to ensure the correct display of the contents in excel.

#### Environment:

Recommend Python 3.9 or later though any python 3+ should work.

No additional packages needed beyond built-in modules

#### Inputs:

The complete set of files and folders for a completed approved ALICE output: This is generally the transcriptions_metadata.csv file and the set of folders “transcription_XXXXXXXX” where XXXXXXXX is one of the subject numbers in the group.  
The path and file name of the transcriptions_metadata.csv file are given as parameters.

#### Parameter help:

usage: parse_alice_exports_with BOM.py [-h] [-d DIRECTORY] [-f FILE]

The first step is to define the input file and path for the 
transcriptions_metadata using parameters.  This is done by giving 
the script two parameters, 1) a working directory path where the 
transcriptions_metadata, the individual transcription directories 
by subject, and the output file will reside, and 2) the name of 
the transcriptions_metadata.csv file if it is not the default. 

options:

  -h, --help            show this help message and exit
  
  -d DIRECTORY, --directory DIRECTORY
                        The path and directory where the input and output
                        files, are located. It defaults to the directory where
                        this script is running. example '-d
                        C:\py\BMT_collections'
                        
  -f FILE, --file FILE  The transcriptions_metadata.csv file to parse. It must
                        be in the working directory and contain a column
                        'transcription id' which is the zooniverse subject
                        number, and a column 'internal id' which is the BMT
                        Collection's object number. The output file will have
                        the same name as the transcriptions_metadata input
                        file with "_parsed" added prior to the file extension.
                        example: "-f transcriptions_metadata.csv"

Example: -d C:\py\BMT_collections\15052024_fine_art_1945_export -f transcriptions_metadata.csv

#### Output:

One csv filefor the entire set with the following columns:
“transcription_id”, “internal_id”, and “consensus_text”


transcription_id - is also the zooniverse subject_id

internal_id - a required metadata field for the ALICE tool

consensus_id - The entire text block for each subject in the group.
