from nmigen import *

class Fetcher(Elaboratable):
    def __init__(self):
        # READS
        self.available = Signal(4) # Number of instruction words available to pull.
        self.cannot_fetch_further = Signal() # Indicates further buffering isn't possible due to a memory boundary
        self.instr_bus_r = Signal(16)
        self.data_bus_r = Signal(32)
        self.addr_bus_r = Signal(30)
        self.read_req = Signal()
        self.new_pc_value = Signal(30)
        self.set_pc_value = Signal()
        
        # WRITES
        self.advance = Signal() # Advance instruction bus ahead 1 word
        self.data_bus_w = Signal(32)
        self.addr_bus_w = Signal(30)
        self.write_req = Signal()
        self.write_busy = Signal()

        # EXTERNAL
        self.ext_data_bus = Signal(32)
        self.ext_addr_bus = Signal(30)
        self.ext_read_ack = Signal()
        self.ext_comb_read_ack = Signal()
        self.ext_read_en  = Signal()
        self.ext_write_en = Signal()
        self.ext_comb_write_ack = Signal()

        self.instr_buffer = Memory(width=32, depth=4)
        self.buffer_pos = Signal(2)
        self.reader_pos = Signal(3)

    def elaborate(self, platform):
        m = Module()
        m.submodules.read_port = self.instr_buffer.read_port()
        m.submodules.write_port = self.instr_buffer.write_port()
        internal_pc = Signal(30)
        m.d.comb += m.submodules.read_port.addr.eq(self.reader_pos[1:3])
        m.d.comb += self.instr_bus_r.eq(m.submodules.read_port.data.word_select(self.reader_pos[0], 16))
        with m.If(self.advance & (self.available > 0)):
            m.d.sync += self.available.eq(self.available - 1)
            m.d.sync += self.reader_pos.eq(self.reader_pos + 1)
        with m.FSM() as fsm:
            with m.State("IFETCH"):
                
                with m.If(self.available >= 7):
                    m.d.sync += self.ext_read_en.eq(0)
                with m.If(self.write_req):
                    m.d.sync += self.ext_read_en.eq(0)
                    m.mode = "WRITE"
                with m.Elif(self.read_req):
                    m.d.sync += self.ext_read_en.eq(0)
                    m.mode = "READ"
                with m.Elif(self.ext_read_ack & self.ext_read_en & (self.available < 7)):
                    m.d.comb += m.submodules.write_port.en.eq(1)
                    m.d.comb += m.submodules.write_port.addr.eq(self.buffer_pos)
                    m.d.comb += m.submodules.write_port.data.eq(self.ext_data_bus)
                    m.d.sync += self.buffer_pos.eq(self.buffer_pos + 1)
                    m.d.sync += self.available.eq(self.available + 2)
                    m.d.sync += self.ext_read_en.eq(0)
                    m.d.sync += internal_pc.eq(internal_pc + 1)
                with m.Elif((self.available < 7) & ~(self.ext_read_en)):
                    m.d.sync += self.ext_read_en.eq(1)
                    m.d.sync += self.ext_addr_bus.eq(internal_pc)
            with m.State("WRITE"):
                m.d.comb += self.write_busy.eq(1)
                with m.If(self.ext_write_en):
                    with m.If(self.ext_read_ack):
                        m.mode = "IFETCH"
                        m.d.sync += self.ext_write_en.eq(0)
                with m.Else():
                    m.d.sync += self.ext_write_en.eq(1)
                    m.d.sync += self.ext_data_bus.eq(self.data_bus_w)
                    m.d.sync += self.ext_addr_bus.eq(self.addr_bus_w)
            with m.State("READ"):
                with m.If(self.ext_write_en):
                    with m.If(self.ext_read_ack):
                        m.mode = "IFETCH"
                        m.d.sync += self.ext_read_en.eq(0)
                        m.d.sync += self.read_req.eq(0)
                        m.d.sync += self.data_bus_r.eq(self.ext_data_bus)
                with m.Else():
                    m.d.sync += self.ext_write_en.eq(1)
                    m.d.sync += self.ext_addr_bus.eq(self.addr_bus_r)
        return m