"""read and write disk definitions to a file defaulting to diskdefs"""

import cpm_disk


class CPMDiskDefinition:
    """ Reads and writes disk definitions to a file defaulting to diskdefs """

    def __init__(self, filename="diskdefs"):
        self.filename = filename
        self.cpm_defs = {}
        self.read_cpm_defs()

    def write_cpm_defs(self, cpm_defs):
        """ Writes a dictionary of disk definitions to a file """
        with open(self.filename, 'w', encoding='utf-8') as file:
            for title, params in cpm_defs.items():
                file.write(f"def {title}\n")
                for key, value in params.items():
                    file.write(f"   {key} {value}\n")
                file.write("end\n\n")

    def read_cpm_defs(self):
        """ Reads disk definitions from a file """
        current_title = None
        current_data = {}

        with open(self.filename, 'r', encoding='utf-8') as file:
            for line in file:
                stripped_line = line.strip()
                if stripped_line.startswith('def'):
                    _, title = stripped_line.split()
                    current_title = title
                    current_data = {}
                elif stripped_line.startswith('end'):
                    self.cpm_defs[current_title] = current_data
                else:
                    if stripped_line:
                        key, value = stripped_line.split()
                        current_data[key] = int(value)

    def get_disk(self, def_name, filename):
        if def_name in self.cpm_defs:
            params = self.cpm_defs[def_name]
            return cpm_disk.CPMDisk(filename,
                                    params['tracks'],
                                    params['sectors'],
                                    params['bytes_sector'],
                                    params['blocksize'],
                                    params['bsh'],
                                    params['drm'],
                                    params['off'])
        else:
            raise ValueError(
                "Disk definition not found for drivename: " + def_name)

    def print_defs(self):
        print(self.cpm_defs)
