#
# Directory entries
# The directory is a sequence of directory entries (also called extents), which contain
# 32 bytes of the following structure:
#
# St	F0	F1	F2	F3	F4	F5	F6	F7	E0	E1	E2	Xl	Bc	Xh	Rc
# Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al	Al
#
# St is the status; possible values are:
#
#   0–15:   used for file, status is the user number.  CP/M 2.2 only documents 0–15 and
#           CCP and PIP only offer those, but the BDOS allows to use 0–31.
#   16–31:  used for file, status is the user number (P2DOS, CP/M 2.2) or used for password extent (CP/M 3 or higher)
#   32:     disc label
#   33:     time stamp (P2DOS)
#   0xE5: unused
#
# F0–E2 are the file name and its extension.  They may consist of any printable 7 bit ASCII
# character but: < > . , ; : = ? * [ ]. The file name must not be empty, the extension
# may be empty.  Both are padded with blanks.  The highest bit of each character of the
# file name and extension is used as attribute.  The attributes have the following meaning:
#
#   F0: requires set wheel byte (Backgrounder II)
#   F1: public file (P2DOS, ZSDOS), forground-only command (Backgrounder II)
#   F2: date stamp (ZSDOS), background-only commands (Backgrounder II)
#   F7: wheel protect (ZSDOS)
#   E0: read-only
#   E1: system file
#   E2: archived
#
# Public files (visible under each user number) are not supported by CP/M 2.2, but there is
# a patch and some free CP/M clones support them without any patches.
#
# The wheel byte is (by default) the memory location at 0x4b.  If it is zero,
# only non-privileged commands may be executed.
#
# Xl and Xh store the extent number.  A file may use more than one directory entry,
# if it contains more blocks than an extent can hold. In this case, more extents are allocated
# and each of them is numbered sequentially with an extent number.
# If a physical extent stores more than 16k, it is considered to contain multiple logical extents,
# each pointing to 16k data, and the extent number of the last used logical extent is stored.
# Note: Some formats decided to always store only one logical extent in a physical extent, thus
# wasting extent space.  CP/M 2.2 allows 512 extents per file, CP/M 3 and higher allow up to 2048.
#
# Bit 5–7 of Xl are 0, bit 0–4 store the lower bits of the extent number.
# Bit 6 and 7 of Xh are 0, bit 0–5 store the higher bits of the extent number.
#
# Rc and Bc determine the length of the data used by this extent.
# The physical extent is divided into logical extents, each of them being 16k in size (a physical
# extent must hold at least one logical extent, e.g. a blocksize of 1024 byte with two-byte block
# pointers is not allowed). Rc stores the number of 128 byte records of the last used logical
# extent. Bc stores the number of bytes in the last used record.  The value 0 means 128 for
# backward compatibility with CP/M 2.2, which did not support Bc.
# ISX records the number of unused instead of used bytes in Bc. This only applies to files with
# allocated blocks.  For an empty file, no block is allocated and Bc 0 has no meaning.
#
# Al stores block pointers.  If the disk capacity minus boot tracks but including the directory
# area is less than or equal to 256 blocks, Al is interpreted as 16 byte-values, otherwise as
# 8 double-byte-values. Since the directory area is not subtracted, the directory area starts with
# block 0 and files can never allocate block 0, which is why this value can be given a new meaning:
# A block pointer of 0 marks a hole in the file.  If a hole covers the range of a full extent,
# the extent will not be allocated.  In particular, the first extent of a file does not neccessarily
# have extent number 0.  A file may not share blocks with other files, as its blocks would be freed
# if the other files is erased without a following disk system reset.
# CP/M returns EOF when it reaches a hole, whereas UNIX returns zero-value bytes, which makes
# holes invisible.
#

# UU F1 F2 F3 F4 F5 F6 F7 F8 T1 T2 T3 EX S1 S2 RC   .FILENAMETYP....
# AL AL AL AL AL AL AL AL AL AL AL AL AL AL AL AL   ................
#
# UU = User number. 0-15 (on some systems, 0-31). The user number allows multiple
#     files of the same name to coexist on the disc.
#      User number = 0E5h => File deleted
# Fn - filename
# Tn - filetype. The characters used for these are 7-bit ASCII.
#        The top bit of T1 (often referred to as T1') is set if the file is
#      read-only.
#        T2' is set if the file is a system file (this corresponds to "hidden" on
#      other systems).
# EX = Extent counter, low byte - takes values from 0-31
# S2 = Extent counter, high byte.
#
#       An extent is the portion of a file controlled by one directory entry.
#     If a file takes up more blocks than can be listed in one directory entry,
#     it is given multiple entries, distinguished by their EX and S2 bytes. The
#     formula is: Entry number = ((32*S2)+EX) / (exm+1) where exm is the
#     extent mask value from the Disc Parameter Block.
#
# S1 - reserved, set to 0.
# RC - Number of records (1 record=128 bytes) used in this extent, low byte.
#     The total number of records used in this extent is
#
#     (EX & exm) * 128 + RC
#
#     If RC is >=80h, this extent is full and there may be another one on the
#     disc. File lengths are only saved to the nearest 128 bytes.
#
# AL - Allocation. Each AL is the number of a block on the disc. If an AL
#     number is zero, that section of the file has no storage allocated to it
#     (ie it does not exist). For example, a 3k file might have allocation
#     5,6,8,0,0.... - the first 1k is in block 5, the second in block 6, the
#     third in block 8.
#      AL numbers can either be 8-bit (if there are fewer than 256 blocks on the
#     disc) or 16-bit (stored low byte first).

