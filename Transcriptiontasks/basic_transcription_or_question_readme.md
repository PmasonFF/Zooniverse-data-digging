In the Classification download, the user's responses to each task are recorded in a field called 'annotations' (including those of experts and those tagged "TRUE" for being gold standard responses. The field is a JSON string. When loaded into Python using the json.loads() function from import json it becomes a dictionary of dictionaries of form {{....}, {.....}, {....}} with a dictionary for each task the user is required to complete, in the order completed.

The form of the individual dictionaries for the tasks depends very much on what type of task it is - a question, drawing tool, transcription or survey task.

This set of scripts is for basic transcription and question tasks which will be flattened in preparation of using reconcile.py to reconcile the transcription blocks.

Types of transcription tasks:

A simple transcription tasks ans simple question tasks both have the form {"task":"TX", "task_label":"instructions the users saw", "value":"text entered or answer(s) selected"}.

This is pretty simple, especially if one knows which of the blocks in annotations we are dealing with. Even without that we can find the correct task because we know the wording of the instruction text. (Due to the way the project builder can be assembled, it is unlikely tasks are numbered in the order completed, and with the conditional branching allowed, tasks are not even in the same order in every response.)

To start we use the basic frame - see elsewhwere in this respository, and add in blocks to get the metadata of the form:
````
                subject_data = json.loads(row['subject_data'])  # pull metadata from the subject data field

                metadata = subject_data[(row['subject_ids'])]
                try:
                    metadata_1 = metadata['metadata_1']
                except KeyError:
                    metadata_1 = ''
````

Then we are ready to add blocks for the questions and transcriptions of the form:
Note the task numbers are used here exclusively to pick the correct task values, and these task numbers would be project specific!
````
                annotations = json.loads(row['annotations'])
                
                # reset the field variables for each new row
                q1 = ''
                q2 = []
                q2_vector = [0, 0, 0]  # vector format for multiple responses
                t1 = ''
                t2 = ''
                d1 = ''
                d2 = ''
                d3 = ''
                date = ''

                # loop over the tasks
                for task in annotations:
                    #  Question 1? # single response
                    try:
                        if task['task'] == 'T0':
                            q1 = task['value']
                    except KeyError:
                        pass

                    #  Question 2? # multiple response where shortened response choices are listed, and also reported
                    # in a vector format for easy aggregation
                    try:
                        if task['task'] == 'T1':
                            if task['value'] is not None:
                                for counter in range(0, len(q2_template)):
                                    for item in task['value']:
                                        if item.find(q2_template[counter]) >= 0:
                                            q2.append(q2_template[counter])
                                            q2_vector[counter] = 1
                    except KeyError:
                        pass

                    # Free Transcription_1
                    try:
                        if task['task'] == 'T2':
                            if task['value'] is not None:
                                t1_raw = str(task['value'])
                                t1 = t1_raw.replace('\n', ' ').strip()
                    except KeyError:
                        pass
````
Further transcription blocks and dropdowns both nested and standalone may be required.  Here we do some preprocessing of a transcription block, in this case to remove "unclear" tags using a function:
````
                    # Free Transcription_2  - clean for unclear tags
                    try:
                        if task['task'] == 'T3':
                            if task['value'] is not None:
                                t2_raw = str(task['value'])
                                t2 = clear_unclear(t2_raw.replace('\n', ' ').strip())  # uses a function to replace tags with blanks
                    except KeyError:
                        pass

                    # Dropdown Month/day? # example of a nested set of dropdowns
                    try:
                        if task['task'] == 'T4':
                            if task['value'] is not None:
                                if task['value'][0]['value'] is not None:
                                    d2 = str(task['value'][0]['value'])
                                if task['value'][1]['value'] is not None:
                                    d1 = str(task['value'][1]['value'])
                                    # Occasionally it may be necessary to deal with certain cases where the d1 or d2 value
                                    # appears as an odd string like 'da0a39c5a481a8' rather than the correct number (zooniverse glitch which has been corrected):
                                    #  if d1 == 'da0a39c5a481a8':
                                    #      d1 = '12'
                    except KeyError:
                        pass

                    # Dropdown Year?
                    try:
                        if task['task'] == 'T5':
                            if task['value'] is not None:
                                d3 = str(task['value'][0]['value'])
                                # same issue as in month/day dropdowns can occur here with odd values not in the dropdown list
                    except KeyError:
                        pass
````
Of course other preprocessing or modification of the returned values can be done, here to get date in a certain format:
````
                # massage date
                if len(d1) == 1:
                    day = '0' + d1
                else:
                    day = d1

                if len(d2) == 1:
                    mon = '0' + d2
                else:
                    mon = d2

                if len(d3) > 4:
                    year = 'xxxx'
                elif len(d3) == 0:
                    year = '0000'
                else:
                    year = d3
                date = mon + '/' + day + '/' + year
````
Finally the rest of the flattening framework outputs the responses in columns as we defined in the framework.

Reconciliation of the transcriptions between users:

Transcriptions are difficult to aggregate. Unless multiple volunteers input the exact same thing, down to capitalization, spacing and punctuation, simple conditional matching is inadequate and some sort of reconciliation between the multiple answers must be done. However this problem has been solved rather well by the Notes From Nature team, and we can use their expertise. We need to get the data from your specific project into a format that can use their code to reconcile the responses.

See https://github.com/juliema/label_reconciliations

It is not a trivial task to get set up to use their code - it requires a number of additional python packages be installed and familiarity with passing arguments to the main module at execution. See the readme in this repository on this topic.

While it was written specifically for their somewhat customized Zooniverse interface, their code has the ability to reconcile any appropriately prepared csv file. To do so we need to give reconcile.py a parameter string:

Firstly -f csv to tell it is getting a csv formatted file,

then -c with a list of the column headers you want reconciled and what sort of data each is example:
-c column1:text column2:same column3:select
would tell reconcile.py to reconcile the first column as a transcribed text, the second column would be included in the output but it is expected all the classifications for that subject had column2 the same value, and column3 is from a dropdown and expected to be one of a defined group of responses - the majority response (or first if a tie) would be reported.

Next you have to have--user-column user_name where user_name is the column header for your file where the user_names are listed.

Plus the output file names -r xxxxxxxxxxxxxxxxxxx and -s xxxxxxxxxxxxxxxxxx and the input file name last.

So here is a parameter list using the column names used in flatten_classification_basic_transcription_or_question_tasks.py:
````
-fcsv -c metadata_1:same,metadata_2:same,question_task_1:select,transcription_1:text,transcription_2:text,month:select,day:select,year:select,Date:text
-r data\reconciled_basic_transcription_or_ question_tasks.csv
-s data\summary_basic_transcription_or_ question_tasks.html
--user-column user_name
flatten_class_project_sorted.csv
````
Note one would have to aggregate and deal with the multiple response question outside of reconcile.py, and for the single response question reconcile will find strictly the majority response, but will struggle with tie situations or where there is no good consensus and even the majority response is questionable.
                                 
                                 
