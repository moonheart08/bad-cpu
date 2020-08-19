from nmigen import *
from instr_decode import *
from alu import *
from fetcher import *

class CPU(Elaboratable):
    def __init__(self):
        

        self.registers = Memory(width=32, depth=16)
        self.pc = Signal(31)
        self.current_instr = Signal(32)

        self.ccount = Signal(64) # Cycle counter
        self.icount = Signal(64) # Instruction Counter
        self.rcount = Signal(64) # Read counter
        self.wcount = Signal(64) # Write counter
        self.fcount = Signal(64) # Instruction Fetch Counter
        self.pbcount = Signal(64) # Prefetch blocked Fetch counter
        self.fscount = Signal(64) # Fetch Stalled counter

        self.carry = Signal()
        self.overflow = Signal()
        self.zero = Signal()
        self.negative = Signal()

        self.decode = InstructionDecoder()
        self.alu = ALU()
        self.fetcher = Fetcher()

    def elaborate(self, platform):
        m = Module()
        m.submodules.regrd_1 = self.registers.read_port()
        regrd_1 = m.submodules.regrd_1
        m.submodules.regrd_2 = self.registers.read_port()
        regrd_2 = m.submodules.regrd_2
        m.submodules.regwr   = self.registers.write_port()
        regwr = m.submodules.regwr
        m.submodules.decode  = self.decode
        m.submodules.alu     = self.alu
        m.submodules.fetcher = self.fetcher
        m.d.sync += self.ccount.eq(self.ccount + 1)
        instr_lower = self.current_instr.word_select(0, 16)
        instr_upper = self.current_instr.word_select(1, 16)
        
        operand_fetch_addr = Signal(32)
        reg_a = Signal(32)
        reg_b = Signal(32)
        reg_a_addr = Signal(32)
        reg_a_data = Signal(32)
        reg_a_sel = Signal(4)
        post_increment = Signal(32)
        store_back_addr = Signal()
        decode_handle_store = Signal()

        with m.FSM() as fsm:
            with m.State("AAAAAA"):
                m.mode = "DECODE"
            with m.State("DECODE"):
                with m.If((self.fetcher.available == 0) | (decode_handle_store & self.fetcher.write_busy)):
                    m.mode = "DECODE" # wait for un-busy/available instrs. :(
                with m.Else():
                    with m.If(decode_handle_store):
                        m.d.sync += self.fetcher.data_bus_w.eq(reg_a_data)
                        m.d.sync += self.fetcher.addr_bus_w.eq(reg_a_addr)
                        m.d.comb += self.fetcher.write_req.eq(1)
                        with m.If(store_back_addr):
                            m.d.comb += regwr.en.eq(1)
                            m.d.sync += regwr.addr.eq(reg_a_sel)
                            m.d.sync += regwr.data.eq(reg_a_addr + (post_increment * 4))
                    m.d.sync += instr_lower.eq(self.fetcher.instr_bus_r)
                    m.d.sync += self.decode.instr_in_1.eq(instr_lower)
                    m.d.sync += regrd_1.addr.eq(self.decode.register_a)
                    m.d.sync += regrd_2.addr.eq(self.decode.register_b)
                    with m.If(self.decode.fetch_second):
                        m.mode = "DECODE_2"
                        m.d.comb += self.fetcher.advance.eq(1) # Holds for 1 cycle
                    with m.Elif(self.decode.operation_mode.matches("0011-")):
                        m.mode = "EXECUTE"
                    with m.Else():
                        m.mode = "FETCH"

            with m.State("DECODE_2"):
                m.d.sync += instr_upper.eq(self.fetcher.instr_bus_r)
                m.mode = "EXECUTE"
            with m.State("FETCH"):
                # oh no
                m.mode = "FETCH"
            with m.State("EXECUTE"):
                with m.If(self.decode.operation_mode.matches("0011-")):
                    m.d.sync += reg_a.eq(regrd_1.data)
                    m.d.sync += reg_b.eq(regrd_1.data)
                # otherwise it's already been stored for us
                reg_a_out = Signal(32)
                with m.Switch(self.decode.operation):
                    with m.Case("0----"):
                        m.d.comb += self.alu.op_select.eq(self.decode.operation[0:4])
                        m.d.comb += self.alu.in_bus_a.eq(reg_a)
                        m.d.comb += self.alu.in_bus_a.eq(reg_b)
                        m.d.comb += self.alu.carry_in.eq(self.carry)
                        m.d.comb += reg_a_out.eq(self.alu.out_bus)
                        m.d.sync += self.carry.eq(self.alu.carry_out)
                        m.d.sync += self.overflow.eq(self.alu.overflow)
                        m.d.sync += self.negative.eq(self.alu.negative)
                        m.d.sync += self.zero.eq(self.alu.zero)
                m.d.comb += regwr.en.eq(1)
                m.d.sync += regwr.addr.eq(self.decode.register_a)
                m.d.sync += regwr.data.eq(reg_a_out)
                m.mode = "DECODE"
                        
                

        return m