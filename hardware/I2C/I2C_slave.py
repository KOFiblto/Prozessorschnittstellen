# I2C_slave.py
from amaranth import *

class I2CSlave(Elaboratable):
    def __init__(self, address=0x50):
        self.address = address
        self.scl = Signal(reset=1)
        self.sda_i = Signal(reset=1)
        self.sda_oe = Signal(reset=0) # Output Enable (Active High)
        self.data_out = Signal(8)
        self.valid = Signal()
        
        # Debug signals exposed as instance variables
        self.sda_r = Signal(3, reset=7) # Reset to all 1s (binary 111)
        self.scl_r = Signal(3, reset=7) # Reset to all 1s (binary 111)
        self.start_cond = Signal()
        self.stop_cond = Signal()
        self.scl_rising = Signal()
        self.scl_falling = Signal()
        self.bit_cnt = Signal(range(10))
        self.shift_reg = Signal(8)

    def elaborate(self, platform):
        m = Module()
        
        # Synchronization
        m.d.sync += [self.sda_r.eq(Cat(self.sda_i, self.sda_r[:2])),
                     self.scl_r.eq(Cat(self.scl, self.scl_r[:2]))]
        
        m.d.comb += [
            self.scl_rising.eq(self.scl_r[1] & ~self.scl_r[2]),
            self.scl_falling.eq(~self.scl_r[1] & self.scl_r[2]),
            self.start_cond.eq(self.scl_r[1] & (~self.sda_r[1] & self.sda_r[2])), # SCL high, SDA falling
            self.stop_cond.eq(self.scl_r[1] & (self.sda_r[1] & ~self.sda_r[2]))   # SCL high, SDA rising
        ]

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += [
                    self.sda_oe.eq(0),
                    self.valid.eq(0)
                ]
                with m.If(self.start_cond):
                    m.d.sync += [
                        self.bit_cnt.eq(0),
                        self.shift_reg.eq(0)
                    ]
                    m.next = "ADDR"
            
            with m.State("ADDR"):
                with m.If(self.start_cond):
                    m.d.sync += [self.bit_cnt.eq(0), self.shift_reg.eq(0)]
                    m.next = "ADDR"
                with m.Elif(self.stop_cond):
                    m.next = "IDLE"
                with m.Elif(self.scl_rising):
                    m.d.sync += [self.shift_reg.eq(Cat(self.sda_r[1], self.shift_reg[:7])),
                                 self.bit_cnt.eq(self.bit_cnt + 1)]
                with m.Elif(self.scl_falling):
                    with m.If(self.bit_cnt == 8):
                        with m.If(self.shift_reg[1:] == self.address):
                            m.d.sync += [self.sda_oe.eq(1), self.bit_cnt.eq(0)] # ACK
                            m.next = "DATA"
                        with m.Else():
                            m.next = "IDLE"
            
            with m.State("DATA"):
                with m.If(self.start_cond):
                    m.d.sync += [self.bit_cnt.eq(0), self.shift_reg.eq(0)]
                    m.next = "ADDR"
                with m.Elif(self.stop_cond):
                    m.next = "IDLE"
                with m.Elif(self.scl_rising):
                    with m.If(self.bit_cnt == 0):
                        m.d.sync += self.bit_cnt.eq(1)
                    with m.Elif(self.bit_cnt < 9):
                        m.d.sync += [self.shift_reg.eq(Cat(self.sda_r[1], self.shift_reg[:7])),
                                     self.bit_cnt.eq(self.bit_cnt + 1)]
                with m.Elif(self.scl_falling):
                    with m.If(self.bit_cnt == 1):
                        m.d.sync += self.sda_oe.eq(0) # Release ACK
                    with m.Elif(self.bit_cnt == 9):
                        m.d.sync += [self.valid.eq(1), self.data_out.eq(self.shift_reg),
                                     self.sda_oe.eq(1)] # ACK
                        m.next = "WAIT_STOP"
                    
            with m.State("WAIT_STOP"):
                m.d.sync += self.valid.eq(0)
                with m.If(self.start_cond):
                    m.d.sync += [self.sda_oe.eq(0), self.bit_cnt.eq(0)]
                    m.next = "ADDR"
                with m.Elif(self.stop_cond):
                    m.d.sync += self.sda_oe.eq(0)
                    m.next = "IDLE"
                with m.Elif(self.scl_falling):
                    m.d.sync += [
                        self.sda_oe.eq(0),
                        self.bit_cnt.eq(1)
                    ]
                    m.next = "DATA"

        return m