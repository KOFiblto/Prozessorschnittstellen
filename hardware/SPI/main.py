# spi.py
from amaranth import *
from amaranth.sim import Simulator

from SPI_master import SPIMaster
from SPI_slave import SPISlave

class SPITestBench(Elaboratable):
    def __init__(self):
        self.master = SPIMaster(clk_div=4)
        self.slave = SPISlave()

    def elaborate(self, platform):
        m = Module()
        m.submodules.master = self.master
        m.submodules.slave = self.slave

        m.d.comb += [
            self.slave.sck.eq(self.master.sck),
            self.slave.mosi.eq(self.master.mosi),
            self.slave.cs.eq(self.master.cs),
            self.master.miso.eq(self.slave.miso)
        ]
        return m

if __name__ == "__main__":
    dut = SPITestBench()
    sim = Simulator(dut)
    sim.add_clock(1e-6)

    async def testcase(ctx):
        message = "SPI"
        for char in message:
            ctx.set(dut.slave.data_in, ord('+')) 
            
            while not ctx.get(dut.master.ready):
                await ctx.tick()
            
            ctx.set(dut.master.data_in, ord(char))
            ctx.set(dut.master.start, 1)
            await ctx.tick()
            ctx.set(dut.master.start, 0)
            
            while not ctx.get(dut.master.valid):
                await ctx.tick()
            
            master_rx = chr(ctx.get(dut.master.data_out))
            slave_rx = chr(ctx.get(dut.slave.data_out))
            
            print(f"Master sent: '{char}' -> Slave received: '{slave_rx}'")
            print(f"Slave sent:  '+'   -> Master received: '{master_rx}'\n")

    sim.add_testbench(testcase)
    with sim.write_vcd("SPI/SPI.vcd"):
        sim.run()