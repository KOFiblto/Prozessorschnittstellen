# main.py
from amaranth import *
from amaranth.sim import Simulator

class UART(Elaboratable):
    def __init__(self, clks_per_bit):
        self.clks_per_bit = clks_per_bit
        self.tx_start = Signal()
        self.tx_data = Signal(8)
        self.tx = Signal(reset=1)
        self.tx_ready = Signal(reset=1)
        self.rx = Signal(reset=1)
        self.rx_data = Signal(8)
        self.rx_valid = Signal()

    def elaborate(self, platform):
        m = Module()

        tx_clk_count = Signal(range(self.clks_per_bit))
        tx_bit_count = Signal(range(8))
        tx_reg = Signal(8)

        with m.FSM(name="tx_state"):
            with m.State("IDLE"):
                m.d.sync += [
                    self.tx.eq(1),
                    self.tx_ready.eq(1),
                    tx_clk_count.eq(0),
                    tx_bit_count.eq(0)
                ]
                with m.If(self.tx_start):
                    m.d.sync += [
                        self.tx_ready.eq(0),
                        tx_reg.eq(self.tx_data)
                    ]
                    m.next = "START"
            
            with m.State("START"):
                m.d.sync += self.tx.eq(0)
                with m.If(tx_clk_count < self.clks_per_bit - 1):
                    m.d.sync += tx_clk_count.eq(tx_clk_count + 1)
                with m.Else():
                    m.d.sync += tx_clk_count.eq(0)
                    m.next = "DATA"

            with m.State("DATA"):
                m.d.sync += self.tx.eq(tx_reg[0])
                with m.If(tx_clk_count < self.clks_per_bit - 1):
                    m.d.sync += tx_clk_count.eq(tx_clk_count + 1)
                with m.Else():
                    m.d.sync += tx_clk_count.eq(0)
                    m.d.sync += tx_reg.eq(tx_reg >> 1)
                    with m.If(tx_bit_count < 7):
                        m.d.sync += tx_bit_count.eq(tx_bit_count + 1)
                    with m.Else():
                        m.d.sync += tx_bit_count.eq(0)
                        m.next = "STOP"

            with m.State("STOP"):
                m.d.sync += self.tx.eq(1)
                with m.If(tx_clk_count < self.clks_per_bit - 1):
                    m.d.sync += tx_clk_count.eq(tx_clk_count + 1)
                with m.Else():
                    m.d.sync += tx_clk_count.eq(0)
                    m.d.sync += self.tx_ready.eq(1)
                    m.next = "IDLE"

        rx_clk_count = Signal(range(self.clks_per_bit))
        rx_bit_count = Signal(range(8))
        rx_reg = Signal(8)

        with m.FSM(name="rx_state"):
            with m.State("IDLE"):
                m.d.sync += [
                    self.rx_valid.eq(0),
                    rx_clk_count.eq(0),
                    rx_bit_count.eq(0)
                ]
                with m.If(self.rx == 0):
                    m.next = "START"

            with m.State("START"):
                with m.If(rx_clk_count == (self.clks_per_bit // 2) - 1):
                    with m.If(self.rx == 0):
                        m.d.sync += rx_clk_count.eq(0)
                        m.next = "DATA"
                    with m.Else():
                        m.next = "IDLE"
                with m.Else():
                    m.d.sync += rx_clk_count.eq(rx_clk_count + 1)

            with m.State("DATA"):
                with m.If(rx_clk_count < self.clks_per_bit - 1):
                    m.d.sync += rx_clk_count.eq(rx_clk_count + 1)
                with m.Else():
                    m.d.sync += rx_clk_count.eq(0)
                    m.d.sync += rx_reg.eq(Cat(rx_reg[1:8], self.rx))
                    with m.If(rx_bit_count < 7):
                        m.d.sync += rx_bit_count.eq(rx_bit_count + 1)
                    with m.Else():
                        m.d.sync += rx_bit_count.eq(0)
                        m.next = "STOP"

            with m.State("STOP"):
                with m.If(rx_clk_count < self.clks_per_bit - 1):
                    m.d.sync += rx_clk_count.eq(rx_clk_count + 1)
                with m.Else():
                    m.d.sync += [
                        self.rx_valid.eq(1),
                        self.rx_data.eq(rx_reg),
                        rx_clk_count.eq(0)
                    ]
                    m.next = "IDLE"

        return m


class UARTTestBench(Elaboratable):
    def __init__(self):
        self.uart = UART(clks_per_bit=4)
        
    def elaborate(self, platform):
        m = Module()
        m.submodules.uart = self.uart
        m.d.comb += self.uart.rx.eq(self.uart.tx) # Loopback
        return m

if __name__ == "__main__":
    dut = UARTTestBench()
    sim = Simulator(dut)
    sim.add_clock(1e-6)

    async def testcase(ctx):
        message = "Hello World"
        for char in message:
            while not ctx.get(dut.uart.tx_ready):
                if ctx.get(dut.uart.rx_valid):
                    print(chr(ctx.get(dut.uart.rx_data)), end="", flush=True)
                await ctx.tick()
            
            ctx.set(dut.uart.tx_data, ord(char))
            ctx.set(dut.uart.tx_start, 1)
            
            if ctx.get(dut.uart.rx_valid):
                print(chr(ctx.get(dut.uart.rx_data)), end="", flush=True)
            await ctx.tick()
            
            ctx.set(dut.uart.tx_start, 0)
            if ctx.get(dut.uart.rx_valid):
                print(chr(ctx.get(dut.uart.rx_data)), end="", flush=True)
            await ctx.tick()

        for _ in range(100):
            if ctx.get(dut.uart.rx_valid):
                print(chr(ctx.get(dut.uart.rx_data)), end="", flush=True)
            await ctx.tick()
        print()

    sim.add_testbench(testcase)
    with sim.write_vcd("UART/UART.vcd"):
        sim.run()