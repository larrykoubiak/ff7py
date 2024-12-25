class BitReader:
    def __init__(self, data):
        """Initialize the bit reader with a bytearray."""
        self.data = data
        self.bit_pos = 0  # Track the current position in bits

    def read(self, n):
        """Read the next n bits and return them as an integer."""
        result = 0
        for _ in range(n):
            if self.bit_pos == len(self.data) * 8:
                raise IndexError("Reached end of data")
            # Calculate byte index and bit index within that byte
            byte_index = self.bit_pos // 8
            bit_index = self.bit_pos % 8
            
            # Extract the bit
            bit = (self.data[byte_index] >> (7 - bit_index)) & 1
            result = (result << 1) | bit
            
            self.bit_pos += 1
        return result

    def read_byte(self):
        """Convenience method to read the next byte (8 bits)."""
        return self.read(8)

    def has_more(self):
        """Check if there are more bits to read."""
        return self.bit_pos < len(self.data) * 8
