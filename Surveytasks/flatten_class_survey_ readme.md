# Survey tasks:

In the Classification download, the user's responses to each task are recorded in a field called 'annotations' (including those of experts and those tagged "TRUE" for being gold standard responses. The field is a JSON string. When loaded into Python using the json.loads() function from import json it becomes a dictionary of dictionaries of form {{....}, {.....}, {....}} with a dictionary for each task the user is required to complete, in the order completed.

The form of the individual dictionaries for the tasks depends very much on what type of task it is - a question, drawing tool, transcription or survey task.

This set of scripts is for a generic survey task. It can be combined with task blocks for other task types – see the other task building block scripts.  To interpret the questions and structure the output files, we need to know all about the project details - fortunately most of what we need to know is conveniently summarized in the questions.csv file used to build the project. With a copy of that file included in the file locations list, most of the heavy lifting for the details is done.  

This script will flatten the classification file so the responses are shown in a neat column format with one column per question.  It will aggregate the results showing the vote fraction for each possible response for each species reports for each subject.  There will be one line for each subject-choice reported.  The aggregated output is not intended for direct Human readability, but it is then filtered to determine consensus based on gates input into the script, as described below.  The filtered output shows the results for those subject-choices that meet the minimum limit of consensus, and those subjects that remain indeterminate for one of several reasons.  Finally as an option, those subjects which are not resolved by consensus can be added to a new subject set which can then be linked to the existing workflow or a customized workflow for further review using zooniverse.

In order for the script to connect with and log on to zooniverse the username and password of a project collaborator must be available to the script.  There are various ways of providing this

–	The worst way is to simply hardcode it in lines 647,648 which is not secure since the password is clearly visible to anyone with the script.

–	Using an interactive input every time it is needed (this is not convenient and unfortunately this echos the password to the screen and is not secure against shoulder surfers).

–	The username and password can be set up as environmental variables in the OS – this is only as secure as Admin privileges on your computer since the environmental variables are stored in plain text.

–	The last way as used in this script is to collect the username and password once using an interactive input , then encrypt it and store it in a file in the working directory.  To this end there is a small script run_config.py that must be placed in the same directory as this survey task script.  The first time the survey task script runs it will call run_config.py which will generate a new encryption key (which will be stored in run_config.py) and allow you to generate a new file run_config.csv that will store your encrypted password and some other details.  Note that anyone with **both** the current file run_config.csv  and the version of run_config.py that produced it can generate the password in plain text, but both of the matching pair of files are required. 


## Setting up the Flattening script:

To set up this script, the following changes need to be made based on your project details:

1) line 36 directory = Runconfig().working_directory

The directory where the classification data, a copy of the questions.csv, and output files will reside. This Path and file name can be hardcoded here or pulled from a config file built with a copy of the script run_config.py that is also used to securely store credentials for logging on to zooniverse.  An example of a hardcoded directory is:
 
    line 36 directory = r'C:\py\My_Survey_task_data directory'    
note the "r" prevents the slashes from being escape sequences

2) line 39 question_file = 'questions.csv'

The name of the questions file used to set up the survey task for the data to be analyzed – the file must be in the directory defined above.

3) line 41 confused_with_file = 'confusedwith.csv'

The name of the confusedwith file used to set up the survey task for the data to be analyzed – the file must be in the directory defined above.

4) line 43 location = 'survey-classifications.csv'

The name of the classification data export (it is best if these are the workflow classification exports) – the file must be in the directory defined above.

5) line 47 workflow_id = 4994
6) line 48 workflow_version = 106.0

The survey task workflow number and the version to include in the output file – the version number can be used to cut off early development classifications.  Further down in the script there are other conditional statements that can be used to exclude certain classifications. 

7) line 51 survey_task = 'T0'

The task number of the survey task (normally T0 but can be project specific)

8) line 54 metadata_fields = ['Filename']

A list of metadata fields to include in the output files - these must match the subject metadata field names for your subjects. The list must include every metadata field name to be reported in the output, but not every subject must have values for all the metadata fields nor need all metadata field names be listed. Here is an example of a case with more metadata uploaded with the subjects which are to be included in the output:

    line 54 metadata_fields = ['Site', 'Date_time', 'image_1']

9) line 58  question_headers = ['how_many', 'behaviours', 'young', 'horns', 'care?']

This is a list of Headers for the flattened output file for the "questions" columns - one per question in the questions file.  This list is optional - if it is left blank (i.e. []) the zooniverse questions labels will be used, for example
"HOWMANYINDIVIDUALSDOYOUSEE". These are unnecessarily long and messy, and normally can be shortened.

10) line 62 show_vote_fraction = [0]

A list of questions which are to be filtered to a single value and vote fraction. These are normally “How many” type questions, but the output format can be used for Yes/No questions where the strict majority response is reported. If the question has more than two choices the value reported is the first value where 50% or more volunteers reported that value or values subsequent to it in the list of responses. Note the number of the questions starts at 0. The following example would be for a survey with both the first and second question a “how many” type question

