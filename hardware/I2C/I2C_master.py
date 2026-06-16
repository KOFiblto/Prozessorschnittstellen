# I2C_master.py
from amaranth import *

class I2CMaster(Elaboratable):
    def __init__(self, clk_freq=1000000, i2c_freq=100000):
        self.divider = clk_freq // (i2c_freq * 4)
        self.scl = Signal(reset=1)
        self.sda_oe = Signal(reset=0) # Open-drain drive
        self.start = Signal()
        self.addr = Signal(7)
        self.data = Signal(8)
        self.ready = Signal(reset=1)
        
        # Debug signals exposed as instance variables
        self.bit_cnt = Signal(range(20)) # 0 to 19
        self.shift_reg = Signal(16) # [Addr(7), RW(1), Data(8)]
        self.div_cnt = Signal(range(self.divider))

    def elaborate(self, platform):
        m = Module()

        with m.FSM(name="i2c_master"):
            with m.State("IDLE"):
                m.d.sync += [
                    self.scl.eq(1), 
                    self.sda_oe.eq(0), 
                    self.ready.eq(1)
                ]
                with m.If(self.start):
                    m.d.sync += [
                        self.ready.eq(0),
                        self.shift_reg.eq(Cat(self.data, 0, self.addr)),
                        self.sda_oe.eq(1), # Start Condition
                        self.bit_cnt.eq(0),
                        self.div_cnt.eq(0)
                    ]
                    m.next = "TX"

            with m.State("TX"):
                with m.If(self.div_cnt < self.divider - 1):
                    m.d.sync += self.div_cnt.eq(self.div_cnt + 1)
                with m.Else():
                    m.d.sync += [self.div_cnt.eq(0), self.scl.eq(~self.scl)]
                    
                    with m.If(self.scl == 1): # Falling edge
                        m.d.sync += self.bit_cnt.eq(self.bit_cnt + 1)
                        
                        with m.If(self.bit_cnt == 7):
                            m.d.sync += [
                                self.sda_oe.eq(0),
                                self.shift_reg.eq(self.shift_reg << 1)
                            ]
                        with m.Elif(self.bit_cnt == 8):
                            m.d.sync += self.sda_oe.eq(0) # Release SDA for Address ACK
                        with m.Elif(self.bit_cnt == 17):
                            m.d.sync += self.sda_oe.eq(0) # Release SDA for Data ACK
                        with m.Elif(self.bit_cnt == 18):
                            m.d.sync += self.sda_oe.eq(1) # Prepare for STOP
                            m.next = "STOP"
                        with m.Else():
                            m.d.sync += [
                                self.sda_oe.eq(~self.shift_reg[15]),
                                self.shift_reg.eq(self.shift_reg << 1)
                            ]

            with m.State("STOP"):
                with m.If(self.div_cnt < self.divider - 1):
                    m.d.sync += self.div_cnt.eq(self.div_cnt + 1)
                with m.Else():
                    m.d.sync += self.div_cnt.eq(0)
                    with m.If(self.scl == 0):
                        m.d.sync += self.scl.eq(1)
                    with m.Else():
                        m.d.sync += self.sda_oe.eq(0) # STOP Condition
                        m.next = "IDLE"
        return m