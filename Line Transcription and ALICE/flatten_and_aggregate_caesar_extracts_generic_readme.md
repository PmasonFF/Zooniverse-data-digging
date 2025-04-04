### [flatten_and_aggregate_caesar_extracts_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/flatten_and_aggregate_caesar_extracts_generic.py)

This script uses the raw responses from the volunteers as extracted by caesar.  The data is effectively the same as the raw data export from the project builder with no aggregation but a somewhat simpler format.  The Subject extracts export is one of the two possible data exports from the caesar setup for the workflow.  It has positional and text information at the “internal_id” level for each classification done by all volunteers that worked on the subject.  It is necessary to extract both positional and text information and 1) cluster or group the texts based on the line positions (ie the aggregation step) and 2) reconcile the differences between the various versions of the same original text segment.   The algorithms used for these steps are NOT THE SAME as used by ALICE.  Indeed this approach was investigated originally to reduce the errors seen in the ALICE data, particularly duplicate lines that should but do not cluster, and errors in reconciliation due to splitting the text on spacing.  At the same time we wanted an easier means of pointing out the variations between volunteers, with an emphasis on showing only those differences, eliminating showing all high consensus options, or simple minor spacing differences.    

The following script successfully does eliminate most of the line duplications found in ALICE outputs, and does at least as well on reconciliation for texts such as Documention Detectives which are heavy on sentence fragments with erratic positional placement on the page.  It may not be any better on text that is line after line of full text across the page - it simply has not been tested sufficiently to know.   Neither this script nor ALICE does a good job of addressing incorrectly drawn lines – ie lines that are misplaced on the subject by the first volunteer that drew them, usually overdrawn or corrected by further volunteers.  These “incorrect lines” usually result in more than one version of certain segments of the text getting through to the final output, despite the fact that often they are identified but at least some volunteers either in the transcribed text with terms such as “incorrect line” or in the subject “Talk” comments.


The script in this repository is a generic version of a script written for Documentation Detectives.  It is a somewhat more complex Python script requiring a number of additional packages. It uses fuzzywuzzy and Levenshtein distance for fuzzy string matching, and a customized DBSCAN for positional clustering.  Inputs and outputs are defined by a list of parameters. Basically it is given as inputs, the top directory path and name for the Subject extracts export as downloaded directly from caesar for the workflow in question, and an accompanying file which links the subject _id with the subject metadata, and the script returns one .csv file with the full consensus text and metadata for each subject in the Subject extracts export.  The output can be limited to select for a range of zooniverse subjects or by a list of “group_id’s”.  There are also some options for how the lines are ordered based on knowledge of the original subject’s pagination.  A natsort package adds the ability to do a natural sort on any two of the subject metadata fields.  Again a BOM character ensures the file loads with the correct encoding in EXCEL.  

The reconciliation algorithm is entirely different than that used for ALICE.   Basically related text segments are groups by a positional clustering, the positional clusters are then further split by a fuzzy string matching.  The grouped texts are positionally sorted in one of three ways depending on knowledge of the subject pagination (single page, double page or columns).   Then the related text segments are reconciled in three step process: 1) remove extreme outliers of unreconcilable text (usually transcribed from an incorrect line, or with added information that does not actually appear in the original text, 2) accept text segments that have a high enough consensus (currently set at 100% but variable) and 3) for the rest, isolate those sections of text that are common and those that differ and take the majority option among the differences.   The consensus text for each line is assembled in order to build the full text for the subject, and for those lines with significant variations, these are collected and the options shown as lists between the common text sections in an additional column in the output.  Outliers and clustering noise (positional segments that did not cluster) are shown in additional columns but experience so far says these can generally be ignored as no value. 

#### Environment:
Recommend Python 3.9 or later  (package versions and base Python need be compatible)

The script requires several additional packages beyond the normal built-in modules.

fuzzywuzzy – version 0.18.0   https://pypi.org/project/fuzzywuzzy/

numpy – version 1.23.3 or later   https://pypi.org/project/numpy/

python- Levenshtein – version 0.26.1  https://pypi.org/project/python-Levenshtein/

natsort – version 8.4+  https://pypi.org/project/natsort/

In addition to these packages, copies of the two modules below need to be in the directory where the script is run from:

line_scan.py – a modified DBSCAN used to cluster the positional lines.  The nearness metric is modified to be less critical for x position (line start point) than for y position, and returns the mean position of the cluster, as well as the clustered texts.

wordcan.py – a string clustering algorithm using Levenstein distance as a nearness metric.  It is used to group and separate texts that clustered positionally but should be reconciled separately. 


#### Inputs:
The subject_extracts export.csv file to parse. This is a copy of the  caesar extracts as requested and downloaded from the caesar data requests for the workflow in question. This is generally renamed to Subject_extract_export_XXXXXX.csv where "XXXXXX" is the workflow-id.

 In addition to this file a cross-reference between the zoonivere subject numbers and the subject metadata is required. This filer can be produced from a workflow data export requested through the project builder using the script "generate_metadata_x_ref_from_data_export.py".  Generally it will be called "metadata_crossreference_XXXXXX.csv where XXXXXX" is the workflow_id.

