import struct


class ARMInstruction:
    def __init__(self, binary_word):
        self.binary_word = binary_word
        self.instruction_type = None
        self.opcode = None
        self.operands = {}
        self.condition_code = None
        self.set_flags = False

    def decode(self):
        self.condition_code = (self.binary_word >> 28) & 0xF

        # Check for Multiply (MUL/MLA) instruction
        if ((self.binary_word >> 24) & 0xFF) >> 1 == 0b0000000 and ((self.binary_word >> 4) & 0xF) == 0b1001:
            a_bit = (self.binary_word >> 21) & 0x1
            if a_bit == 0:
                self.instruction_type = 'MUL'
            else:
                self.instruction_type = 'MLA'
            self.set_flags = bool((self.binary_word >> 20) & 0x1)
            self.rd = (self.binary_word >> 16) & 0xF
            self.rm = self.binary_word & 0xF
            self.rs = (self.binary_word >> 8) & 0xF
            if a_bit:
                self.rn = (self.binary_word >> 12) & 0xF
                self.operands = {'rd': self.rd, 'rm': self.rm,
                                 'rs': self.rs, 'rn': self.rn}
            else:
                self.operands = {'rd': self.rd, 'rm': self.rm, 'rs': self.rs}
            return

        # Check for Data Processing Instructions
        if ((self.binary_word >> 26) & 0b11) == 0b00:
            self.set_flags = bool((self.binary_word >> 20) & 0x1)
            self.opcode = (self.binary_word >> 21) & 0xF
            self.rn = (self.binary_word >> 16) & 0xF
            self.rd = (self.binary_word >> 12) & 0xF

            # Immediate operand
            if (self.binary_word >> 25) & 0x1:
                rotate_imm = (self.binary_word >> 8) & 0xF
                imm8 = self.binary_word & 0xFF
                # Perform ROR on imm8 by 2 * rotate_imm
                self.operand2 = (imm8 >> (2 * rotate_imm)) | (imm8 <<
                                                              (32 - 2 * rotate_imm)) & 0xFFFFFFFF
                self.operands = {'rd': self.rd,
                                 'rn': self.rn, 'operand2': self.operand2}

                # Map opcodes to instruction types
                if self.opcode == 0b0100:  # ADD
                    self.instruction_type = 'ADD'
                elif self.opcode == 0b0010:  # SUB
                    self.instruction_type = 'SUB'
                elif self.opcode == 0b1101:  # MOV
                    self.instruction_type = 'MOV'
                elif self.opcode == 0b1010:  # CMP
                    self.instruction_type = 'CMP'
                    self.set_flags = True
                elif self.opcode == 0b0000:  # AND
                    self.instruction_type = 'AND'
                elif self.opcode == 0b1100:  # ORR
                    self.instruction_type = 'ORR'
                elif self.opcode == 0b0001:  # EOR
                    self.instruction_type = 'EOR'
                else:
                    self.instruction_type = 'UNKNOWN_DATA_PROCESSING_IMM'

            # Register operand
            else:
                self.rm = self.binary_word & 0xF
                shift_type_bits = (self.binary_word >> 5) & 0b11

                # Immediate shift amount
                if not ((self.binary_word >> 4) & 0x1):
                    shift_amount = (self.binary_word >> 7) & 0b11111
                    # Standalone shift instructions (Rn=0, opcode=MOV)
                    if self.rn == 0 and self.opcode == 0b1101:
                        if shift_type_bits == 0b00:  # LSL
                            self.instruction_type = 'LSL'
                        elif shift_type_bits == 0b01:  # LSR
                            self.instruction_type = 'LSR'
                        elif shift_type_bits == 0b10:  # ASR
                            self.instruction_type = 'ASR'
                        elif shift_type_bits == 0b11:  # ROR
                            self.instruction_type = 'ROR'
                        self.operands = {
                            'rd': self.rd, 'rm': self.rm, 'shift_amount': shift_amount}
                        return
                    # Regular data processing with immediate shift
                    self.operands = {'rd': self.rd, 'rn': self.rn, 'rm': self.rm,
                                     'shift_amount': shift_amount, 'shift_type': shift_type_bits}

                # Register shift amount
                else:
                    rs = (self.binary_word >> 8) & 0xF
                    # Standalone shift instructions
                    if self.rn == 0 and self.opcode == 0b1101:
                        if shift_type_bits == 0b00:  # LSL
                            self.instruction_type = 'LSL'
                        elif shift_type_bits == 0b01:  # LSR
                            self.instruction_type = 'LSR'
                        elif shift_type_bits == 0b10:  # ASR
                            self.instruction_type = 'ASR'
                        elif shift_type_bits == 0b11:  # ROR
                            self.instruction_type = 'ROR'
                        self.operands = {'rd': self.rd,
                                         'rm': self.rm, 'rs': rs}
                        return
                    # Regular data processing with register shift
                    self.operands = {'rd': self.rd,
                                     'rn': self.rn, 'rm': self.rm, 'rs': rs}

                # Map opcodes for register operands
                if self.opcode == 0b0100:  # ADD
                    self.instruction_type = 'ADD'
                elif self.opcode == 0b0010:  # SUB
                    self.instruction_type = 'SUB'
                elif self.opcode == 0b1101:  # MOV
                    self.instruction_type = 'MOV'
                elif self.opcode == 0b1010:  # CMP
                    self.instruction_type = 'CMP'
                    self.set_flags = True
                elif self.opcode == 0b0000:  # AND
                    self.instruction_type = 'AND'
                elif self.opcode == 0b1100:  # ORR
                    self.instruction_type = 'ORR'
                elif self.opcode == 0b0001:  # EOR
                    self.instruction_type = 'EOR'
                else:
                    self.instruction_type = 'UNKNOWN_DATA_PROCESSING_REG'
            return

        # Load/Store Instructions
        if ((self.binary_word >> 26) & 0b11) == 0b01:
            self.l_bit = (self.binary_word >> 20) & 0x1  # 1 for LDR, 0 for STR
            # 0=immediate, 1=register
            i_bit = (self.binary_word >> 25) & 0x1
            self.rn = (self.binary_word >> 16) & 0xF
            self.rd = (self.binary_word >> 12) & 0xF

            # Immediate offset
            if i_bit == 0:
                self.offset = self.binary_word & 0xFFF
                self.operands = {'rd': self.rd,
                                 'rn': self.rn, 'offset': self.offset}
            # Register offset
            else:
                self.rm = self.binary_word & 0xF
                shift_type = (self.binary_word >> 5) & 0x3
                shift_amount = (self.binary_word >> 7) & 0x1F
                self.operands = {'rd': self.rd, 'rn': self.rn, 'rm': self.rm,
                                 'shift_type': shift_type, 'shift_amount': shift_amount}

            if self.l_bit:
                self.instruction_type = 'LDR'
            else:
                self.instruction_type = 'STR'
            return

        # Branch Instructions
        if ((self.binary_word >> 25) & 0b111) == 0b101:
            self.l_bit = (self.binary_word >> 24) & 0x1
            self.offset = self.binary_word & 0x00FFFFFF  # 24-bit offset

            if self.l_bit:
                self.instruction_type = 'BL'
            else:
                self.instruction_type = 'B'
            self.operands = {'offset': self.offset}
            return

        self.instruction_type = 'UNKNOWN'

    def __str__(self):
        if self.instruction_type == 'UNKNOWN':
            return f"UNKNOWN Instruction: {self.binary_word:08X}"
        elif self.instruction_type.startswith('UNKNOWN'):
            return f"{self.instruction_type} Instruction: {self.binary_word:08X}"
        else:
            operand_str = ', '.join(
                [f'{k}: {v}' for k, v in self.operands.items()])
            return f"Type: {self.instruction_type}, Cond: {self.condition_code:X}, Set Flags: {self.set_flags}, Operands: {{{operand_str}}}"


def decode_instructions(binary_data):
    instructions = []
    for i in range(0, len(binary_data), 4):
        word_bytes = binary_data[i:i+4]
        if len(word_bytes) == 4:
            binary_word = struct.unpack('>I', word_bytes)[0]
            instruction = ARMInstruction(binary_word)
            instruction.decode()
            instructions.append(instruction)
    return instructions


class ThumbInstruction(ARMInstruction):
    def __init__(self, binary_word):
        super().__init__(binary_word)
        self.binary_word = binary_word & 0xFFFF

    def decode(self):
        self.instruction_type = 'UNKNOWN_THUMB'
        self.operands = {'binary_word': self.binary_word}

    def __str__(self):
        return f"Type: {self.instruction_type}, Operands: {self.operands}"
