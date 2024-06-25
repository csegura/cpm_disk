import sys
import os
from argparse import ArgumentParser

from cpm_disk_def import CPMDiskDefinition

if __name__ == "__main__":

    # parse arguments to get the directory where are the files to add
    parser = ArgumentParser()
    parser.add_argument(
        "-t", "--type", help="Type of disk to create", required=True)
    parser.add_argument("-d", "--dir", nargs='+',
                        help="Directory with files to add", type=str)
    parser.add_argument(
        "-a", "--add", help="Add files to disk", type=str, nargs='+')
    parser.add_argument("-e", "--extract",
                        help="Extract files from disk", type=str, nargs='+')
    parser.add_argument("-f", "--format", help="Format disk",
                        default=False, action="store_true")
    parser.add_argument("-s", "--show", help="Show directory",
                        default=False, action="store_true")
    parser.add_argument("-db", "--dump", help="Dump a block (hex)",
                        default=0, type=str)
    parser.add_argument(
        "-i", "--img", help="Image file. With -f image will be created", required=True)
    parser.add_argument("-v", "--verbose", help="Verbose output",
                        action="store_true")

    args = parser.parse_args()

    diskdef = CPMDiskDefinition()

    # print definitions
    # diskdef.print_defs()

    disk = diskdef.get_disk(args.type, args.img)

    if args.verbose:
        disk.disk_info()

    if args.format:
        print(f"Creating disk image {args.img} of type {args.type}")
        disk.initialize_disk()

    disk.read_directory()

    # args directory is the source or list sources directory
    if args.dir:
        print(f"Adding files from directories: {args.dir}")
        for directory in args.dir:
            if not os.path.exists(directory):
                print(f"Error: Directory {directory} does not exist")
                sys.exit(1)
            # get all files in the source directory
            files = [f for f in os.listdir(directory) if os.path.isfile(
                os.path.join(directory, f))]
            for file in files:
                if file.startswith("."):
                    continue
                print(f"** Adding file: {file}")
                disk.put_file(os.path.join(directory, file))

    if args.add:
        print(f"Adding files: {args.add}")
        for file in args.add:
            print(f"** Adding file: {file}")
            disk.put_file(file)

    if args.extract:
        print(f"Extracting files: {args.extract}")
        for file in args.extract:
            print(f"** Extract file: {file}")
            disk.get_file(file)

    if args.dir or args.add or args.extract or args.show:
        disk.list_directory()        
        
    if args.dump:
        block = int(args.dump, 16)
        disk.dump_block(block)
