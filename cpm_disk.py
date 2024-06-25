

# Summary table for common disk sizes in CP/M, showcasing typical values for `dsm`, `drm`, `off`, `bsh`, and `blm`.
# This table provides a quick reference for these key DPB parameters for various disk formats:
#
# | Disk Size  | DSM  | DRM  | OFF | BSH | BLM | Remarks                                        |
# |------------|------|------|-----|-----|-----|------------------------------------------------|
# | 8" SSSD    | 242  | 63   | 2   | 3   | 7   | Single-Sided Single-Density, ~250KB            |
# | 8" DSSD    | 494  | 127  | 2   | 3   | 7   | Double-Sided Single-Density, ~500KB            |
# | 8" DSDD    | 988  | 127  | 2   | 3   | 7   | Double-Sided Double-Density, ~1MB              |
# | 5.25" SSDD | 242  | 63   | 1   | 3   | 7   | Single-Sided Double-Density, ~180KB            |
# | 5.25" DSDD | 488  | 127  | 1   | 3   | 7   | Double-Sided Double-Density, ~360KB            |
# | 5.25" DSDD | 720  | 255  | 2   | 4   | 15  | Double-Sided Double-Density, IBM PC, ~720KB    |
# | 3.5" DSDD  | 720  | 255  | 2   | 4   | 15  | Double-Sided Double-Density, IBM PC, ~720KB    |
# | 3.5" DSHD  | 1440 | 255  | 2   | 4   | 15  | Double-Sided High-Density, ~1.44MB             |

# **Notes:**
# - **BSH (Block Shift)**: Used to calculate block size as `2^BSH * 128` bytes.
# - **BLM (Block Mask)**: Typically `2^BSH - 1`.
# - **DSM (Disk Storage Module)**: Indicates the highest numbered data block.
# - **DRM (Directory Maximum)**: Highest numbered directory entry.
# - **OFF (Offset)**: Number of tracks reserved for the system.

import os
import sys
import math

from cpm_dir import CPMDirectoryEntry

EMPTY_DIR = 0xE5
EMPTY_BYTE = b'\x00'

# Reserved Area - If there are reserved tracks, the first `OFF` tracks are reserved for the system.
# Directory Area - The directory area starts at the beginning of the first reserved track.
# Data Area - The data area starts immediately after the directory area.


