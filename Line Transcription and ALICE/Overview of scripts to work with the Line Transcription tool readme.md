##  Overview of scripts to work with the Line Transcription tool

The Line transcription tool uses a two step collaborative process: one volunteer marks a section of code with a line drawing, then that volunteer transcribes that portion of text, and then subsequent volunteers edit or re-transcribe the text until the aggregation tool caesar is satisfied there is enough transcriptions of that bit of text whereupon the marking line changes colour.  An additional question is asked if all the text is marked and the line colours indicate the transcription is fully complete.

## Data from the Line transcription tool can be extracted at several points:  

### Using ALICE without the review and approval step.

Ideally the Line transcription tool is used with the ALICE  (Aggregate Line Inspector and Collaborative Editor) to inspect and edit crowd sourced transcriptions after they have reached their retirement limit. 
This link [Transcription viewer/editor help](https://alice.zooniverse.org/about) discusses ALICE in detail.  For this discussion we are primarily dealing with scripts that assist in working with either the Line transcription tool data directly or working with the output of ALICE and very little to do with ALICE itself or how it works.

The final output from ALICE, once the aggregated transcriptions have been reviewed and approved, is a set of files in a group of folders for each zooniverse group_id (subject_set) that has been completed and approved – the best fit or consensus text for each subject is in a separate folder, with a master file listing the metadata for the set.  **Note to obtain this set of folders, the Line transcription data must be reviewed and APPROVED subject by subject via ALICE.   At this time there is no functionality for blanket approval or automating the approval process – every subject must be opened, reviewed and marked as approved, and once that is done can no longer be edited via ALICE.

Some teams wanted the consensus texts extracted from their individual folders and brought into a larger file with various parts of the metadata for each subject in additional column as preparation for uploading to their own data base.  The first script in this repository was for that purpose:

####  [parse_alice_exports_with BOM.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/parse_alice_exports_with%20BOM.py)

This is a generic version of a script written for Documentation Detectives.  It is a simple Python script requiring no additional packages, running a list of parameters. Basically it is given as inputs the top directory path and name for the ALICE output for the subject set, and returns one .csv file with the full consensus text and metadata for each subject in the group.  It does not keep any information as to the level of consensus, the other versions or the positional information for the individual lines of the full text.  It is by listed by subject, though variations of the script exist that sort by items in the subject metadata, such as a natural sort on the “internal_id” field which is a required field for the ALICE tool.  The BOM character placed at the beginning of the output .csv file allows this file to be opened directly in EXCEL with uft-8 encoding, to ensure the correct display of the contents in excel.  Further details are available in the script’s readme file.

### Using the Subject Reductions from caesar for the Line Transcription tool

Effectively this is just using the “A” part of the ALICE tool.  The Subject reducer export is one of the two possible data exports from the caesar setup for the workflow.  It has positional and consensus text information aggregated at the “internal_id” level.  It has, for each line drawn on the subject, a “consensus text” and cluster positional information.  From this it is possible to extract the consensus text line by line and reorder the lines based on their position.  Using this file as input one can effectively obtain the same output as from ALICE without the approval step.   This approach does not correct the output for extraneous lines, incorrect clustering, or errors reconciling the consensus text – you get exactly the same text output as ALICE  shows before review and editing.  Edits made with ALICE are not retained in this output, and there can be some differences in line ordering from what ALICE ends up with depending on how the positional information is processed.
 
Documentation Detectives  wanted their data extracted in the same form as the script above but without the need to review and approve each subject.  The following script was written for this purpose:

####  [flatten_and_parse_caesar_reducers_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/flatten_and_parse_caesar_reducers_generic.py)

This is a generic version of a script written for Documentation Detectives.  It is a simple Python script in its simplest form requiring no additional packages, running a list of parameters. Basically it is given as inputs the top directory path and name for the Subject reducer export as downloaded directly from caesar for the workflow in question, and an accompanying file which links the subject _id with the subject metadata, and returns one .csv file with the full consensus text and metadata for each subject in the Subject reducer export.  The output can be limited to select for a range of zooniverse subjects or by a list of “group_id’s”.  There are also some options for how the lines are ordered based on knowledge of the original subject’s pagination.  A natsort package adds the ability to do a natural sort on any two of the subject metadata fields.  Again a BOM character ensures the file loads with the correct encoding in EXCEL.  Further details are available in the script’s readme file.


### Using the Subject extracts from caesar for the Line Transcription tool

This approach uses the raw responses from the volunteers as extracted by caesar.  The data is effectively the same as the raw data export from the project builder with no aggregation but a somewhat simpler format.  The Subject extracts export is one of the two possible data exports from the caesar setup for the workflow.  It has positional and text information at the “internal_id” level for each classification done by all volunteers that worked on the subject.  It is necessary to extract both positional and text information and 1) cluster or group the texts based on the line positions (ie the aggregation step) and 2) reconcile the differences between the various versions of the same original text segment.   The algorithms used for these steps are NOT THE SAME as used by ALICE.  Indeed this approach was investigated originally to reduce the errors seen in the ALICE data, particularly duplicate lines that should but do not cluster, and errors in reconciliation due to splitting the text on spacing.  At the same time we wanted an easier means of pointing out the variations between volunteers, with an emphasis on showing only those differences, eliminating showing all high consensus options, or simple minor spacing differences.    