line 62 show_vote_fraction = [0, 1]

11) line 69 custom_headers = {1: ['Resting', 'Standing', 'Moving', 'Eating', 'Interacting'],
                  2: ['young-Yes', 'young-No'],
                  3: ['horns-Yes', 'horns-No']
                  }


This is a dictionary of optional headers for the filtered output file. If the custom headers for a question are not defined, the question labels (or if given above in line 58, the question headers) and the response options to those questions will be used to create the column headings for that question eg " behaviours-RESTING". " behaviours-STANDING ".
If the columns headers for a question are included here there must be a header for every possible response option for that question. Again questions are numbered from 0 in the order they are in the questions file.


12) line 74 min_class = 10
13) line 75 min_species_vf = 66
14) line 76 ignore_vf = 26
15) line 77 at_least_v_f = 51

These are the limits to be used to filter the aggregate for consensus as described in the filter defined below.


## Filtering the aggregated data

````
"""The next section applies a optional filter to accept a consensus by plurality or to determine if the
result is too ambiguous to accept.  Multiple species, if they survive the filter, are output
on separate lines.

The details of the filter are as follows:

1)  The minimum number of classifications required retain a subject as classified is min_class. Subjects with
    less than this number of classifications are marked "A0 - insufficient classifications in the species column.    

2)  Determine species to include:
    Calculate the total v_f for each species using all votes for that species in any classification for the
    subject, including those with multiple species identified.

    The minimum total v_f to count any species as present is the min_species_vf (value set below). Any species
    with at least this vote fraction is recorded on a separate line with the responses to the rest of the 
    questions as recorded  against that species. These are the species "known" to be present and are marked 
    "C0 - consensus". There can be multiple "known" species.

    Species with a total vote fraction less than some value ignore_vf are ignored, and their "how many" count
    may be spread over the remaining species as described below. 
    If no species has a vote fraction over this limit then mark the subject as 'A1 - no species agreement '. This  
    only occurs if volunteers voted for many different species and all votes are spread over many species.    

3)  Indeterminate species - some species has a total vote fraction less than the min_species_vf but more
    than the ignore_vf. A subject may have both known and indeterminate species, and it may have multiple 
    indeterminate species. Indeterminate species will show on a separate line as 'I0 - indeterminate species' or 
    'I1 - multiple indeterminate species' if there is more than one. Vote fractions will show for all responses
    entered for the species but 'how many' values are shown only if the vote fraction meets some limit 
    at_least_v_f where it is assumed they have some significance.      

4)  If there is a "How many" type question. (These will generally be counts and a vote fraction for that count)        
        Calculate the "How many" and vote fraction as follows:
            1. Use the vote fractions for all possible responses to the 'how many' question(s), from all 
            classifications including in some cases described below, those from an "ignored" species that did 
            not make it through the species filter above.            
            2. list the vote fraction of each possible response option ie the number of classifications that had
            that response divided by the number of classifications for the subject, in order by count. Place 
            "unknown" as the lowest option if it was an allowed choice.            
            3. Beginning at the highest count, take the vote fraction of classifications that had that count 
            and add the vote fraction of the next highest count, and continue until some total at_least_v_f 
            saw AT LEAST that number of animals. Report the count as the 'how many' and the summed vote
            fraction as the vote fraction. For a reasonable choice of at_least_v_f such as 51 this ensures any 
            consensus, if one exists, is selected as the 'how many', otherwise the value can be interpreted as 
            an "at least" count.
            
        If there is one or more "ignore" species which did not get enough votes to be counted as a known or an 
        indeterminate species, it is very likely that the animals are misidentified, but it is also likely 
        the 'how many' responses are still accurate, and these may be applied to one of the species that did 
        make the cut.  
        
        The "ignored" votes for a species will be applied to any known or indeterminate species that was a 
        'confused with' pair with the ignored species as listed in the confusedwith.csv file. If there is a
        match, the vote fraction for each possible response for the ignored species is added to the vote fraction
        for the corresponding response for the matching species. Note the vote fraction for the species choices
        themselves are NOT modified, only the question responses are added up.       
        In general, "known" species already have enough votes this makes little or no difference, but it is 
        the best we can do to include all the information provided by the volunteers.
        Species which have added votes are marked with the word "augmented". 

5)  For all other (ie not "how many" type) questions, report a simple v_f for each possible response.  This is 
        based on the votes for each response divided by the total number of classifications.  If the votes for 
        an ignored species are added to a known or indeterminate species the vote fractions can be higher than 
        the species vote_fraction.  

Note the output is a columnar format vs the answer_vector approach of the aggregated file, with columns for a 
value and a vote fraction for each How many type question, and a column for every question response option 
for the other question types"""

````
