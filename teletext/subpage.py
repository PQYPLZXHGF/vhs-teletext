import base64

import numpy as np

from .packet import Packet
from .elements import Element, Displayable
from .printer import PrinterHTML


class Subpage(Element):

    def __init__(self, array=None, numbers=None, prefill=False):
        super().__init__((32, 42), array)
        if numbers is None:
            self._numbers = np.full((32,), fill_value=-100, dtype=np.int64)
        else:
            self._numbers = numbers

        if prefill:
            for i in range(25):
                self.row(i).mrag.row = i
                self._numbers[i] = -1
            self.displayable[:] = 0x20

    @property
    def numbers(self):
        return self._numbers[:]

    def row(self, row):
        return Packet(self._array[row, :])

    @property
    def mrag(self):
        return Packet(self._array[0, :]).mrag

    @property
    def header(self):
        return Packet(self._array[0, :]).header

    @property
    def fastext(self):
        return Packet(self._array[27, :]).fastext

    @property
    def displayable(self):
        return Displayable((24, 40), self._array[1:25,2:])

    @staticmethod
    def from_packets(packets):
        s = Subpage()

        for p in packets:
            s._array[p.mrag.row, :] = p[:]
            s._numbers[p.mrag.row] = -1 if p.number is None else p.number
        return s

    @property
    def packets(self):
        for n, a in enumerate(self._array):
            if self._numbers[n] > -100:
                yield Packet(a, number=None if self._numbers[n] < 0 else self._numbers[n])

    @property
    def url(self):
        data = base64.b64encode(Element((25, 40), self._array[0:25,2:]).sevenbit, b'-_').decode('ascii')
        return f'0:{data}'


    def to_html(self, pages_set):
        lines = []

        lines.append(f'<div class="subpage" id="{self.header.subpage:04x}">')
        p = PrinterHTML(self.header.displayable[:])
        p.anchor = f'#{self.header.subpage:04x}'
        lines.append(f'    <span class="pgnum">P{self.mrag.magazine}{self.header.page:02x}{str(p)}')

        for i in range(0,24):
            # only draw the line if previous line does not contain double height code
            if i == 0 or np.all(self.displayable[i-1,:] != 0x0d):
                p = PrinterHTML(self.displayable[i,:], pages_set=pages_set)
                if i == 23:
                    p.fastext = True
                    p.links = [f'{l.magazine}{l.page:02x}' for l in self.fastext.links]
                lines.append(str(p))

        lines.append('</div>')

        return '\n'.join(lines)