class CPMDisk:
    def __init__(self, drivename, tracks, sectors_per_track, sector_size, block_size, bsh, drm, off):
        self.drivename = drivename
        self.tracks = tracks
        self.sectors_per_track = sectors_per_track
        self.sector_size = sector_size
        self.block_size = block_size
        self.bsh = bsh
        self.drm = drm   # 0 based
        self.off = off

        self.size = tracks * sectors_per_track * sector_size

        # calculate the total number of usable blocks on the disk
        # only for reference purposes (not used)
        self.phisical_blocks = (tracks * sectors_per_track *
                                sector_size) / block_size

        # reserved blocks - blocks begins after this tracks
        self.off_blocks = (self.off * self.sectors_per_track *
                           self.sector_size) // block_size

        # calculate the start of the directory (this are counted as blocks)
        # block 0 starts directory
        self.directory_start = self.off * self.sectors_per_track * self.sector_size

        # Each directory entry is 32 bytes
        self.directory_size = self.drm * 32
        self.directory_blocks = math.ceil(self.directory_size / block_size)

        # use only full blocks
        self.total_blocks = int(self.phisical_blocks)
        # if self.phisical_blocks % 1 == 0 else int(
        #    self.phisical_blocks)

        # self.dir_block = self.directory_size // block_size

        # self.directory_start + self.directory_size
        self.data_area_start = self.directory_blocks * self.block_size
        self.total_usable_blocks = ((
            self.size - self.data_area_start) // block_size) + 1
        # ((self.off * self.sectors_per_track * self.sector_size) //
        # block_size) - (self.directory_size // block_size)

        self.first_usable_block = self.total_blocks - self.total_usable_blocks + 1

        self.sectors_per_block = block_size // sector_size
        self.use_16bit = self.total_usable_blocks > 255
        self.directory = []
        
        self.debug = False

    def disk_info(self):
        print(f"Disk: {self.drivename}")
        print(f"Tracks: {self.tracks}")
        print(f"Sectors per track: {self.sectors_per_track}")
        print(f"Sector size: {self.sector_size}")
        print(f"Block size: {self.block_size}")
        print(
            f"Total blocks: {self.total_blocks} - ({self.total_blocks * self.block_size} bytes)")
        print(f"Reserved blocks: {self.off_blocks}")
        print(f"Directory blocks: {self.directory_blocks}")
        print(
            f"Total usable blocks: {self.total_usable_blocks} - ({self.total_usable_blocks * self.block_size} bytes)")
        print(
            f"First usable block: {self.first_usable_block} - {self.track_sector(self.first_usable_block)} ")
        print(f"Sectors per block: {self.sectors_per_block}")

        print(
            f"Directory start: {self.directory_start} - {self.directory_start:08x}")
        print(
            f"Data area start: {self.data_area_start} - {self.data_area_start:08x}")
        print(f"Directory blocks: {self.directory_blocks}")
        print(f"Directory size: {self.directory_size}")
        print(f"Directory max entries: {self.drm}")

        print(f"Size: {self.size} bytes")

    def initialize_disk(self):
        with open(self.drivename, 'wb') as f:
            f.write(EMPTY_BYTE * self.size)
        # generate an empty directory
        self.directory = []
        for entry_number in range(self.drm + 1):
            entry = CPMDirectoryEntry.empty_entry(self.use_16bit)
            self.write_directory_entry(
                entry_number, entry) #.to_bytes(self.use_16bit))
            self.directory.append(entry)

    # -------------------------
    # block management
    # -------------------------

    def block(self, track, sector):
        """Convert track and sector to block number."""
        block = (track * self.sectors_per_track + sector) >> self.bsh
        block -= self.off_blocks
        return block

    def track_sector(self, block):
        """Convert block number to track and sector."""
        block += self.off_blocks
        # linear_sector_number = block * self.sectors_per_block
        # cpm calculates the linear sector number as follows:
        linear_sector_number = block << self.bsh
        track = linear_sector_number // self.sectors_per_track
        sector = linear_sector_number % self.sectors_per_track
        return track, sector

    def track_sector_offset(self, track, sector):
        """ Convert track and sector to offset in the disk."""
        offset = (track * self.sectors_per_track *
                  self.sector_size) + (sector * self.sector_size)
        return offset

    def offset_to_track_sector(self, offset):
        """ Convert offset to track and sector."""
        track = offset // (self.sectors_per_track * self.sector_size)
        sector = (offset % (self.sectors_per_track *
                  self.sector_size)) // self.sector_size
        return track, sector

    def read_position(self, position, size):
        """ Read data from a position in the disk."""
        try:
            with open(self.drivename, 'rb') as f:
                f.seek(position)
                return f.read(size)
        except Exception as e:
            print(f"DiskError: Error reading position {position:08x} - {size} bytes")
            print(e)
            exit(1)            

    def write_position(self, position, data):
        """ Write data to a position in the disk."""
        try: 
            with open(self.drivename, 'r+b') as f:
                f.seek(position)
                f.write(data)
        except Exception as e:
            print(f"DiskError: Error writing position {position:08x} - {len(data)} bytes")
            print(e)
            exit(1)

    def read_block(self, block_number):
        """ Read a block from the disk."""
        position = (block_number + self.off_blocks) * self.block_size
        if self.debug:
            print(f"Reading block {block_number} {position:08x}")        
        return self.read_position(position, self.block_size)

    def write_block(self, block_number, data):
        """ Write a block to the disk."""
        if len(data) > self.block_size:
            raise ValueError("Data exceeds block size")
        position = (block_number * self.block_size) + self.directory_start
        if self.debug:
            print(f"Writing block {block_number} {position:08x} len {len(data)}")        
        # Pad data to full block size
        self.write_position(position, data.ljust(self.block_size, EMPTY_BYTE))

    # -------------------------
    # directory management
    # -------------------------
    
    # 0x2000 - 0x1A00 = 0x0600 = 1536 /32 = 48 entries
    # 0x2200 - 0x1A00 = 0x0800 = 2048 /32 = 64 entries
    def read_directory(self):
        """ Read the directory entries from the disk."""
        self.directory = []
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            if entry_data[0] != EMPTY_DIR:
                try:
                    entry = CPMDirectoryEntry.from_bytes(
                        self.use_16bit, entry_data)
                    self.directory.append(entry)
                except Exception as e:
                    print(entry)
                    print(entry_data)
                    print(
                        f"Error reading directory entry {entry_number}/{self.drm}")
                    print(e)

    def find_free_directory_entry(self):
        """ Find a free directory entry."""
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            if entry_data[0] == EMPTY_DIR:
                return entry_number
        return None

    def read_directory_entry(self, entry_number):
        """ Read a directory entry from the disk."""
        position = self.directory_start + entry_number * 32
        # Read only the first 32 bytes for the directory entry
        return self.read_position(position, 32)

    def write_directory_entry(self, entry_number, entry_data):
        """ Write a directory entry to the disk."""
        position = self.directory_start + entry_number * 32
        self.write_position(position, entry_data)

    def get_ditectory_entry_from_block(self, block_number):
        """ Get the directory entry number for a block number."""
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            entry = CPMDirectoryEntry.from_bytes(self.use_16bit, entry_data)
            if block_number in entry.block_allocation:
                return entry_number
        return None

    def is_valid_entry_data(self, entry_data):
        """ Check if the directory entry data is valid."""
        return entry_data[0] != EMPTY_DIR

    def get_used_blocks_from_directory(self):
        """ Get a list of used blocks from the directory entries. """
        used_blocks = []
        for entry in self.directory:
            for block in entry.block_allocation:
                if block != 0:
                    used_blocks.append(block)
        return used_blocks

    def get_blocks_status_from_directory(self):
        """ Get a list true-free/false-occupied for each block status. """
        # Initialize all blocks as free
        block_status = [True] * (self.total_usable_blocks + 1)
        used_blocks = self.get_used_blocks_from_directory()
        if self.debug:
            print(f"Used blocks: {used_blocks}")
        # Mark first blocks as False
        for block in range(0, self.directory_blocks):
            # print(f"Marking block {block} as False")
            block_status[block] = False

        # Mark used blocks as False
        for block in used_blocks:
            if 0 < block <= self.total_usable_blocks:
                block_status[block] = False
        return block_status

    def find_free_blocks(self, number_of_blocks):
        number = self.get_blocks_status_from_directory()
        free_blocks = []

        for number, status in enumerate(number):
            if status:
                free_blocks.append(number)
                number_of_blocks -= 1
            if number_of_blocks == 0:
                break

        if number_of_blocks > 0:
            raise Exception("Not enough free space on the disk")

        return free_blocks

    # -------------------------
    # file management
    # -------------------------

    def find_blocks(self, data):
        """ Find free blocks for a file."""
        # Allocate blocks for the file
        blocks_needed = (
            len(data) + self.block_size - 1) // self.block_size

        blocks = []
        for block_number in range(self.first_usable_block, self.total_blocks):
            if len(blocks) >= blocks_needed:
                break
            block_data = self.read_block(block_number)
            if block_data == EMPTY_DIR * self.block_size:
                blocks.append(block_number)

        if len(blocks) < blocks_needed:
            raise Exception("Not enough free space on the disk")
        return blocks

    def write_file(self, filename, filetype, data):
        """ Write a file to the disk."""
        self.read_directory()
        # Create directory entries
        entries = CPMDirectoryEntry.create_entries_for_file(
            filename, 
            filetype, 
            len(data), 
            self)

        blocks = []
        for entry in entries:
            blocks.extend(entry.block_allocation)

        # Write the file data to the allocated blocks
        for i, block in enumerate(blocks):
            start = i * self.block_size
            end = start + self.block_size
            self.write_block(block, data[start:end])

        # create directory entries
        for entry in entries:
            num_entry = self.find_free_directory_entry()
            self.write_directory_entry(
                num_entry, entry.to_bytes(self.use_16bit))

        if self.debug:
            print(f"Writing file {filename} {filetype} {blocks}")

    def read_file(self, filename, filetype):
        entries = []        
        print(f"Reading file {filename}.{filetype}")
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            entry = CPMDirectoryEntry.from_bytes(self.use_16bit, entry_data)
            if entry.filename.strip() == filename.upper() and entry.filetype.strip() == filetype.upper():
                entries.append(entry)

        if len(entries) > 0:
            file_data = bytearray()
            for entry in entries:
                for block in entry.block_allocation:
                    if block == 0:
                        break
                    file_data.extend(self.read_block(block))
            return bytes(file_data)        
        return None
        

    def put_file(self, filename):
        """ Put a file on the disk."""
        # load a file into the disk
        try:
            with open(filename, 'rb') as f:
                data = f.read()
            # extract the file name and extension
            # without path
            file_name, file_type = os.path.splitext(os.path.basename(filename))
            if self.debug:
                print(f"Putting file {file_name} with extension {file_type}")
            self.write_file(file_name.strip(), file_type.strip("."), data)
        except Exception as e:
            print(f"Error reading file {filename}")
            print(e)
            exit(1)

    def get_file(self, filename):
        """ Get a file from the disk."""
        try:
            file_name, file_type = os.path.splitext(os.path.basename(filename))
            data = self.read_file(file_name.strip(), file_type.strip("."))
            if data:
                with open(filename, 'wb') as f:
                    f.write(data)
                print(f"File {filename} written - size {len(data)} bytes")
            else:   
                print(f"File '{filename}' not found.")        
        except Exception as e:
            print(f"Error writing file {filename}")
            print(e)
            exit(1)

    def delete_file(self, filename):
        """ Delete a file from the disk."""
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            entry = CPMDirectoryEntry.from_bytes(self.use_16bit, entry_data)
            if entry.filename.strip() == filename.upper():
                # Zero out the directory entry
                self.write_directory_entry(entry_number, EMPTY_DIR * 32)

                # Optionally, zero out the data blocks
                for block in entry.block_allocation:
                    if block == 0:
                        break
                    self.write_block(block, EMPTY_DIR * self.block_size)
                return
        raise FileNotFoundError(f"File '{filename}' not found.")

    # -------------------------
    # System tools
    # -------------------------  
    
    def putsys(self, filename):
        """ Put a file on the disk as a system file."""
        with open(filename, 'rb') as f:
            data = f.read()
        if len(data) > 2048:
            raise ValueError("File too large for system file")
        with open(self.drivename, 'r+b') as f:
            f.seek(0)
            f.write(data)

    def put_at_block(self, filename, block):
        """ Put a file on the disk starting at a block."""
        with open(filename, 'rb') as f:
            data = f.read()
        print(f"Writing file {filename} at block {block} ...")
        print(
            f"Data size: {len(data)} bytes - {len(data) / self.block_size:.2f} blocks")
        # write the data on blocks starting at block
        for i, start in enumerate(range(0, len(data), self.block_size)):
            end = start + self.block_size
            self.write_block(block + i, data[start:end])
            print(
                f"Writing block {block + i} Start: {start} 0x{start:08x} - {end} 0x{end:08x}")
            print(f"Track sector {self.track_sector(block + i)}")

    def put_file_at_offset(self, filename, offset):
        """ Put a file on the disk starting at an offset."""
        with open(filename, 'rb') as f:
            data = f.read()
        print(f"Writing file {filename} at offset {offset} ...")
        with open(self.drivename, 'r+b') as f:
            f.seek(offset)
            f.write(data)
        print(
            f"{filename} written at start 0x{offset:08x} - 0x{offset+len(data):08x} - len {len(data)} 0x{len(data):08x} bytes")
        return len(data)

    # -------------------------
    # disk utilities
    # -------------------------

    def list_directory(self):
        print("Directory Listing:")
        print("-" * 110)
        print(
            f"{'Entry':<6} {'Usr':<3} {'Ext':<3} {'Filename':<9} {'Type':<5} {'Rec':<4} {'Blocks':<50} {'Size':<10}")
        print("-" * 110)
        entries_used = 0
        entries_total = 0

        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            if self.is_valid_entry_data(entry_data):
                entry = CPMDirectoryEntry.from_bytes(
                    self.use_16bit, entry_data)
                if entry.filename.strip() != '':
                    print(f"{entry_number:<6} {entry.status:<3} {entry.extent_number():<3} {entry.filename:<9} {entry.filetype:<5} {entry.record_count:02x} - ", end="")
                    size = 0
                    if self.use_16bit:
                        for i in range(0, 8):
                            print(f"{entry.block_allocation[i]:04x}", end=" ")
                            if entry.block_allocation[i] != 0:
                                size += self.block_size
                    else:
                        for i in range(0, 16):
                            print(f"{entry.block_allocation[i]:02x}", end=" ")
                            if entry.block_allocation[i] != 0:
                                size += self.block_size
                    print(f" - {size/1024:.2f} Kb")
                entries_used += 1
            entries_total += 1

        print("-" * 110)
        print(f"Total entries: {entries_total} - Used entries: {entries_used}")

    def raw_directory(self):
        print("Directory Listing:")
        print("-" * 140)
        entries_used = 0
        entries_total = 0
        
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            if self.is_valid_entry_data(entry_data):
                for byte in entry_data:
                    print(f"{byte:02x}", end=" ")
                print("  ", end="   ")
                for byte in entry_data:
                    print(f"{chr(byte) if byte > 0x20 else '.'}", end=" ")
                print()
                entries_used += 1
            entries_total += 1

        print("-" * 110)
        print(f"Total entries: {entries_total} - Used entries: {entries_used}")

    def get_file_entry(self, filename):
        for entry_number in range(self.drm):
            entry_data = self.read_directory_entry(entry_number)
            entry = CPMDirectoryEntry.from_bytes(self.use_16bit, entry_data)
            if entry.filename.strip() == filename.upper():
                return entry
        return None

    def get_file_info(self, filename):
        """ Get information about a file on the disk. """
        entry = self.get_file_entry(filename)
        if entry:
            return {
                "filename": entry.filename.strip(),
                "filetype": entry.filetype.strip(),
                "size": entry.record_count,
                "blocks": entry.block_allocation,
                "position": entry.extent_low + entry.extent_high * 128,
                "1 pos": entry.block_allocation[0] * self.block_size
            }
        return None

    def disk_map(self):
        """ Display a map of the disk showing used and free blocks. """
        print("Disk Map:")
        print("-" * 70)
        print("Block:  Status:")
        print("-" * 70)
        for block in range(self.total_blocks):
            block_data = self.read_block(block)
            if block_data == b'\x00' * self.block_size:
                status = "Free"
            else:
                status = "Used"
            print(f"{block:>6} {status}")
        print("-" * 70)

    def disk_map_visual(self):
        """ Display a visual map of the disk showing used and free blocks.
            an * indicates a used block, a . indicates a free block.
            in a matrix format.
        """
        block = 0
        print(" "*26, end="")
        for sector in range(self.sectors_per_track):
            print(f"{sector:03d}", end=" ")
        print("")
        # a line for each track
        for track in range(self.tracks):
            # a character for each sector
            print(f"Track {track:02d} - {block:>6} 0x{block:04x}: ", end="")

            for sector in range(self.sectors_per_track):
                block = self.block(track, sector)
                print(f"{block:>3}", end=" ")
            print(f" 0x{block-1:04x}")

            print(" "*26, end="")
            for sector in range(self.sectors_per_track):
                # block = track * self.sectors_per_track + sector
                block = self.block(track, sector)
                if block < self.first_usable_block:
                    status = "R"
                else:
                    entry = self.get_ditectory_entry_from_block(block)
                    if entry:
                        status = entry
                    else:
                        status = "."

                print(f"{status:>3}", end=" ")
            print()

    def disk_map_free(self):
        """ Display a visual map of the disk showing used and free blocks.
            an * indicates a used block, a . indicates a free block.
            in a matrix format.
        """
        free_blocks = self.get_blocks_status_from_directory()
        block = 0
        # print(free_blocks, len(free_blocks))
        print(" "*26, end="")
        for sector in range(self.sectors_per_track):
            print(f"{sector:03d}", end=" ")
        print("")
        # a line for each track
        for track in range(self.tracks):
            # a character for each sector
            print(f"Track {track:02d} - {block:>6} 0x{block:04x}: ", end="")

            for sector in range(self.sectors_per_track):
                # block = track * self.sectors_per_track + sector
                block = self.block(track, sector)
                if block <= self.total_blocks:
                    if free_blocks[block]:
                        status = "."
                    else:
                        status = "*"
                else:
                    status = "-"
                print(f"{status:>3}", end=" ")

            print()

    def dump_block(self, block_number):
        block_data = self.read_block(block_number)
        offset = block_number * self.block_size
        print(f"Block {block_number} - Offset 0x{offset:08x} - Size {len(block_data)} bytes")
        t, s = 0, 0
        # show block in 32 bytes chunks
        for i in range(0, len(block_data), 32):
            track, sector = self.offset_to_track_sector(offset + i)
            if t != track or s != sector:
                t, s = track, sector
                print(f"Track {track:02d} 0x{track:02x} Sector {sector:02d} 0x{sector:02x}")
            
            print(f" 0x{offset + i:08x} :: ", end="")
            # show 32 bytes in hex and ascii
            for j in range(i, i + 32):
                print(f"{block_data[j]:02x}", end=" ")
            print(" ", end="")
            for j in range(i, i + 32):
                print(f"{chr(block_data[j]) if block_data[j] > 0x20 else '.'}", end="")
            print("")

        