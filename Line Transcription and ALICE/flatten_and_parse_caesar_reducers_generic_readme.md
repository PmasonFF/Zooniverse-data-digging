###  [flatten_and_parse_caesar_reducers_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/flatten_and_parse_caesar_reducers_generic.py)

Effectively this script allows us to use just the “A” part of the ALICE tool.  The Subject reducer export is one of the two possible data exports from the Caesar setup for the workflow.  It has positional and consensus text information aggregated at the “internal_id” level.  It has, for each line drawn on the subject, a “consensus text” and cluster positional information.  From this it is possible to extract the consensus text line by line and reorder the lines based on their position.  Using this file as input one can effectively obtain the same output as from ALICE without the approval step.   This approach does not correct the output for extraneous lines, incorrect clustering, or errors reconciling the consensus text – you get exactly the same text output as ALICE  shows before review and editing.  Edits made with ALICE are not retained in this output, and there can be some differences in line ordering from what ALICE ends up with depending on how the positional information is processed.
 
Documentation Detectives  wanted their data extracted in the same form as ALICE but without the need to review and approve each subject.  This script was written for this purpose.

This is a simple Python script in its simplest form requiring no additional packages, running a list of parameters. Basically it is given as inputs the top directory path and name for the Subject reducer export as downloaded directly from caesar for the workflow in question, and an accompanying file which links the subject _id with the subject metadata, and returns one .csv file with the full consensus text and metadata for each subject in the Subject reducer export.  The output can be limited to select for a range of zooniverse subjects or by a list of “group_id’s”.  There are also some options for how the lines are ordered based on knowledge of the original subject’s pagination.  A natsort package adds the ability to do a natural sort on any two of the subject metadata fields.  Again a BOM character ensures the file loads with the correct encoding in EXCEL. 

#### Environment:

Recommend Python 3.9 or later though any python 3.8+ should work.

The version in this repository requires on additional package beyond the normal built-in modules to sort the output using a natural sort.  Very minor changes to use the built-in Python sort obviates the need for this package (use “sorted” in place of “natsorted” in lines 429, 241, 246, 247.)

natsort – version 8.4+   https://github.com/SethMMorton/natsort

It can be installed with pip in its simplest form

$ pip install natsort
 

#### Inputs:

The subject_reducer export.csv file to parse. This is a copy of the caesar reductions as requested and downloaded from the caesar data requests for the workflow in question. This is generally renamed to Subject_reducer_export_XXXXXX.csv where "XXXXXX" is the workflow-id.

 In addition to this file a cross-reference between the zoonivere subject numbers and the subject metadata is required. This filer can be produced from a workflow data export requested through the project builder using the script "generate_metadata_x_ref_from_data_export.py".  Generally it will be called "metadata_crossreference_XXXXXX.csv where XXXXXX" is the workflow_id.

Additional inputs can be used to limit the output to specified subject_id ranges, or a list of group_ids, and the line order can be somewhat adjusted with two additional parameters ( see below).   

#### Parameter help:

usage: flatten_and_parse_caesar_reducers_generic.py [-h] [-d DIRECTORY]
                                                    [-f FILE] [-x XREFERENCE]
                                                    [-w WORKFLOW] [-l LIMITS]
                                                    [-p PAGINATION]
                                                    [-s WIDTH_TO_LINE_RATIO]

The first step is to define the input files and path for the subject 
reducer export file using parameters. This is done by giving the 
script two parameters, 1) a working directory path where the subject 
reducer export file, the cross reference to the metadata and the 
output file will reside, and 2) the name of the subject_reducer.csv 
file if it is not renamed to the default name 
"Subject_reducer_export_XXXXXX.csv where "XXXXXXX" is the workflow-id. 

Then define the workflow_id and the name of the metadata cross reference 
file if it has not been named the default 
"metadata_crossreference_[workflow_id].csv".

