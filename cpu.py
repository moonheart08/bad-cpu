from nmigen import *
from instr_decode import *
from alu import *

class CPU(Elaboratable):
    def __init__(self):
        self.data_bus_r = Signal(32)
        self.data_bus_w = Signal(32)
        self.addr_bus_r = Signal(30) # all accesses are 16-bit
        self.addr_bus_w = Signal(30) 
        self.read_en  = Signal()
        self.read_ack = Signal()
        self.write_en = Signal()
        self.write_ack = Signal()

        self.registers = Memory(width=32, depth=16)
        self.pc = Signal(31)
        self.current_instr = Signal(16)
        self.fetch_done = Signal()
        self.can_fetch = Signal()

        self.ccount = Signal(64) # Cycle counter
        self.icount = Signal(64) # Instruction Counter
        self.rcount = Signal(64) # Read counter
        self.wcount = Signal(64) # Write counter
        self.fcount = Signal(64) # Instruction Fetch Counter
        self.pbcount = Signal(64) # Prefetch blocked Fetch counter
        self.fscount = Signal(64) # Fetch Stalled counter

        self.decode = InstructionDecoder()
        self.alu = ALU()

    def elaborate(self, platform):
        m = Module()
        m.submodules.regrd_1 = self.registers.read_port()
        m.submodules.regrd_2 = self.registers.read_port()
        m.submodules.regwr   = self.registers.write_port()
        m.submodules.decode  = self.decode
        m.submodules.alu     = self.alu
        m.d.sync += self.ccount.eq(self.ccount + 1)

        
        fetched = Signal(32)
        
        i_lower = Signal(16)
        i_upper = Signal(16)
        
        bus_busy = Signal()
        fetch_specific = Signal(30)
        fetch_specific_ctrl = Signal()
        reg_a = Signal(32)
        reg_a_out_addr = Signal(32)
        reg_a_is_outp  = Signal()
        reg_b = Signal(32)
        reg_c = Signal(32)

        m.d.comb += self.decode.instr_in_1.eq(i_lower)

        with m.If(bus_busy):
            with m.If(self.read_ack):
                m.d.sync += [
                    fetched.eq(self.data_bus_r),
                    bus_busy.eq(0),
                    fetch_specific_ctrl.eq(0),
                    self.fetch_done.eq(1),
                    self.read_en.eq(0)
                ]
                

        with m.FSM() as fsm:
            with m.State("START"):
                m.next = "FETCH_INSTR"
                m.d.comb += self.can_fetch.eq(1)
            with m.State("FETCH_INSTR"):
                with m.If(self.fetch_done):
                    m.d.sync += self.fetch_done.eq(0)
                    m.d.sync += self.fcount.eq(self.fcount + 1)
                    m.d.sync += i_lower.eq(fetched.word_select(self.pc[0], 16))
                    i_lower_cur = fetched.word_select(self.pc[0], 16)
                    m.d.comb += self.decode.instr_in_1.eq(i_lower_cur)
                    imode = self.decode.operation_mode
                    m.d.comb += self.can_fetch.eq(1) # Fetch next instr/second instr word
                    with m.If(imode.matches("-1---")):
                        with m.If(self.pc[0] == 1):
                            m.d.sync += fetch_specific.eq(self.pc[1:32] + 1)
                            m.d.sync += fetch_specific_ctrl.eq(1)
                            m.next = "WAIT_ON_INSTR_HALF"
                        with m.Else():
                            a_sel = Mux(imode.matches("1---0"), self.decode.register_a, Cat(self.decode.register_a, 1))
                            m.d.sync += m.submodules.regrd_1.addr.eq(a_sel)
                            b_sel = Mux(imode.matches("1---0"), self.decode.register_b, Cat(self.decode.register_b, 1))
                            m.d.sync += m.submodules.regrd_2.addr.eq(b_sel)
                            m.next = "DECODE"
                    with m.Else():
                        a_sel = Mux(imode.matches("1---0"), self.decode.register_a, Cat(self.decode.register_a, 1))
                        m.d.sync += m.submodules.regrd_1.addr.eq(a_sel)
                        b_sel = Mux(imode.matches("1---0"), self.decode.register_b, Cat(self.decode.register_b, 1))
                        m.d.sync += m.submodules.regrd_2.addr.eq(b_sel)
                        m.next = "EXECUTE"
            with m.State("WAIT_ON_INSTR_HALF"):
                m.d.sync += self.fscount.eq(self.fscount + 1)
                with m.If(self.fetch_done):
                    m.d.sync += i_upper.eq(fetched.word_select(0, 16))
                    m.next = "DECODE"
            with m.State("DECODE"):
                m.next = "HALT"
            with m.State("EXECUTE"):
                with m.If(self.decode.operation_mode.matches("0011-")):
                    m.d.sync += reg_a.eq(m.submodules.regrd_1.data) 
                    m.d.sync += reg_b.eq(m.submodules.regrd_2.data)
                    m.d.sync += reg_a_out_addr.eq(self.decode.register_a)
                write_val = Signal(32)
                with m.Switch(self.decode.operation):
                    with m.Case("00----"):
                        m.d.comb += self.alu.in_bus_a.eq(reg_a)
                        m.d.comb += self.alu.in_bus_b.eq(reg_b)
                        m.d.comb += self.alu.op_select.eq(self.decode.operation[0:4])
                        m.d.comb += write_val.eq(self.alu.out_bus)
                
                m.d.sync += m.submodules.regwr.addr.eq(reg_a_out_addr)
                m.d.sync += m.submodules.regwr.data.eq(write_val)
                m.d.sync += self.pc.eq(self.pc + 1 + self.decode.fetch_second)
                m.next = "FETCH_INSTR"
            with m.State("HALT"):
                m.next = "HALT"
        
        with m.If(self.can_fetch):
            next = Signal(30)
            with m.If(fetch_specific_ctrl):
                m.d.comb += next.eq(fetch_specific)
            with m.Else():
                m.d.comb += next.eq(self.pc[1:32])
            m.d.sync += self.addr_bus_r.eq(next)
            m.d.sync += self.read_en.eq(1)
            m.d.sync += bus_busy.eq(1)
        return m