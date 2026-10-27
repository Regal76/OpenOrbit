path = 'C:/Users/tusit/AppData/Local/DarkOrbit Unity/GameAssembly.dll'
with open(path, 'r+b') as f:
    f.seek(0x00735992)
    old = f.read(7)
    assert old == bytes([0xC7, 0x04, 0x24, 0xCD, 0xCC, 0x4C, 0x3E]), f"Unexpected bytes: {old.hex()}"
    f.seek(0x00735992)
    f.write(bytes([0xC7, 0x04, 0x24, 0x00, 0x00, 0x00, 0x00]))
    f.flush()

with open(path, 'rb') as f:
    f.seek(0x00735992)
    new_b = f.read(8)
    print('New on-disk bytes at 0x00735992:', new_b.hex())
    assert new_b[:7] == bytes([0xC7, 0x04, 0x24, 0x00, 0x00, 0x00, 0x00])
print('Disk patch applied successfully!')
