# SPI_master.py
from amaranth import *

class SPIMaster(Elaboratable):
    def __init__(self, clk_div=4, data_width=8):
        self.clk_div = clk_div
        self.data_width = data_width
        
        self.start = Signal()
        self.data_in = Signal(data_width)
        self.miso = Signal()
        self.sck = Signal(reset=0)
        self.mosi = Signal()
        self.cs = Signal(reset=1)
        self.data_out = Signal(data_width)
        self.ready = Signal(reset=1)
        self.valid = Signal()

    def elaborate(self, platform):
        m = Module()
        clk_cnt = Signal(range(self.clk_div))
        bit_cnt = Signal(range(self.data_width + 1))
        shift_reg = Signal(self.data_width)

        m.d.sync += self.valid.eq(0)

        with m.FSM(name="spi_master"):
            with m.State("IDLE"):
                m.d.sync += [
                    self.cs.eq(1),
                    self.sck.eq(0),
                    self.ready.eq(1)
                ]
                with m.If(self.start):
                    m.d.sync += [
                        self.ready.eq(0),
                        self.cs.eq(0),
                        shift_reg.eq(self.data_in),
                        self.mosi.eq(self.data_in[-1]),
                        clk_cnt.eq(0),
                        bit_cnt.eq(0)
                    ]
                    m.next = "WAIT_LEAD"

            with m.State("WAIT_LEAD"):
                with m.If(clk_cnt == (self.clk_div // 2) - 1):
                    m.d.sync += [
                        clk_cnt.eq(0),
                        self.sck.eq(1),
                        shift_reg.eq(Cat(self.miso, shift_reg[:self.data_width-1])) 
                    ]
                    m.next = "WAIT_TRAIL"
                with m.Else():
                    m.d.sync += clk_cnt.eq(clk_cnt + 1)

            with m.State("WAIT_TRAIL"):
                with m.If(clk_cnt == (self.clk_div // 2) - 1):
                    m.d.sync += [
                        clk_cnt.eq(0),
                        self.sck.eq(0),
                        bit_cnt.eq(bit_cnt + 1)
                    ]
                    with m.If(bit_cnt == self.data_width - 1):
                        m.next = "END"
                    with m.Else():
                        m.d.sync += self.mosi.eq(shift_reg[-1])
                        m.next = "WAIT_LEAD"
                with m.Else():
                    m.d.sync += clk_cnt.eq(clk_cnt + 1)

            with m.State("END"):
                with m.If(clk_cnt == (self.clk_div // 2) - 1):
                    m.d.sync += [
                        self.valid.eq(1),
                        self.data_out.eq(shift_reg),
                        self.cs.eq(1),
                        self.ready.eq(1)
                    ]
                    m.next = "IDLE"
                with m.Else():
                    m.d.sync += clk_cnt.eq(clk_cnt + 1)

        return m
