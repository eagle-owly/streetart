from io import BytesIO


class Aco:

    def __init__(self):
        self.colors = []

    def add(self, name, r, g, b):
        self.colors.append({'r': r, 'g': g, 'b': b, 'name': name})

    @staticmethod
    def _n(x):
        return b'%c%c' % ((x >> 8) & 0xff, x & 0xff)

    def as_bytea(self):
        output = BytesIO()

        output.write(self._n(1))
        output.write(self._n(len(self.colors)))

        for color in self.colors:
            output.write(self._n(0))
            output.write(self._n((color['r'] << 8) | color['r']))
            output.write(self._n((color['g'] << 8) | color['g']))
            output.write(self._n((color['b'] << 8) | color['b']))
            output.write(self._n(0))

        output.write(self._n(2))
        output.write(self._n(len(self.colors)))

        for color in self.colors:
            output.write(self._n(0))
            output.write(self._n((color['r'] << 8) | color['r']))
            output.write(self._n((color['g'] << 8) | color['g']))
            output.write(self._n((color['b'] << 8) | color['b']))
            output.write(self._n(0))
            output.write(self._n(0))
            output.write(self._n(len(color['name']) + 1))

            for c in color['name']:
                output.write(self._n(ord(c)))

            output.write(self._n(0))

        output.seek(0)
        return output
