import os
import csv
import cryptography
from cryptography.fernet import Fernet


class Runconfig(object):
    def __init__(self, run_config='run_config.csv'):
        self.run_config = run_config
        self.username = ''
        self.password = ''
        self.working_directory = ''
        self.project_slug = ''

        key = b'0BKQ-udLcSlQz0rAvUQnONMC7UVJ2f1y2IxUXSGcglk='
        fernet = Fernet(key)

        if os.path.isfile(self.run_config):
            with open(self.run_config, 'r') as config_file:
                config_dict = csv.DictReader(config_file)
                for line in config_dict:
                    try:
                        self.username = line['username']
                        self.password = fernet.decrypt(line['password'].encode()).decode()
                        self.working_directory = line['directory']
                        self.project_slug = line['project_slug']
                        return
                    except cryptography.fernet.InvalidToken:
                        pass
                    break

        print("\033[1;31m No valid run_config file found; generating a new one:")
        print("\033[1;30m")
        new_key = Fernet.generate_key()
        fernet = Fernet(new_key)
        with open('New_file.py', 'w', newline='') as new_file:
            with open('run_config.py', 'r') as old_file:
                for line in old_file:
                    if line.find(str(key)) >= 0:
                        new_file.write('        ' + 'key = ' + str(new_key) + '\n')
                    else:
                        new_file.write(line)

        os.remove('run_config.py')
        os.rename('New_file.py', 'run_config.py')

        with open(self.run_config, 'w', newline='') as config_file:
            fieldnames = ['username', 'password', 'directory', 'project_slug']
            writer = csv.DictWriter(config_file, fieldnames=fieldnames)
            writer.writeheader()
            new_row = {}
            while True:
                print('Enter the full path for the working '
                      'directory for the project where the'
                      ' \033[1;31mdata files'
                      ' \033[1;30mare stored.')
                self.working_directory = input()
                if os.path.exists(self.working_directory):
                    break
                else:
                    print('That entry is not a valid path for an existing directory')
                    retry = input('Enter "y" to try again, any other key to exit' + '\n')
                    if retry.lower() != 'y':
                        quit()
            new_row['directory'] = self.working_directory
            self.username = input('Enter your zooniverse username' + '\n')
            new_row['username'] = self.username
            self.password = input('Enter your zooniverse password' + '\n')
            new_row['password'] = fernet.encrypt(self.password.encode()).decode()
            self.project_slug = input('Enter the full project slug for your zooniverse project - '
                                      'eg pmason/fossiltrainer' + '\n')
            new_row['project_slug'] = self.project_slug
            writer.writerow(new_row)
            print('Completed generating new config file, Please \033[1;31mrestart the script \033[1;30mto use it')
            quit()
