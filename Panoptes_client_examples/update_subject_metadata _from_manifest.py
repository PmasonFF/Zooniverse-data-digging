import os
import csv
from panoptes_client import SubjectSet, Project, Panoptes

Panoptes.connect(username=os.environ['User_name'], password=os.environ['Password'])
project = Project.find(slug='tomomi/rainforest-flowers')

updated_manifest = r'C:\py\Flowers\Sharon_Manifes_updated.csv'
with open(updated_manifest) as f:
    r = csv.DictReader(f)
    metadata_dict = {}
    for row in r:
        built_dict = {"Scientific Name": row['Scientific Name'],
                      "Country         ": row['Country'],
                      "Photographer      ": row['Photographer'],
                      "institution        ": row['Institution'],
                      "Catalog IRN         ": row['Catalog_IRN'],
                      "MM_IRN               ": row['MM_IRN'],
                      "#file": row['#File'],
                      "#Grouping": row['#Grouping'],
                      "#Project": row['#Project']
                      }
        metadata_dict[row['#File']] = built_dict

i = 0
while True:
    set_id = input('Entry subject set id to update:' + '\n')
    try:
        subject_set = SubjectSet.find(set_id)
        for subject in subject_set.subjects:
            new_meta = metadata_dict[subject.metadata['#file']]
            i += 1
            field = list(subject.metadata.keys())
            for item in field:
                del subject.metadata[item]
            subject.metadata.update(new_meta)
            print(i, subject.metadata)
            subject.save()
        break
    except:
        retry = input('Subject set not found, Enter "n" to cancel, any other key to retry' + '\n')
        if retry.lower() == 'n':
            quit()
