# SPI_slave.py
from amaranth import *

class SPISlave(Elaboratable):
    def __init__(self, data_width=8):
        self.data_width = data_width
        
        self.sck = Signal()
        self.mosi = Signal()
        self.cs = Signal()
        self.data_in = Signal(data_width)
        self.miso = Signal()
        self.data_out = Signal(data_width)
        self.valid = Signal()

    def elaborate(self, platform):
        m = Module()
        
        sck_r = Signal()
        cs_r = Signal()
        m.d.sync += sck_r.eq(self.sck)
        m.d.sync += cs_r.eq(self.cs)

        sck_rise = Signal()
        sck_fall = Signal()
        m.d.comb += sck_rise.eq(~sck_r & self.sck)
        m.d.comb += sck_fall.eq(sck_r & ~self.sck)

        shift_reg = Signal(self.data_width)
        bit_cnt = Signal(range(self.data_width + 1))

        m.d.sync += self.valid.eq(0)

        with m.If(cs_r & ~self.cs):
            m.d.sync += [
                shift_reg.eq(self.data_in),
                self.miso.eq(self.data_in[-1]),
                bit_cnt.eq(0)
            ]
        with m.Elif(~cs_r):
            with m.If(sck_rise):
                m.d.sync += shift_reg.eq(Cat(self.mosi, shift_reg[:self.data_width-1]))
            with m.Elif(sck_fall):
                m.d.sync += self.miso.eq(shift_reg[-1])
                m.d.sync += bit_cnt.eq(bit_cnt + 1)
                
                with m.If(bit_cnt == self.data_width - 1):
                    m.d.sync += [
                        self.valid.eq(1),
                        self.data_out.eq(shift_reg)
                    ]
        with m.Else():
            m.d.sync += self.miso.eq(0)

        return m
