from argparse import ArgumentParser

from cpm_disk_def import CPMDiskDefinition

if __name__ == "__main__":

    # parse arguments to get the directory where are the files to add
    parser = ArgumentParser()
    parser.add_argument("-i", "--img", help="Image file to create", required=True)
    parser.add_argument("-t", "--type", help="Type of disk to create", required=True)
    parser.add_argument("-v", "--verbose", help="Verbose output",
                        action="store_true")
    
    args = parser.parse_args()
    diskdef = CPMDiskDefinition()
    diskdef.print_defs()
    disk = diskdef.get_disk(args.type, args.img)

    disk.disk_info()
    disk.read_directory()
    disk.list_directory()
    
    if args.verbose:
        disk.disk_map_visual()
        disk.disk_map_free()
        disk.dump_block(0)
        
        
