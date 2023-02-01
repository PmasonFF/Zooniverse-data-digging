import csv
import json
import os

# File location section:
directory = r'C:\py\Battling_birds'  # modify this to match your directory structure
json_file = 'project-5103-comments_2020-07-07'  # modify as needed
json_location = directory + os.sep + json_file + '.json'
parsed_location = directory + os.sep + 'parsed_' + json_file + '.csv'

# board_ids
#   HT 2108,2307,2100,2019,2017,2016,2015,2014
#   BB 1498,2308,2011,1174,1500,1501,1499,1497


# Filter definitions
def include(comment_record):
    if int(comment_record['board_id']) in [1498, 2308, 2011, 1174, 1500, 1501, 1499, 1497]:
        pass
    else:
        return False
        # if '2100-00-10 00:00:00 UTC' >= comment_record['comment_created_at'] >= '2020-04-13 00:00:00 UTC':
    #     pass  # replace earliest and latest created_at date and times to select records commenced in a
    #     #  specific time period
    # else:
    #     return False
    # otherwise :
    return True


# Set up the output file structure with desired fields:
# prepare the output file and write the header
with open(parsed_location, 'w', newline='', encoding='utf-8') as file:
    fieldnames = ['board_id',
                  'board_title',
                  'discussion_id',
                  'discussion_title',
                  'comment_id',
                  'body',
                  'user_id',
                  'user_login',
                  'created_at'
                  ]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()

    # this area for initializing counters, status lists and loading pick lists into memory:
    i = 0
    j = 0

    #  open the zooniverse comment file
    with open(json_location, encoding='utf-8') as f:
        r = json.load(f)
        for row in r:
            i += 1
            #
            if include(row) is True:
                j += 1
                # This sets up the writer to match the field names above and the variable names of their values:
                writer.writerow({'board_id': row['board_id'],
                                 'board_title': row['board_title'],
                                 'discussion_id': row['discussion_id'],
                                 'discussion_title': row['discussion_title'],
                                 'comment_id': row['comment_id'],
                                 'body': row['comment_body'],
                                 'user_id': row['comment_user_id'],
                                 'user_login': row['comment_user_login'],
                                 'created_at': row['comment_created_at']
                                 })
    print(j, "comments written out of", i)