import re
import math

EMPTY_ALLOCATION = [0] * 16

class CPMDirectoryEntry:
    """ CP/M Directory Entry
        Manages CPM Directory Entries
    """
    def __init__(self, use_16bit, user_number=0, filename="", filetype="", extent_low=0, extent_high=0, record_count=0, block_allocation=None):

        filename, filetype = self.sanitize(filename, filetype)

        self.status = user_number                  # [0]    1 byte
        self.filename = filename.upper().ljust(8)  # [1-09] 8 bytes
        self.filetype = filetype.upper().ljust(3)  # [9-11] 3 bytes
        self.extent_low = extent_low               # [12]   1 byte
        self.reserved = 0                          # [13]   1 byte
        self.extent_high = extent_high             # [14]   1 byte
        self.record_count = record_count           # [15]   1 byte
        self.block_allocation = block_allocation if block_allocation else EMPTY_ALLOCATION
        self.extent = (32 * extent_high) + extent_low  # assume exm = 0

        # use 16 bit block allocation
        self.use_16bit = use_16bit

    def sanitize(self, filename, filetype):
        # sanitize filename and filetype
        # They may consist of any printable 7 bit ASCII
        # character but: < > . , ; : = ? * [ ].
        # The file name must not be empty
        # remove "<>.,;:=?*[]" from filename
        filename = re.sub(r'[<>.,;:=?*\[\]]', '', filename)
        filetype = re.sub(r'[.]', '', filetype)
        return filename,filetype

    def to_bytes(self, use_16bit=False):
        # Transform the directory entry to a bytearray
        try:
            entry = bytearray([self.status])
            entry += self.filename.encode('ascii')
            entry += self.filetype.encode('ascii')
            entry += bytearray([self.extent_low, self.extent_high])
            entry.append(self.reserved)
            entry.append(self.record_count)
            # Convert block_allocation to bytes based on use_16bit
            if use_16bit:
                entry += bytearray(CPMDirectoryEntry.encode16(self.block_allocation))
            else:
                entry += bytearray(self.block_allocation)
        except Exception as e:
            print(f"Error decoding directory entry: {e}")
            print(f"Entry: {self}")
            raise e
        return entry

    def is_unused(self):
        # Check if the directory entry is unused        
        return self.status == 0xE5

    def extent_number(self):
        # Adjust according to bit usage
        return (self.extent_high << 5) + (self.extent_low & 0x1F)

    def get_block_number(self, index):
        # Assuming block numbers are stored in two consecutive bytes
        if 2*index+1 < len(self.block_allocation):
            return self.block_allocation[2*index] + (self.block_allocation[2*index+1] << 8)
        else:
            return None  # Or handle index error

    @staticmethod
    def empty_entry(use_16bit=False):
        # return an empty entry a bytearray with all 0xE5
        return bytearray([0xE5] + [0] * 31)

    @staticmethod
    def from_bytes(use_16bit, data):
        # Create a CPMDirectoryEntry object from a bytearray
        user_number = data[0]
        filename = data[1:9].decode('ascii').rstrip()
        filetype = data[9:12].decode('ascii').rstrip()
        extent_low = data[12]
        reserved = data[13]
        extent_high = data[14]
        record_count = data[15]
        
        if use_16bit:
            block_allocation = CPMDirectoryEntry.decode16(data[16:32])
        else:
            block_allocation = list(data[16:32])
        return CPMDirectoryEntry(use_16bit, user_number, filename, filetype, extent_low, extent_high, record_count, block_allocation)

    @staticmethod
    def encode16(block_list):
        # Encode a list of block numbers as a bytearray
        ba = bytearray()
        for block in block_list:
            # Append each 16-bit block number as two bytes (little-endian format)
            ba.extend(block.to_bytes(2, 'little'))
        return ba

    @staticmethod
    def decode16(data):
        # Decode a bytearray into a list of block numbers
        block_list = []
        # Iterate through the bytearray two bytes at a time
        for i in range(0, len(data), 2):
            # Read two bytes from the bytearray, interpret them as a little-endian integer
            block = int.from_bytes(data[i:i+2], 'little')
            # Append the integer to the list
            block_list.append(block)
        return block_list

    @classmethod    
    def create_entries_for_file(cls, filename, filetype, data_length, disk):
        # Create directory entries for a file
        entries = []

        blocks_per_entry = 8 if disk.use_16bit else 16

        # adjust based on actual block size and records per block
        records_per_extent = disk.block_size * blocks_per_entry

        num_blocks = math.ceil(data_length / disk.block_size)
        num_extents = math.ceil(num_blocks / blocks_per_entry)
        
        # find free blocks
        disk.read_directory()
        blocks = disk.find_free_blocks(num_blocks)

        for i in range(num_extents):
            record_count = math.ceil(min(
                data_length, records_per_extent) / disk.sector_size)
            data_length -= record_count * disk.sector_size
            block_allocation = blocks[i * blocks_per_entry:i *
                                      blocks_per_entry + blocks_per_entry]
            
            # print(f"File: {filename}.{filetype} Extent: {i} Records: {record_count} Blocks: {block_allocation}")

            entries.append(cls(use_16bit=disk.use_16bit, 
                               filename=filename, 
                               filetype=filetype, 
                               extent_low=i,
                               record_count=record_count, 
                               block_allocation=block_allocation))

        return entries

    def __str__(self):
        return f"User: {self.status}, Filename: {self.filename}, Type: {self.filetype}, Extent: {self.extent_low}/{self.extent_high}, Records: {self.record_count}, Blocks: {self.block_allocation}"



