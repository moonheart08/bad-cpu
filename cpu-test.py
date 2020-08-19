from cpu import *
from nmigen import *
from nmigen.back.pysim import Simulator

testee = CPU()

def bench():
    yield testee.registers._array[0].eq(2)
    yield testee.fetcher.ext_data_bus.eq(0x30003000)
    yield testee.fetcher.ext_read_ack.eq(1)
    yield
    yield
    yield
    yield
    yield
    yield
    yield
    yield
    yield
    yield

sim = Simulator(testee)
sim.add_clock(1e-6)
sim.add_sync_process(bench)
with sim.write_vcd("cpu.vcd", gtkw_file="cpu.gtkw", traces=[testee.fetcher.available, testee.fetcher.ext_addr_bus, testee.fetcher.ext_data_bus, testee.fetcher.instr_bus_r]):
    sim.run()
