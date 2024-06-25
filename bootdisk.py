from cpmdisk import CPMDisk


if __name__ == "__main__":

    disk = CPMDisk("boot.dsk",
                   77,      # 75 tracks
                   26,      # 26 sectors per track
                   128,     # 128 bytes per sector
                   1024,    # 1024 bytes per block (1 block = 8 sectors)
                   3,       # bsh - block shift
                   7,       # blm - block mask
                   242,     # dsm - max data blocks
                   64,      # drm - max directory entries
                   2)       # off - reserved tracks
    disk.initialize_disk()

    # BOOT2   0000..007F  0000-007F   128/080  = 0.1K
    # CCP     0080..087F  DB00-E2FF   2048/800 = 2K
    # BDOS    0880..167F  E300-F0FF   3584/E00 = 3.5K
    # BIOS    1680..19FF  F100-F47F   896/380 = 0.8K

    # 128 * 26 * 2 = 6656 bytes

    # cold start loader
    files = [
        {"name": "../cpm_bios/boot.bin", "address": 0x0000},
        {"name": "../cpm_bios/ccp.bin", "address": 0x0080},
        {"name": "../cpm_bios/bdos.bin", "address": 0x0880},
        {"name": "../cpm_bios/bios.bin", "address": 0x1680}
    ]

    DIR_BIN = "../cpm_bios/bin"

    offset = disk.put_file_at_offset(DIR_BIN + "/boot.bin", 0x0000)
    trak, sector = disk.offset_to_track_sector(offset)
    print(f"boot.bin ends at {offset:04X} - T: {trak:02X} S: {sector:02X}")

    offset = disk.track_sector_offset(0, 2)

    # CCP and BDOS
    offset += disk.put_file_at_offset(DIR_BIN + "/ccp.bin", offset)
    trak, sector = disk.offset_to_track_sector(offset)
    print(f"ccp.bin ends at {offset:04X} - T: {trak:02X} S: {sector:02X}")

    offset += disk.put_file_at_offset(DIR_BIN + "/bdos.bin", offset)
    trak, sector = disk.offset_to_track_sector(offset)
    print(f"bdos.bin ends at {offset:04X} - T: {trak:02X} S: {sector:02X}")

    # disk.disk_map_free()
