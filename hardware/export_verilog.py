# export_verilog.py
import sys
import os

# Add the workspace path to sys.path so we can import from subfolders
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("./I2C"))
sys.path.append(os.path.abspath("./SPI"))
sys.path.append(os.path.abspath("./UART"))

from amaranth.back import verilog
from SPI.SPI_master import SPIMaster
from SPI.SPI_slave import SPISlave
from I2C.I2C_master import I2CMaster
from I2C.I2C_slave import I2CSlave
from UART.main import UART

def export_module(module, ports, filename):
    print(f"Exporting {module.__class__.__name__} to {filename}...")
    try:
        verilog_code = verilog.convert(module, ports=ports)
        with open(filename, "w") as f:
            f.write(verilog_code)
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

if __name__ == "__main__":
    # Setup environment paths for OSS CAD Suite so Amaranth can find Yosys
    oss_root = r"C:\_dev\oss-cad-suite"
    oss_bin = os.path.join(oss_root, "bin")
    oss_lib = os.path.join(oss_root, "lib")
    os.environ["YOSYSHQ_ROOT"] = oss_root
    os.environ["PATH"] = f"{oss_bin};{oss_lib};" + os.environ.get("PATH", "")

    os.makedirs("verilog_export", exist_ok=True)

    # 1. SPI Master
    spi_master = SPIMaster()
    export_module(
        spi_master,
        ports=[
            spi_master.start, spi_master.data_in, spi_master.miso,
            spi_master.sck, spi_master.mosi, spi_master.cs,
            spi_master.data_out, spi_master.ready, spi_master.valid
        ],
        filename="verilog_export/SPIMaster.v"
    )

    # 2. SPI Slave
    spi_slave = SPISlave()
    export_module(
        spi_slave,
        ports=[
            spi_slave.sck, spi_slave.mosi, spi_slave.cs,
            spi_slave.data_in, spi_slave.miso, spi_slave.data_out,
            spi_slave.valid
        ],
        filename="verilog_export/SPISlave.v"
    )

    # 3. I2C Master
    i2c_master = I2CMaster()
    export_module(
        i2c_master,
        ports=[
            i2c_master.scl, i2c_master.sda_oe, i2c_master.start,
            i2c_master.addr, i2c_master.data, i2c_master.ready
        ],
        filename="verilog_export/I2CMaster.v"
    )

    # 4. I2C Slave
    i2c_slave = I2CSlave()
    export_module(
        i2c_slave,
        ports=[
            i2c_slave.scl, i2c_slave.sda_i, i2c_slave.sda_oe,
            i2c_slave.data_out, i2c_slave.valid
        ],
        filename="verilog_export/I2CSlave.v"
    )

    # 5. UART
    uart = UART(clks_per_bit=4)
    export_module(
        uart,
        ports=[
            uart.tx_start, uart.tx_data, uart.tx, uart.tx_ready,
            uart.rx, uart.rx_data, uart.rx_valid
        ],
        filename="verilog_export/UART.v"
    )
