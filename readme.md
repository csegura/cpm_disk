
## CPM Disk Tool

I'm currently working on implementing a CP/M for my small Z80 CPU. As a reminder, this involves a single Z80 CPU connected to a Raspberry Pi, with the latter emulating RAM, ROM, and IO devices.

I spent this weekend diving into the workings of CP/M disks. While there is a Unix tool available to create CP/M disk images [](https://github.com/lipro-cpm4l/cpmtools
), I've decided to create my own version using Python.

The project contains a class to manage the directory entries CPMDirectoryEntry, and another CPMDisk to deal with disk operations. The program also uses a disk definition file in order to generate different disk formats inspired by the Unix tool.

Finally, there is a tool disktool.py to manipulate the disk images.

### Disktool

Example 

```sh
python ./disktool.py -t 8Mb -f -d ./src/main -i ./img/disk_8.img -v
```

Sample output:

```
Disk: ./img/disk_a.img
Tracks: 77
Sectors per track: 26
Sector size: 128
Block size: 1024
Total blocks: 250 - (256000 bytes)
Reserved blocks: 6
Directory blocks: 2
Total usable blocks: 249 - (254976 bytes)
First usable block: 2 - (2, 12)
Sectors per block: 8
Directory start: 6656 - 00001a00
Data area start: 2048 - 00000800
Directory blocks: 2
Directory size: 2048
Directory max entries: 64
Size: 256256 bytes
Creating disk image ./img/disk_a.img of type 256k
Adding files from directories: ['./src/main']
** Adding file: ASM.COM
** Adding file: basic.com
** Adding file: CRC.COM
** Adding file: DDT.COM
** Adding file: DUMP.COM
** Adding file: ED.COM
** Adding file: LOAD.COM
** Adding file: MBASIC.COM
** Adding file: PIP.COM
** Adding file: STAT.COM
** Adding file: SUBMIT.COM
** Adding file: SURVEY.COM
** Adding file: SYSGEN.COM
** Adding file: XSUB.COM
** Adding file: ZDE.COM
Directory Listing:
--------------------------------------------------------------------------------------------------------------
Entry  Usr Ext Filename  Type  Rec  Blocks                                             Size
--------------------------------------------------------------------------------------------------------------
0      0   0   ASM       COM   40 - 02 03 04 05 06 07 08 09 00 00 00 00 00 00 00 00  - 8.00 Kb
1      0   0   BASIC     COM   80 - 0a 0b 0c 0d 0e 0f 10 11 12 13 14 15 16 17 18 19  - 16.00 Kb
2      0   1   BASIC     COM   61 - 1a 1b 1c 1d 1e 1f 20 21 22 23 24 25 26 00 00 00  - 13.00 Kb
3      0   0   CRC       COM   29 - 27 28 29 2a 2b 2c 00 00 00 00 00 00 00 00 00 00  - 6.00 Kb
4      0   0   DDT       COM   26 - 2d 2e 2f 30 31 00 00 00 00 00 00 00 00 00 00 00  - 5.00 Kb
5      0   0   DUMP      COM   04 - 32 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 1.00 Kb
6      0   0   ED        COM   34 - 33 34 35 36 37 38 39 00 00 00 00 00 00 00 00 00  - 7.00 Kb
7      0   0   LOAD      COM   0e - 3a 3b 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 2.00 Kb
8      0   0   MBASIC    COM   80 - 3c 3d 3e 3f 40 41 42 43 44 45 46 47 48 49 4a 4b  - 16.00 Kb
9      0   1   MBASIC    COM   3e - 4c 4d 4e 4f 50 51 52 53 00 00 00 00 00 00 00 00  - 8.00 Kb
10     0   0   PIP       COM   3a - 54 55 56 57 58 59 5a 5b 00 00 00 00 00 00 00 00  - 8.00 Kb
11     0   0   STAT      COM   29 - 5c 5d 5e 5f 60 61 00 00 00 00 00 00 00 00 00 00  - 6.00 Kb
12     0   0   SUBMIT    COM   0a - 62 63 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 2.00 Kb
13     0   0   SURVEY    COM   0d - 64 65 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 2.00 Kb
14     0   0   SYSGEN    COM   0c - 66 67 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 2.00 Kb
15     0   0   XSUB      COM   06 - 68 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 1.00 Kb
16     0   0   ZDE       COM   80 - 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 76 77 78  - 16.00 Kb
17     0   1   ZDE       COM   04 - 79 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  - 1.00 Kb
--------------------------------------------------------------------------------------------------------------
Total entries: 64 - Used entries: 18
```

### Usage

```
Usage: disktool.py [-h] -t TYPE [-d DIR [DIR ...]] [-a ADD [ADD ...]]
                       [-e EXTRACT [EXTRACT ...]] [-f] [-s] [-db DUMP] -i IMG
                       [-v]

Options:
  -h, --help            Show this help message and exit
  -t TYPE, --type TYPE  Type of disk to create (required)
  -d DIR [DIR ...], --dir DIR [DIR ...]
                        Directory with files to add
  -a ADD [ADD ...], --add ADD [ADD ...]
                        Add files to disk
  -e EXTRACT [EXTRACT ...], --extract EXTRACT [EXTRACT ...]
                        Extract files from disk
  -f, --format          Format disk
  -s, --show            Show directory
  -db DUMP, --dump DUMP
                        Dump a block (hex)
  -i IMG, --img IMG     Image file. With -f image will be created (required)
  -v, --verbose         Verbose output

Description:
This program allows you to create, modify, and inspect disk images.

Examples:
  Create a new disk image:
    disktool.py -t 256k -i new_disk.img -f

  Add files to an existing disk image:
    disktool.py -t 256k -i existing_disk.img -a file1.txt file2.txt

  Extract files from a disk image:
    disktool.py -t 256k -i disk.img -e file1.txt file2.txt

  Show the directory contents of a disk image:
    disktool.py -t 256k -i disk.img -s

  Dump a specific block from the disk image in hexadecimal:
    disktool.py -t 256k -i disk.img -db 0

Note: The --type and --img options are required for all operations.
```

Disk definitions are stored in the diskdef file, it is similar but not the same as the Unix tool. 

Example for a 256k disk image:
77 tracks, 26 sectors per track, 128 bytes per sector, 1024 bytes per block, 242 directory sectors, 64 directory entries, 2 reserved tracks.

```
def 256k
  tracks 77
  sectors 26
  bytes_sector 128
  blocksize 1024
  bsh 3
  blm 7
  dsm 242
  drm 64
  off 2
end
```

Create disk image with content files included in ./scr/main as ./img/disk_a.img

```sh
 python ./disktool.py -t 256k -f -d ./src/main -i ./img/disk_a.img -v  
```

Add files to disk image

```sh
 python ./disktool.py -t 256k -i ./img/disk_a.img -a ./src/main/file1.txt ./src/main/file2.txt -v
```

Also you might use the classes in your own code, for example:

```python
    import cpm_disk

    disk = CPMDisk("TDISK02.DSK",
                   77,      # 75 tracks
                   26,      # 26 sectors per track
                   128,     # 128 bytes per sector
                   1024,    # 1024 bytes per block (1 block = 8 sectors)
                   3,       # bsh - block shift
                   7,       # blm - block mask
                   242,     # dsm - max data blocks
                   64,      # drm - max directory entries
                   2)       # off - reserved tracks
    initialize_disk()
```                   

Or a custom tool as dir.py

```python
from argparse import ArgumentParser
from cpm_disk_def import CPMDiskDefinition

if __name__ == "__main__":

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
```