Finally various limits to the output may be defined:  The default is 
"all", where all available records will be output, option 1)is a upper 
and lower limit for subject_ids to be included, and option 2)is a list 
of the group_id's to be included. 

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        The path and directory where the input and output
                        files, are located. It defaults to the directory where
                        this script is running. example '-d
                        C:\py\BMT_collections'
  -f FILE, --file FILE  The subject_reducer export.csv file to parse. It must
                        be in the working directory. This is a copy of the
                        caesar reductions as requested and downloaded from the
                        caesar data requests for the workflow in question. The
                        output files will have the same name as the
                        subject_reducer input file with "_sorted" added prior
                        to the file extension. Generally the reducer export
                        file should be renamed to
                        "Subject_reducer_export_XXXXXX.csv where "XXXXXXX" is
                        the workflow-id. If this is done, this parameter is
                        optional. example: "-f
                        Subject_reducer_export_26197.csv"
  -x XREFERENCE, --xreference XREFERENCE
                        The metadata_crossreference_[workflow_id].csv file. It
                        must be in the working directory. This is a cross
                        reference between the zooniverse subject number and
                        the subject metadata. It is produced from a workflow
                        data export requested through the project builder
                        using the script
                        "generate_metadata_x_ref_from_data_export.py".
                        Generally it will be called
                        "metadata_crossreference_XXXXXX.csv where XXXXXXX" is
                        the workflow_id, in which case this parameter is
                        optional. The cross reference must have at least four
                        columns: subject_id, internal_id, group_id, and
                        image_width, and may have others. example: "-x
                        metadata_crossreference_25224.csv"
  -w WORKFLOW, --workflow WORKFLOW
                        The transcription based workflow_id that is to be
                        parsed. This is a required field and is used to
                        generate the default names for the input files.
                        example: "-w 25224"
  -l LIMITS, --limits LIMITS
                        This parameter is used to limit the output to selected
                        ranges of zooniverse subject_id or group_id's. The
                        default is for all records in the subject reductions,
                        but in general unless all the data is complete at the
                        time the reductions were exported, some form of limits
                        need to be given. There are two options: 1) A range of
                        subject_ids to include - two integers in any order
                        being the upper and lower limits of the range of
                        subject id's to be included.l example: "-l
                        1000;103000000" This would effectively include any
                        subject_id less than 103000000. Note use of semicolon
                        and no spaces. 2) A list of group_id's to include.
                        These must listed EXACTLY as the group_id given in the
                        subject metadata. The easiest way to create the list
                        is to copy and paste from the metadata cross reference
                        file, though the group_id can be obtained from the
                        project lab for a subject set by looking at the
                        metadata of an included subject. example 1: "-l
                        archaeology_and_folk_life_1962" example 2: "-l archaeo
                        logy_and_folk_life_1961;archaeology_and_folk_life_1962
                        " Note use of semicolon and no spaces.
  -p PAGINATION, --pagination PAGINATION
                        This parameter is used to adjust the sorting of the
                        consensus text into pages. Currently there are three
                        options, the default assumes double pages and places
                        lines beginning 45% of the image width from the left
                        into Page 2, separated from Page 1 lines by two empty
                        lines. This option also works fine for single page
                        images where lines all begin at the left margin.
                        Single page can be forced using a value "single" and a
                        special formatting for Birmingham Museum Trust can be
                        selected using a value "bmt". The latter may be useful
                        where the text is in rough columns with multiple
                        segments spread across the page. All versions add a
                        horizontal sort for line segments that are nearly at
                        the same vertical position, listing them from left to
                        right for each page. example: "-p single"
  -s WIDTH_TO_LINE_RATIO, --width_to_line_ratio WIDTH_TO_LINE_RATIO
                        This parameter is used to adjust the sorting and
                        display of the consensus text into pages. In this
                        script using the subject reductions. It DOES NOT
                        affect the clustering of text lines. It is not
                        directly the line height which may vary from subject
                        to subject depending on how the material was scanned.
                        To estimate a reasonable number, divide the width of a
                        typical subject image in pixels by the pixel height of
                        an average line of text in that image. Hopefully this
                        ratio is consistent across subjects which have been
                        scanned similarly but possibly resized variable
                        amounts for uploading. If this number as selected is
                        too small or too large the order that the consensus
                        text is listed may be less than desirable. Scans which
                        are narrower in width relative to the line height need
                        a smaller number. Text that is spread out in width
                        relative to line height need a larger number. example:
                        "-s 40"

Example 1): -d C:\py\BMT_collections -f Subject_reducer_export_25224.csv -x metadata_crossreference_25224.csv -w 25224 -l archaeology_and_folk_life_1961;archaeology_and_folk_life_1962 -p bmt -s 40

Example 2): -d C:\py\BMT_collections -w 25224  (using the default names for the subject reducer file, cross-reference, all records, and the default values for pagination and width to line ratio.)

#### Output:
One csv file for the entire set with the following columns:
“subject_id”, “group_id”, “internal_id”, “ image_width”, “workflow_id”, and “transcription_text”, plus other possible metadata fields.

The output file is sorted with a natural sort on first the internal_id and then group_id.

An initial BOM character ensures the file loads with the correct encoding in EXCEL. 




