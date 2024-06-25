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



