from nmigen import *

class EffectiveAddressGenerator(Elaboratable):
    def __init__(self):
        self.in_reg_val  = Signal(32)
        self.in_creg_val = Signal(32) 
        self.in_mode     = Signal(5)
        self.in_second   = Signal(16) # Mode data word

        self.out_addr    = Signal(32, reset = 0)
        self.store_pre   = Signal(reset = 0)
        self.store_post  = Signal(reset = 0)
        self.reserved_op = Signal(reset = 0)
    
    def elaborate(self, platform):
        m = Module()
        mode = self.in_mode.bit_select(1, 3)

        with m.Switch(mode):
            with m.Case(0b000):
                m.d.comb += self.out_addr.eq(self.in_reg_val)
            with m.Case(0b001):
                m.d.comb += self.out_addr.eq(self.in_reg_val + 4)
                m.d.comb += self.store_post.eq(1)
            with m.Case(0b010):
                m.d.comb += self.out_addr.eq(self.in_reg_val - 4)
                m.d.comb += self.store_pre.eq(1)
            with m.Case(0b011):
                # Reserved. We should never get here
            with m.Case(0b100):
                sext = Signal(signed(16))
                m.d.comb += sext.eq(self.in_second)
                m.d.comb += self.out_addr.eq(self.in_reg_val + sext)
            with m.Case(0b101):
                #TODO: finish
                m.d.comb += self.out_addr.eq(self.in_reg_val + (self.in_creg_val))
            with m.Default():
                m.d.comb += self.reserved_op.eq(0) 