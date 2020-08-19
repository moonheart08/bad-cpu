from fetcher import *
from nmigen import *
from nmigen.back.pysim import Simulator

testee = Fetcher()
def check_bus():
    if ((yield testee.ext_read_en) == 1):
        yield testee.ext_read_ack.eq(1)
    else:
        yield testee.ext_read_ack.eq(0)
def bench():
    yield testee.ext_data_bus.eq(0x30006000)
    for i in range(0, 16):
        yield from check_bus()
        yield
    yield testee.advance.eq(1)
    for i in range(0, 8):
        yield from check_bus()
        yield
    yield testee.advance.eq(0)
    for i in range(0, 4):
        yield from check_bus()
        yield

sim = Simulator(testee)
sim.add_clock(1e-6)
sim.add_sync_process(bench)
with sim.write_vcd("fetcher.vcd", gtkw_file="fetcher.gtkw", traces=[testee.ext_data_bus, testee.ext_addr_bus, testee.advance, testee.available, testee.instr_bus_r]):
    sim.run()