The following script successfully does eliminate most of the line duplications found in ALICE outputs, and does at least as well on reconciliation for texts such as Documention Detectives which are heavy on sentence fragments with erratic positional placement on the page.  It may not be any better on text that is line after line of full text across the page - it simply has not been tested sufficiently to know.   Neither this script nor ALICE does a good job of addressing incorrectly drawn lines – ie lines that are misplaced on the subject by the first volunteer that drew them, usually overdrawn or corrected by further volunteers.  These “incorrect lines” usually result in more than one version of certain segments of the text getting through to the final output, despite the fact that often they are identified but at least some volunteers either in the transcribed text with terms such as “incorrect line” or in the subject “Talk” comments.

#### [flatten_and_aggregate_caesar_extracts_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/flatten_and_aggregate_caesar_extracts_generic.py)

This is a generic version of a script written for Documentation Detectives.  It is a somewhat more complex Python script requiring a number of additional packages. It uses fuzzywuzzy and Levenshtein distance for fuzzy string matching, and a customized DBSCAN for positional clustering.  Inputs and outputs are defined by a list of parameters. As inputs it is given the top directory path and name for the Subject extracts export as downloaded directly from caesar for the workflow in question, and an accompanying file which links the subject _id with the subject metadata, and the script returns one .csv file with the full consensus text and metadata for each subject in the Subject extracts export.  The output can be limited to select for a range of zooniverse subjects or by a list of “group_id’s”.  There are also some options for how the lines are ordered based on knowledge of the original subject’s pagination.  A natsort package adds the ability to do a natural sort on any two of the subject metadata fields.  Again a BOM character ensures the file loads with the correct encoding in EXCEL.  

The reconciliation algorithm is entirely different than that used for ALICE.   Basically related text segments are grouped by a positional clustering, the positional clusters are then further split by a fuzzy string matching.  The grouped texts are positionally sorted in one of three ways depending on knowledge of the subject pagination (single page, double page or columns).   Then the related text segments are reconciled in a three step process: 1) remove extreme outliers of unreconcilable text (usually transcribed from an incorrect line, or with added information that does not actually appear in the original text, 2) accept text segments that have a high enough consensus (currently set at 100% but variable) and 3) for the rest, isolate those sections of text that are common and those that differ and take the majority option among the differences.   The consensus text for each line is assembled in order to build the full text for the subject, and for those lines with significant variations, these are collected and the options shown as lists between the common text sections in an additional column in the output.  Outliers and clustering noise (positional segments that did not cluster) are shown in additional columns but experience so far says these can generally be ignored as no value. 

Further details of the parameters and Python environment are available in the script’s readme file.

### Using the data export for the project with the Line Transcription tool

This approach uses the raw responses from the volunteers as recorded in the normal project data export.  It is obtained from the project lab using either the full export or by workflow. The data from a classification has a main task which holds the positional information for the line(s) being transcribed and supplemental tasks with the “details” which is the text entered or accepted.  The script first flattens the file ie extracts both positional and text information in the same format as the Alice Caesar extraction and then the processing from there is identical to the script flatten_and_aggregate_caesar_extracts_generic.py above.
The output of the two approaches is the same for the same parameters, but the data export is somewhat easier to obtain.

#### [flatten_and_aggregate_caesar_extracts_generic.py]( https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/flatten_and_aggregate_from_export_generic.py)


Further details of the parameters and Python environment are available in the script’s readme file.


## Generate a metadata cross-reference from a data export

Neither of the caesar data exports contains the metadata for the zooniverse subjects – the only link is the zooniverse subject number.  Internal_id and group_id are not given in either output.   To link these fields and other metadata it is necessary to extract this information from elsewhere, and pull it into the reconcile text output files.  There are several ways this can be done – from a subject export file, or from a full data export of the raw data from the workflow.   Of these two sources, the data export is by far larger and more cumbersome to work with but has the advantage that every subject ever classified will be in the export and as well we can obtain other information not in the subject export - specifically image width which is needed to scale the clustering algorithms appropriately.  

#### [generate_metadata_x_ref_from_data_export_generic.py](https://github.com/PmasonFF/Zooniverse-data-digging/blob/master/Line%20Transcription%20and%20ALICE/generate_metadata_x_ref_from_data_export_generic.py)

So this script uses a full data export or a workflow classification export to obtain a list of all the zooniverse subject_ids, their metadata, and raw image width for a given workflow.  For most projects the number of subjects is not so large that this file is consumes too much memory, but if that were the case a minor change to the selection logic in line 24 could be added to restrict the output to a range of subject_ids.  As written it acquires all the subjects classified in the workflow specified in the parameters.

The version in this repository acquires both metadata field’s group_id, and internal_id which are required fields for a line transcription tool to be used with ALICE.  It also extracts the raw image width.   Additional metadata fields can be extracted but adding code blocks as indicated in the script in line 38: 

try:  
     output_row["field_name"] = subject_metadata_["field_name”]
 except KeyError:
     output_row["field_name"] = ''

Also add the additional field_names to the list of output fields in line 13

It would be very easy to modify this script to extract the metadata for any set of subjects in a more general usage.

Further details of the parameters and Python environment are available in the script’s readme file.




