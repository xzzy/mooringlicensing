import os
import json
import csv
from os import listdir
from os.path import isfile, join

class JsonToCsv():
    #def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_07Oct2021_auth_users/'):
    def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_07Oct2021/'):
        self.path = path

    def read_dict(self, fname):
        filename = self.path + os.sep + fname if not self.path.endswith(os.sep) else self.path + fname
        with open(filename) as f:
            f_json = json.load(f)

            # make list unique
            _list = []
            for i in f_json:
                if i not in _list:
                    _list.append(i)

        #import ipdb; ipdb.set_trace()
        return _list

    def convert(self):
        #import ipdb; ipdb.set_trace()
        files = [f for f in listdir(self.path) if isfile(join(self.path, f))]

        for filename in files:
            try:
                _list = self.read_dict(filename)
                if _list:

#                    #csv_filename = '/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_csv/' + filename.replace('json','csv')
#                    csv_filename = '/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_all_csv/' + filename.replace('json','csv')
#                    with open(csv_filename, 'w') as f:
#                        dict_writer = csv.DictWriter(f, fieldnames=_list[0].keys())
#                        dict_writer.writeheader()
#                        for row in _list:
#                            dict_writer.writerow(row)

                    csv_filename = '/var/www/mooringlicensing/mooringlicensing/utils/lotus_notes_all_csv/' + filename.replace('json','csv')
                    with open(csv_filename, 'w') as f:
                        #csvwriter = csv.writer(f)
                        #import ipdb; ipdb.set_trace()
                        for row in _list:
                            f.write(str(row) + '\n')

            except Exception as e:
                print(e)
                print(filename)
                import ipdb; ipdb.set_trace()



