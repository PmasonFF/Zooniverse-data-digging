import os
import csv
import json

# #  Hardcode the pathnames and filenames of destination and sliced output file
dstn_subj = r'C:\py\SASClass\snapshots-at-sea-subjects.csv'
out_location_subj = r'C:\py\SASClass\snapshots-at-sea-subjects_simplified.csv'


def include_subj(subj_record):
    try:
        if int(subj_record['workflow_id']) == 566:
            pass  # replace'!= 0000' with '== xxxx' where xxxx is any workflow linked to the project.
        else:
            return False
    except:
        return False
    # if 84 >= int(subj_record['subject_set_id']) >= 9:
    #     pass  # replace '00000' and 100000 with first and last subject set to include.
    # else:
    #     return False
    if 40000000 >= int(subj_record['subject_id']) >= 1000:
        pass  # replace upper and lower subject_ids to include only a specified range of subjects -this is
        # a very useful slice since subjects ids are sequentially assigned and increase with date and time created.
    else:
        return False
    # otherwise :
    return True


def slice_exports(dstn_sb, out_location_sb):
    i = 0
    m = 0
    with open(out_location_sb, 'w', newline='') as file:
        fieldnames = ['subject_id',
                      'project_id',
                      'workflow_id',
                      'subject_set_id',
                      'Filename',
                      'classifications_count',
                      'retired_at'
                      ]

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        #  open the zooniverse data file using dictreader
        with open(dstn_sb) as f:
            r = csv.DictReader(f)
            subject = ''
            for row in r:
                i += 1
                if include_subj(row):
                    subj = json.loads(row['metadata'])
                    filename = ''
                    new_subject = row['subject_id']
                    if new_subject == subject:
                        continue
                    else:
                        m += 1
                        subject = new_subject
                        try:
                            if "filename" in subj:
                                filename = subj['filename']
                            elif "Filename" in subj:
                                filename = subj['Filename']
                        except:
                            for k in subj:
                                if "filename" in k:
                                    filename = subj[k]['filename']
                                elif "Filename" in subj[k]:
                                    filename = subj[k]['Filename']

                        # This set up the writer to match the field names above and the variable names of their values:
                        writer.writerow({'subject_id': row['subject_id'],
                                         'project_id': row['project_id'],
                                         'workflow_id': row['workflow_id'],
                                         'subject_set_id': row['subject_set_id'],
                                         'Filename': filename,
                                         'classifications_count': row['classifications_count'],
                                         'retired_at': row['retired_at'],
                                         })

    print('Subjects file:' +
          ' ' + str(i) + ' lines read and inspected' + ' ' + str(m) + ' records selected and copied')
    return True


if __name__ == '__main__':
    #  print(download_exports(project, dstn_class, dstn_subj))
    print(slice_exports(dstn_subj, out_location_subj))
#