Additional inputs can be used to limit the output to specified subject_id ranges, or a list of group_ids, and the line order can be somewhat adjusted with two additional parameters ( see below).   

#### Parameter help:
````
usage: flatten_and_aggregate_caesar_extracts_generic.py [-h] [-d DIRECTORY]
                                                        [-f FILE]
                                                        [-x XREFERENCE]
                                                        [-w WORKFLOW]
                                                        [-l LIMITS]
                                                        [-p PAGINATION]
                                                        [-r WIDTH_TO_LINE_RATIO]

The first step is to define the input files and path for the 
subject extracts file using parameters. This is done by giving the 
script two parameters, 1) a working directory path where the 
subject extracts file, the cross reference to the metadata and 
the output file will reside, and 2) the name of 
the subject_extracts.csv file if it is not the default name 
"Subject_extracts_XXXXXX.csv where "XXXXXXX" is the workflow-id.

Then the workflow_id and the name of the metadata cross reference 
file if it is not the default "metadata_crossreference_[workflow_id].csv".
Finally various limits to the output may be defined:  The default is "all",
where all available records will be output, option one is a upper and 
lower limit for subject_ids to be included, and option two is a 
list of the group_id's to be included. 

options:
  -h, --help            show this help message and exit
  -d DIRECTORY, --directory DIRECTORY
                        The path and directory where the input and output
                        files, are located. It defaults to the directory where
                        this script is running. example '-d
                        C:\py\BMT_collections'
  -f FILE, --file FILE  The subject_extracts.csv file to parse. It must be in
                        the working directory. This is a copy of the caesar
                        extracts as requested and downloaded from the caesar
                        data requests for the workflow. The output files will
                        have the same name as the subject_extracts input file
                        with either "_sorted", (the flattened data) or
                        "aggregated_sorted" (the aggregated and reconciled
                        data) added prior to the file extension. Generally the
                        extracts file should be renamed to
                        "Subject_extracts_XXXXXX.csv where "XXXXXXX" is the
                        workflow-id, in which case this parameter is optional.
                        example: "-f Subject_extracts_26197.csv"
  -x XREFERENCE, --xreference XREFERENCE
                        The metadata_crossreference_[workflow_id].csv file. It
                        must be in the working directory. This is a cross
                        reference between the zooniverse subject number and
                        the subject metadata. It is produced from a workflow
                        data export requested through the project builder
                        using the script
                        "generate_metadata_x_ref_from_data_export.py".
                        Generally it will be called
                        "metadata_crossreference_XXXXXX.csv where "XXXXXXX" is
                        the workflow_id, in which case this parameter is
                        optional. example: "-x
                        metadata_crossreference_25224.csv"
  -w WORKFLOW, --workflow WORKFLOW
                        The transcription based workflow_id that is to be
                        parsed. This is a required field and is used to
                        generate the default names for the input files.
                        example: '-w 25224'
  -l LIMITS, --limits LIMITS
                        This parameter is used to limit the output to selected
                        ranges of zooniverse subject_id or group_id's. The
                        default is for all records in the subject extracts,
                        but in general unless all the data is complete at the
                        time the extracts were exported, some form of limits
                        need to be given. There are two options: 1) A range of
                        subject_ids to include - two integers in any order
                        representing the upper and lower limits of the range
                        of id's to be included example: "-l 1000;103000000"
                        This would effectively include any subject_id less
                        than 103000000. Note use of semicolon and no spaces 2)
                        A list of group_id's to include. These must listed
                        EXACTLY as the group_id given in the subject metadata.
                        The easiest way to create the list is to copy and
                        paste from the metadata cross reference file, though
                        the group_id can be obtained from the project lab for
                        a subject set by looking at the metadata of an
                        included subject. example 1: "-l
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
                        special formatting for Birimingham Museum Trust can be
                        selected using a value "bmt". The latter may be useful
                        where the text is in rough columns with multiple
                        segments spread across the page. All versions add a
                        horizontal sort for line segments that are nearly at
                        the same vertical position, listing them from left to
                        right for each page. example: "-p single"
  -r WIDTH_TO_LINE_RATIO, --width_to_line_ratio WIDTH_TO_LINE_RATIO
                        This parameter is used to adjust the clustering of
                        drawn lines to aggregate correlated text. This value
                        may vary from register to register depending on the
                        typeset, hand writing, paper or journal size, and how
                        the material was scanned. To estimate a reasonable
                        number, divide the width of a scanned cropped subject
                        in pixels by the pixel height of an average line of
                        text in the image. If this number as selected is too
                        large, lines that should NOT be aggregated together
                        will be, though there is a second step that would then
                        separate the lines IF the text in the two lines is
                        dissimilar. If the value is too small, then lines that
                        should aggregate together may end up being reconciled
                        separately adding additional near identical lines of
                        text. Much of the handwritten entries have been
                        resolved with a value of 26 while the typewritten work
                        may require a larger number. Scans which are narrower
                        in width relative to the line height need smaller
                        number. Text that is spread out in width relative to
                        line height need a larger number. example: "-r 40"
