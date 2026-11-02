import zlib
import struct
import io
from PIL import Image

def decompress_cgbi(data: bytes) -> bytes:
    """
    Decodes Apple's proprietary CgBI-compressed PNG into standard PNG format.
    Handles uncompressed zlib stream and BGRA to RGBA channel swap.
    """
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        return data
        
    pos = 8
    is_cgbi = False
    chunks = []
    width, height = 0, 0
    idat_data = bytearray()
    
    while pos < len(data):
        if pos + 8 > len(data):
            break
        length = struct.unpack('>I', data[pos:pos+4])[0]
        chunk_type = data[pos+4:pos+8]
        chunk_data = data[pos+8:pos+8+length]
        pos += 12 + length
        
        if chunk_type == b'CgBI':
            is_cgbi = True
            continue
        elif chunk_type == b'IHDR':
            width, height = struct.unpack('>II', chunk_data[:8])
            chunks.append((chunk_type, chunk_data))
        elif chunk_type == b'IDAT':
            idat_data.extend(chunk_data)
        else:
            chunks.append((chunk_type, chunk_data))
            
    if not is_cgbi:
        return data
        
    # Decompress raw deflate without header (-15)
    try:
        decompressed = zlib.decompress(bytes(idat_data), -15)
    except Exception:
        try:
            decompressed = zlib.decompress(bytes(idat_data))
        except Exception:
            return data

    # Convert BGRA to RGBA scanlines
    bpp = 4
    scanline_len = 1 + width * bpp
    new_decompressed = bytearray()
    
    for y in range(height):
        start = y * scanline_len
        if start >= len(decompressed):
            break
        filter_type = decompressed[start:start+1]
        new_decompressed.extend(filter_type)
        line = bytearray(decompressed[start+1:start+scanline_len])
        
        # Swap B and R channels
        for i in range(0, len(line), 4):
            if i + 3 < len(line):
                b, g, r, a = line[i], line[i+1], line[i+2], line[i+3]
                line[i] = r
                line[i+2] = b
        new_decompressed.extend(line)

    # Re-compress standard IDAT with zlib
    new_idat = zlib.compress(bytes(new_decompressed))
    
    # Reassemble valid standard PNG
    out = io.BytesIO()
    out.write(b'\x89PNG\r\n\x1a\n')
    
    for c_type, c_data in chunks:
        if c_type == b'IEND':
            # Write new IDAT before IEND
            out.write(struct.pack('>I', len(new_idat)))
            out.write(b'IDAT')
            out.write(new_idat)
            crc = zlib.crc32(b'IDAT' + new_idat)
            out.write(struct.pack('>I', crc))
            
        out.write(struct.pack('>I', len(c_data)))
        out.write(c_type)
        out.write(c_data)
        crc = zlib.crc32(c_type + c_data)
        out.write(struct.pack('>I', crc))
        
    return out.getvalue()

def load_png(data: bytes) -> Image.Image:
    if b'CgBI' in data[:32]:
        try:
            normal_png = decompress_cgbi(data)
            return Image.open(io.BytesIO(normal_png)).convert("RGBA")
        except Exception:
            pass
    return Image.open(io.BytesIO(data)).convert("RGBA")

