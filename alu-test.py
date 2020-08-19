from alu import *
from nmigen import *
from nmigen.back.pysim import Simulator

class ALUTestBench(Elaboratable):
    def __init__(self):
        self.carry_in  = Signal()
        self.carry_out = Signal()
        self.overflow  = Signal()
        self.negative  = Signal()
        self.zero      = Signal()

        self.in_bus_a  = Signal(32)
        self.in_bus_b  = Signal(32)
        self.op_select = Signal(4)
        self.out_bus   = Signal(32)
        self.dummy     = Signal()

        self.alu = ALU()

    def elaborate(self, platform):
        m = Module()
        m.submodules.alu = self.alu
        m.d.comb += self.alu.in_bus_a.eq(self.in_bus_a)
        m.d.comb += self.alu.in_bus_b.eq(self.in_bus_b)
        m.d.comb += self.alu.carry_in.eq(self.carry_in)
        m.d.comb += self.alu.op_select.eq(self.op_select)
        m.d.comb += self.out_bus.eq(self.alu.out_bus)
        m.d.comb += self.carry_out.eq(self.alu.carry_out)
        
        m.d.sync += self.dummy.eq(self.dummy) # NOP. Probably a terrible idea, but makes sync exist.
        return m

testee = ALUTestBench()

def bench():
    yield testee.in_bus_a.eq(3)
    yield testee.in_bus_b.eq(2)
    yield testee.op_select.eq(0b0000)
    yield testee.carry_in.eq(0)
    yield
    assert ((yield testee.out_bus) == 5)
    yield testee.carry_in.eq(1)
    yield testee.op_select.eq(0b0001)
    yield
    assert ((yield testee.out_bus) == 6)
    yield testee.op_select.eq(0b0010)
    yield testee.carry_in.eq(0)
    yield
    assert ((yield testee.out_bus) == 1)
    yield testee.op_select.eq(0b0011)
    yield testee.carry_in.eq(1)
    yield
    assert ((yield testee.out_bus) == 0)
    yield testee.in_bus_a.eq(0x80000000)
    yield testee.in_bus_b.eq(0x80000000)
    yield testee.op_select.eq(0b0000)
    yield testee.carry_in.eq(0)
    yield
    assert ((yield testee.out_bus) == 0)
    assert ((yield testee.carry_out) == 1)
    yield testee.op_select.eq(0b0001)
    yield testee.carry_in.eq(1)
    yield
    assert ((yield testee.carry_out) == 1)
    assert ((yield testee.out_bus) == 1)
sim = Simulator(testee)
sim.add_clock(1e-6)
sim.add_sync_process(bench)
with sim.write_vcd("counter.vcd"):
    sim.run()
