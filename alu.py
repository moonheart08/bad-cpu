from nmigen import *

class Adder(Elaboratable):
    def __init__(self):
        self.in_bus_a   = Signal(32)
        self.in_bus_b   = Signal(32)
        self.out_bus    = Signal(32)
        self.carry_in   = Signal()
        self.carry_out  = Signal()


    def elaborate(self, platform):
        m = Module()
        m.d.comb += Cat(self.out_bus, self.carry_out).eq(self.in_bus_a + self.in_bus_b + self.carry_in)
        return m


class Subtractor(Elaboratable):
    def __init__(self):
        self.in_bus_a   = Signal(32)
        self.in_bus_b   = Signal(32)
        self.out_bus    = Signal(32)
        self.carry_in   = Signal()
        self.carry_out  = Signal()


    def elaborate(self, platform):
        m = Module()
        m.d.comb += Cat(self.out_bus, self.carry_out).eq(self.in_bus_a - (self.in_bus_b + self.carry_in))
        return m

class LeftShifter(Elaboratable):
    def __init__(self):
        self.in_bus_a   = Signal(32)
        self.in_bus_b   = Signal(32)
        self.out_bus    = Signal(32)
        self.carry_in   = Signal()
        self.carry_out  = Signal()


    def elaborate(self, platform):
        m = Module()
        m.d.comb += Cat(self.out_bus, self.carry_out).eq(Cat(self.in_bus_a, self.carry_in) << self.in_bus_b)
        return m

class RightShifter(Elaboratable):
    def __init__(self):
        self.in_bus_a   = Signal(32)
        self.in_bus_b   = Signal(32)
        self.out_bus    = Signal(32)
        self.carry_in   = Signal()
        self.carry_out  = Signal()


    def elaborate(self, platform):
        m = Module()
        m.d.comb += self.out_bus.eq(Cat(self.carry_in, self.in_bus_a) >> self.in_bus_b)
        return m

class ALU(Elaboratable):
    """
    it counts.
    """
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

        self.add = Adder()
        self.sub = Subtractor()
        self.lsh = LeftShifter()
        self.rsh = RightShifter()
    
    def elaborate(self, platform):
        m = Module()

        m.submodules.add = self.add
        m.submodules.sub = self.sub
        m.submodules.lsh = self.lsh
        m.submodules.rsh = self.rsh

        m.d.comb += [
            self.add.in_bus_a.eq(self.in_bus_a),
            self.add.in_bus_b.eq(self.in_bus_b),
            self.sub.in_bus_a.eq(self.in_bus_a),
            self.sub.in_bus_b.eq(self.in_bus_b),
            self.lsh.in_bus_a.eq(self.in_bus_a),
            self.lsh.in_bus_b.eq(self.in_bus_b),
            self.rsh.in_bus_a.eq(self.in_bus_a),
            self.rsh.in_bus_b.eq(self.in_bus_b),
        ]
        carry = Signal()
        m.d.comb += carry.eq(self.carry_in & self.op_select[0])
        m.d.comb += self.add.carry_in.eq(carry)
        m.d.comb += self.sub.carry_in.eq(carry)
        m.d.comb += self.lsh.carry_in.eq(carry)
        m.d.comb += self.rsh.carry_in.eq(carry)
        m.d.comb += self.carry_out.eq(0)
        with m.Switch(self.op_select):
            with m.Case("000-", "110-"): # ADD/ADC
                m.d.comb += self.out_bus.eq(self.add.out_bus)
                m.d.comb += self.carry_out.eq(self.add.carry_out)
            with m.Case("001-"): # SUB/SBB
                m.d.comb += self.out_bus.eq(self.sub.out_bus)
                m.d.comb += self.carry_out.eq(self.sub.carry_out)
            with m.Case(0b0100, 0b1110): # AND
                m.d.comb += self.out_bus.eq(self.in_bus_a & self.in_bus_b)
            with m.Case(0b0101): # OR
                m.d.comb += self.out_bus.eq(self.in_bus_a | self.in_bus_b)
            with m.Case(0b0110): # XOR
                m.d.comb += self.out_bus.eq(self.in_bus_a ^ self.in_bus_b)
            with m.Case(0b0111): # AND NOT
                m.d.comb += self.out_bus.eq(self.in_bus_a & ~self.in_bus_b)
            with m.Case("100-"): # LSH/LSHC
                m.d.comb += self.out_bus.eq(self.lsh.out_bus)
                m.d.comb += self.carry_out.eq(self.lsh.carry_out)
            with m.Case("101-"): # RSH/RSHC
                m.d.comb += self.out_bus.eq(self.rsh.out_bus)
                m.d.comb += self.carry_out.eq(self.rsh.carry_out)
            with m.Case(0b1111):
                m.d.comb += self.out_bus.eq(self.in_bus_b) # MOV reg, reg

        m.d.comb += self.zero.eq(self.out_bus == 0)
        m.d.comb += self.negative.eq(self.out_bus >= 0x80000000)

        return m
    