````


Example 1): -d C:\py\BMT_collections -f Subject_extracts_export_25224.csv -x metadata_crossreference_25224.csv -w 25224 -l archaeology_and_folk_life_1961 -p bmt -r 40

Example 2): -d C:\py\BMT_collections -w 26197 -r 26 -l 1000;104000000

(using the default names for the subject extracts file, cross-reference, subjects in range 1000 - 104000000, the default values for pagination and 26 as the width to line ratio.)


#### Output:
As written there are two output files:

The first .csv file will be named as the subject extracts file with limit parameter and the words “_sorted.csv” added.  It will have the following columns:

“subject_id”, “workflow_id”, and “transcription_list

This file is sorted on zooniverse subject_id and shows the positional info and text for each classification done.  The position info is the leftmost x value and the midpoint y value for each line drawn, and the text is the transcribed response with the following symbols replacing the text modifiers:

[deletion]' - '˄', [/deletion]' - '˄'

[insertion]' - '˅', [/insertion]' - '˅'

[unclear]' - '‽', '[/unclear]' - '‽'

[underline]' - 'µ' '[/underline]' - 'µ'


The second .csv file will be named as above with the words “_sorted.csv” replaced by “_reconciled.csv”.  It will have the following columns:

“subject_id”, “group_id”, “internal_id”, , plus other possible metadata fields, then  “text_format”, “differences”, “outliers”, and “noise”.

This output file is sorted with a natural sort on first the internal_id and then group_id.

text_format  - this column shows the complete reconciled text for the subject with the line order based on the pagination parameter.  It is the best estimate of the actual text.

differences – this column shows only those lines were there was less than 100% similarity between responses for the same line, with blocks of the text common to all separated by lists of the individual responses that differ.

outliers – this column shows any responses for a line where the response is so different from the rest of the responses for that line that no attempt was made to reconcile the large number of differences.  Most entries here will be transcription of other lines reported incorrectly, partial or incomplete transcriptions, or those with extraneous content which did not appear in the original.

noise – this column contains the responses where the positional information was so far from any other line that the line did not cluster with any other line.  Almost always incorrectly drawn lines, or lines drawn, then dragged off the image instead of being deleted.

While the outliers and noise are retained and displayed, these columns seldom contain useful text.   On the other hand, the differences column is very useful for reviewing and correcting the main text, particularly in the cases where the responses for each version where evenly split and the algorithm selected the incorrect one.

Note that text versions which differ by being absent or missing are shown as the null symbol in the differences list “ø”. Simple differences in spacing are NOT shown (with the reconciled text defaulting to the minimum number of spaces common to all responses).  

 If there are many instances of lines in the text_format column that are duplicated, check the width-to-line-ration is not too large resulting in lines that should cluster being repeated.  By “duplicated” I do not mean some line split in parts with the parts showing separately on other lines, but rather full lines repeated.  Split lines normally occur as a result of someone drawing multiple short lines under the text while someone else drew one longer line – this script does not test or correct for this condition (nor does ALICE). 



The second .csv file will be named as above with the words “_sorted.csv” replaced by “_reconciled.csv”.  It will have the following columns:

“subject_id”, “group_id”, “internal_id”, , plus other possible metadata fields, then  “text_format”, “differences”, “outliers”, and “noise”.

This output file is sorted with a natural sort on first the internal_id and then group_id.

text_format  - this column shows the complete reconciled text for the subject with the line order based on the pagination parameter.  It is the best estimate of the actual text.

differences – this column shows only those lines were there was less than 100% similarity between responses for the same line, with blocks of the text common to all separated by lists of the individual responses that differ.

outliers – this column shows any responses for a line where the response is so different from the rest of the responses for that line that no attempt was made to reconcile the large number of differences.  Most entries here will be transcription of other lines reported incorrectly, partial or incomplete transcriptions, or those with extraneous content which did not appear in the original.

noise – this column contains the responses where the positional information was so far from any other line that the line did not cluster with any other line.  Almost always incorrectly drawn lines, or lines drawn, then dragged off the image instead of being deleted.

While the outliers and noise are retained and displayed, these columns seldom contain useful text.   On the other hand, the differences column is very useful for reviewing and correcting the main text, particularly in the cases where the responses for each version where evenly split and the algorithm selected the incorrect one.

Note that text versions which differ by being absent or missing are shown as the null symbol in the differences list “ø”. Simple differences in spacing are NOT shown (with the reconciled text defaulting to the minimum number of spaces common to all responses).  

 If there are many instances of lines in the text_format column that are duplicated, check the width-to-line-ration is not too large resulting in lines that should cluster being repeated.  By “duplicated” I do not mean some line split in parts with the parts showing separately on other lines, but rather full lines repeated.  Split lines normally occur as a result of someone drawing multiple short lines under the text while someone else drew one longer line – this script does not test or correct for this condition (nor does ALICE). 
