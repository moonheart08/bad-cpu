from nmigen import *

class InstructionDecoder(Elaboratable):
    def __init__(self):
        self.instr_in_1       = Signal(16)
        
        self.operation        = Signal(6)
        self.register_a       = Signal(3)
        self.register_b       = Signal(3)
        self.operation_mode   = Signal(5)

        self.fetch_second     = Signal(reset = 0)
        
    
    def elaborate(self, platform):
        # IFORM 1:
        #  FEDCBA9876543210
        #  mmmmmbbbaaaooooo
        # o: Operand
        # a: Operand A
        # b: Operand B
        # m: Operand mode
        m = Module()
        
        mode_field = self.instr_in_1.bit_select(11, 5)

        m.d.comb += self.fetch_second.eq(mode_field.bit_select(3, 1) & (self.operation_mode.matches("010--")))
        m.d.comb += self.operation_mode.eq(mode_field)
        m.d.comb += self.operation.eq(self.instr_in_1.bit_select(0, 6))
        m.d.comb += self.register_a.eq(self.instr_in_1.bit_select(5, 3))
        m.d.comb += self.register_b.eq(self.instr_in_1.bit_select(8, 3))

        return m