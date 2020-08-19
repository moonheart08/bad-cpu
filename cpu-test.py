from cpu import *
from nmigen import *
from nmigen.back.pysim import Simulator

testee = CPU()

def test_for_req():
    if ((yield testee.read_en) == 1):
        yield testee.read_ack.eq(1)
    else:
        yield testee.read_ack.eq(0)
    yield

def bench():
    yield
    assert ((yield testee.read_en) == 1)
    yield testee.data_bus_r.eq(0b00110_000_000_00000)
    for i in range(0, 16):
        yield from test_for_req()

sim = Simulator(testee)
sim.add_clock(1e-6)
sim.add_sync_process(bench)
with sim.write_vcd("cpu.vcd", gtkw_file="cpu.gtkw", traces=[testee.pc, testee.data_bus_r, testee.data_bus_w, testee.read_en, testee.read_ack, testee.write_en, testee.write_ack, testee.current_instr, testee.can_fetch, testee.fetch_done]):
    sim.run()
