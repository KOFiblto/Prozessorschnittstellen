# main.py
from amaranth import *
from amaranth.sim import Simulator
from I2C_master import I2CMaster
from I2C_slave import I2CSlave

class I2CTop(Elaboratable):
    def __init__(self):
        # Using 10 MHz system clock for sufficient timing resolution
        self.master = I2CMaster(clk_freq=10000000)
        self.slave = I2CSlave(address=0x50)

    def elaborate(self, platform):
        m = Module()
        m.submodules.master = self.master
        m.submodules.slave = self.slave

        # Internal signals for the I2C Bus
        scl_bus = Signal(reset=1)
        sda_bus = Signal(reset=1)

        # Open-drain logic for SCL (Master driven, Slave reads)
        m.d.comb += scl_bus.eq(self.master.scl)
        m.d.comb += self.slave.scl.eq(scl_bus)
        
        # Open-drain logic for SDA (both Master and Slave can drive)
        # SCL/SDA pull-up logic: if neither drives, it remains high (1).
        m.d.comb += sda_bus.eq(~(
            (self.master.sda_oe) | 
            (self.slave.sda_oe)
        ))

        # SDA input visible to Slave
        m.d.comb += self.slave.sda_i.eq(sda_bus)

        return m

if __name__ == "__main__":
    dut = I2CTop()
    sim = Simulator(dut)
    sim.add_clock(1e-7) # 10 MHz clock

    async def bench(ctx):
        print("Starting I2C Simulation...")
        ctx.set(dut.master.addr, 0x50)
        ctx.set(dut.master.data, 0xAA)
        ctx.set(dut.master.start, 1)
        await ctx.tick()
        ctx.set(dut.master.start, 0)
        
        success = False
        # Run simulation and monitor for validation
        for i in range(2500):
            await ctx.tick()
            
            slv_valid = ctx.get(dut.slave.valid)
            slv_data = ctx.get(dut.slave.data_out)
            
            if slv_valid:
                print(f"Cycle {i}: Slave received VALID data: 0x{slv_data:02X}")
                if slv_data == 0xAA:
                    success = True
                    print("SUCCESS: Data matches 0xAA!")
                else:
                    print(f"FAILURE: Data is 0x{slv_data:02X} but expected 0xAA.")
                break
                
        if not success:
            print("FAILURE: No valid I2C transmission completed.")

    sim.add_testbench(bench)
    with sim.write_vcd("I2C/i2c_main.vcd"):
        sim.run()