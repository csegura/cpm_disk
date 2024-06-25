from cpmdisk import CPMDisk


if __name__ == "__main__":

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
        
    disk.disk_map_free()
    disk.directory()
