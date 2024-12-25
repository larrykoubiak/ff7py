from io import BytesIO

class LZS:
    def __init__(self):
        self.size = 4096
        self.start = 0
        self.count = 0
        self.elems = bytearray(self.size)

    def _is_empty(self):
        return self.count == 0

    def _is_full(self):
        return self.count == self.size

    def _read_cb(self, offset, size, elem):
        realoffset = (offset + 18) & 0xFFF
        end = (self.start + self.count) & 0xFFF
        i = 0
        writeoffset = 0
        if (realoffset + size) > end and realoffset < end:
            value = 0
            max_read = end - realoffset
            while writeoffset < size:
                value = self.elems[realoffset + i]
                elem[writeoffset] = value
                writeoffset += 1
                i += 1
                if i == max_read:
                    i = 0
        else:
            for i in range(size):
                elem[writeoffset] = self.elems[(realoffset + i) & 0xFFF]
                writeoffset += 1

    def _write_cb(self, elem):
        end = (self.start + self.count) & 0xFFF
        self.elems[end] = elem
        if self._is_full():
            self.start = (self.start + 1) & 0xFFF
        else:
            self.count += 1

    def un_lzs(self, input_path):
        # Initialize
        self.start = 0
        self.count = 0
        self.elems[:] = bytearray(self.size)
        bytebuff = bytearray(18)
        offsetsize = bytearray(2)

        with open(input_path, 'rb') as f:
            reader = f.read
            filesize = int.from_bytes(reader(4), 'little')
            stream = BytesIO()
            while f.tell() != filesize:
                b_control = reader(1)
                if not b_control:
                    break
                for i in range(8):
                    mask = 1 << i
                    if (mask & ord(b_control)) > 0:
                        literal = reader(1)
                        if not literal:
                            break
                        self._write_cb(ord(literal))
                        stream.write(literal)
                    else:
                        offsetsize = reader(2)
                        if not offsetsize:
                            break
                        length = (offsetsize[1] & 0x0F) + 3
                        offset = offsetsize[0] + ((offsetsize[1] & 0xF0) << 4)
                        self._read_cb(offset, length, bytebuff)
                        for j in range(length):
                            self._write_cb(bytebuff[j])
                        stream.write(bytebuff[:length])
            stream.seek(0)
            return stream
