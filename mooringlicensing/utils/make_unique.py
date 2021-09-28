import os
import json

class MakeUnique(object):

    def __init__(self, path='/var/www/mooringlicensing/mooringlicensing/utils/wait_list'):
        self.path = path
        self.make_unique()

    def get_files(self):
        ''' Read all files in directory '''
        files = []
        with os.scandir(self.path) as it:
            for entry in it:
                if entry.name.endswith(".json") and entry.is_file():
                    files.append(entry.name)
        return files

    def make_unique(self):
        ''' Remove duplicate entries in json file and write to unique folder '''
        tmp_list = []
        for fname in self.get_files():
            filename = self.path + os.sep + fname if not self.path.endswith(os.sep) else self.path + fname
            with open(filename) as f:
                f_json = json.load(f)

            out_path = self.path + os.sep + 'unique' if not self.path.endswith(os.sep) else self.path + 'unique'
            if not os.path.exists(out_path):
                os.makedirs(out_path)

            _list = []
            for i in f_json:
                if i not in _list:
                    _list.append(i)
            print(f'Original Length: {len(f_json)}\tNew Length: {len(_list)}\t({fname})')

            with open(out_path + os.sep + fname, 'w') as f:
                print(json.dumps(_list), file=f)

            tmp_list.append( {fname : _list[:3]} )

        with open(out_path + os.sep + 'summary.json', 'w') as f:
            print(json.dumps(tmp_list), file=f)

        #return tmp
