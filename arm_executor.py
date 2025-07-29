import struct


class ARMCPU:
    def __init__(self):
        self.registers = [0] * 16  # R0-R15
        self.registers[15] = 0  # Initialize PC
        self.cpsr = {'N': 0, 'Z': 0, 'C': 0, 'V': 0}  # Status Flags
        self.memory = bytearray(1024)  # Memory

    def _condition_passed(self, condition_code):
        """Check if instruction should execute based on condition code"""
        if condition_code == 0b0000:  # EQ: Equal
            return self.cpsr['Z'] == 1
        elif condition_code == 0b0001:  # NE: Not Equal
            return self.cpsr['Z'] == 0
        elif condition_code == 0b0010:  # CS/HS: Carry Set/Unsigned Higher or Same
            return self.cpsr['C'] == 1
        elif condition_code == 0b0011:  # CC/LO: Carry Clear/Unsigned Lower
            return self.cpsr['C'] == 0
        elif condition_code == 0b0100:  # MI: Negative
            return self.cpsr['N'] == 1
        elif condition_code == 0b0101:  # PL: Positive or Zero
            return self.cpsr['N'] == 0
        elif condition_code == 0b0110:  # VS: Overflow
            return self.cpsr['V'] == 1
        elif condition_code == 0b0111:  # VC: No Overflow
            return self.cpsr['V'] == 0
        elif condition_code == 0b1000:  # HI: Unsigned Higher
            return self.cpsr['C'] == 1 and self.cpsr['Z'] == 0
        elif condition_code == 0b1001:  # LS: Unsigned Lower or Same
            return self.cpsr['C'] == 0 or self.cpsr['Z'] == 1
        elif condition_code == 0b1010:  # GE: Signed Greater Than or Equal
            return self.cpsr['N'] == self.cpsr['V']
        elif condition_code == 0b1011:  # LT: Signed Less Than
            return self.cpsr['N'] != self.cpsr['V']
        elif condition_code == 0b1100:  # GT: Signed Greater Than
            return self.cpsr['Z'] == 0 and self.cpsr['N'] == self.cpsr['V']
        elif condition_code == 0b1101:  # LE: Signed Less Than or Equal
            return self.cpsr['Z'] == 1 or self.cpsr['N'] != self.cpsr['V']
        else:  # AL: Always (1110) or Unconditional (1111)
            return True

    def _update_flags(self, result, carry_out=None, overflow=None):
        """Update CPSR flags based on operation result"""
        result_32 = result & 0xFFFFFFFF
        self.cpsr['N'] = 1 if (result_32 >> 31) & 1 else 0
        self.cpsr['Z'] = 1 if result_32 == 0 else 0

        if carry_out is not None:
            self.cpsr['C'] = 1 if carry_out else 0
        if overflow is not None:
            self.cpsr['V'] = 1 if overflow else 0

    def _get_operand2(self, instruction):
        """Compute operand2 value and carry for shift operations"""
        if 'operand2' in instruction.operands:
            return instruction.operands['operand2'], self.cpsr['C']

        rm_value = self.registers[instruction.operands['rm']]
        shift_type = instruction.operands.get('shift_type')
        shift_amount = instruction.operands.get('shift_amount')
        rs = instruction.operands.get('rs')
        current_carry = self.cpsr['C']

        # Determine shift amount
        if shift_amount is not None:
            sa = shift_amount
        elif rs is not None:
            sa = self.registers[rs] & 0xFF
        else:
            return rm_value, current_carry

        # Handle special shift amounts
        if sa == 0:
            return rm_value, current_carry

        # Perform shift operations
        if shift_type == 0b00:  # LSL
            if sa > 31:
                return 0, 0
            result = (rm_value << sa) & 0xFFFFFFFF
            carry_out = (rm_value >> (32 - sa)) & 1 if sa <= 32 else 0
            return result, carry_out

        elif shift_type == 0b01:  # LSR
            if sa > 32:
                return 0, 0
            sa = 32 if sa == 0 else sa  # LSR #0 = LSR #32
            result = rm_value >> sa
            carry_out = (rm_value >> (sa - 1)) & 1 if sa > 0 else 0
            return result, carry_out

        elif shift_type == 0b10:  # ASR
            if sa > 31:
                sa = 32
            if sa == 0:  # ASR #0 = ASR #32
                sa = 32
            # Handle sign extension
            if rm_value & 0x80000000:
                result = (rm_value >> sa) | (0xFFFFFFFF << (32 - sa))
            else:
                result = rm_value >> sa
            result &= 0xFFFFFFFF
            carry_out = (rm_value >> (sa - 1)) & 1 if sa > 0 else 0
            return result, carry_out

        elif shift_type == 0b11:  # ROR
            sa = sa % 32
            if sa == 0:
                return rm_value, current_carry
            result = ((rm_value >> sa) | (rm_value << (32 - sa))) & 0xFFFFFFFF
            carry_out = (result >> 31) & 1
            return result, carry_out

        return rm_value, current_carry

    def execute_instruction(self, instruction):
        """Execute decoded ARM instruction"""
        # Check condition code
        if not self._condition_passed(instruction.condition_code):
            return

        # Get PC (R15) and increment for next instruction
        pc = self.registers[15]
        self.registers[15] = pc + 4

        # Execute instruction
        if instruction.instruction_type == 'MOV':
            rd = instruction.operands['rd']
            operand2, _ = self._get_operand2(instruction)
            self.registers[rd] = operand2
            if instruction.set_flags:
                self._update_flags(operand2)

        elif instruction.instruction_type == 'LDR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            offset = instruction.operands.get('offset', 0)
            rm = instruction.operands.get('rm')

            base = self.registers[rn]
            if rm is not None:
                offset = self.registers[rm]

            address = base + offset
            if 0 <= address < len(self.memory) - 3:
                value = struct.unpack('<I', self.memory[address:address+4])[0]
                self.registers[rd] = value

        elif instruction.instruction_type == 'STR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            offset = instruction.operands.get('offset', 0)
            rm = instruction.operands.get('rm')

            base = self.registers[rn]
            if rm is not None:
                offset = self.registers[rm]

            address = base + offset
            value = self.registers[rd]
            if 0 <= address < len(self.memory) - 3:
                self.memory[address:address+4] = struct.pack('<I', value)

        elif instruction.instruction_type == 'ADD':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2, carry_in = self._get_operand2(instruction)
            op1 = self.registers[rn]
            result = op1 + operand2
            self.registers[rd] = result & 0xFFFFFFFF

            if instruction.set_flags:
                carry_out = result > 0xFFFFFFFF
                overflow = ((op1 ^ result) & (
                    operand2 ^ result)) & 0x80000000 != 0
                self._update_flags(result, carry_out, overflow)

        elif instruction.instruction_type == 'SUB':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2, _ = self._get_operand2(instruction)
            op1 = self.registers[rn]
            result = op1 - operand2
            self.registers[rd] = result & 0xFFFFFFFF

            if instruction.set_flags:
                carry_out = op1 >= operand2
                overflow = ((op1 ^ operand2) & (
                    op1 ^ result)) & 0x80000000 != 0
                self._update_flags(result, carry_out, overflow)

        elif instruction.instruction_type == 'MUL':
            rd = instruction.operands['rd']
            rm = instruction.operands['rm']
            rs = instruction.operands['rs']
            result = self.registers[rm] * self.registers[rs]
            self.registers[rd] = result & 0xFFFFFFFF
            if instruction.set_flags:
                self._update_flags(result)

        elif instruction.instruction_type == 'MLA':
            rd = instruction.operands['rd']
            rm = instruction.operands['rm']
            rs = instruction.operands['rs']
            rn = instruction.operands['rn']
            result = (self.registers[rm] *
                      self.registers[rs]) + self.registers[rn]
            self.registers[rd] = result & 0xFFFFFFFF
            if instruction.set_flags:
                self._update_flags(result)

        elif instruction.instruction_type == 'AND':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2, _ = self._get_operand2(instruction)
            result = self.registers[rn] & operand2
            self.registers[rd] = result
            if instruction.set_flags:
                self._update_flags(result)

        elif instruction.instruction_type == 'ORR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2, _ = self._get_operand2(instruction)
            result = self.registers[rn] | operand2
            self.registers[rd] = result
            if instruction.set_flags:
                self._update_flags(result)

        elif instruction.instruction_type == 'EOR':
            rd = instruction.operands['rd']
            rn = instruction.operands['rn']
            operand2, _ = self._get_operand2(instruction)
            result = self.registers[rn] ^ operand2
            self.registers[rd] = result
            if instruction.set_flags:
                self._update_flags(result)

        elif instruction.instruction_type == 'CMP':
            rn = instruction.operands['rn']
            operand2, _ = self._get_operand2(instruction)
            op1 = self.registers[rn]
            result = op1 - operand2
            carry_out = op1 >= operand2
            overflow = ((op1 ^ operand2) & (op1 ^ result)) & 0x80000000 != 0
            self._update_flags(result, carry_out, overflow)

        elif instruction.instruction_type in ('LSL', 'LSR', 'ASR', 'ROR'):
            rd = instruction.operands['rd']
            rm = instruction.operands['rm']
            shift_type = {
                'LSL': 0b00,
                'LSR': 0b01,
                'ASR': 0b10,
                'ROR': 0b11
            }[instruction.instruction_type]

            # Get shift amount
            if 'shift_amount' in instruction.operands:
                sa = instruction.operands['shift_amount']
            elif 'rs' in instruction.operands:
                sa = self.registers[instruction.operands['rs']] & 0xFF
            else:
                sa = 0

            # Perform shift
            value = self.registers[rm]
            if shift_type == 0b00:  # LSL
                if sa == 0:
                    result = value
                    carry_out = self.cpsr['C']
                elif sa > 31:
                    result = 0
                    carry_out = 0
                else:
                    result = (value << sa) & 0xFFFFFFFF
                    carry_out = (value >> (32 - sa)) & 1

            elif shift_type == 0b01:  # LSR
                if sa == 0 or sa == 32:
                    result = 0
                    carry_out = (value >> 31) & 1
                elif sa > 32:
                    result = 0
                    carry_out = 0
                else:
                    result = value >> sa
                    carry_out = (value >> (sa - 1)) & 1

            elif shift_type == 0b10:  # ASR
                if sa == 0 or sa >= 32:
                    if value & 0x80000000:
                        result = 0xFFFFFFFF
                        carry_out = 1
                    else:
                        result = 0
                        carry_out = 0
                else:
                    if value & 0x80000000:
                        result = (value >> sa) | (0xFFFFFFFF << (32 - sa))
                    else:
                        result = value >> sa
                    result &= 0xFFFFFFFF
                    carry_out = (value >> (sa - 1)) & 1

            elif shift_type == 0b11:  # ROR
                sa %= 32
                if sa == 0:
                    result = value
                    carry_out = self.cpsr['C']
                else:
                    result = ((value >> sa) | (
                        value << (32 - sa))) & 0xFFFFFFFF
                    carry_out = (result >> 31) & 1

            self.registers[rd] = result
            if instruction.set_flags:
                self._update_flags(result, carry_out)

        elif instruction.instruction_type == 'B':
            offset = instruction.operands['offset']
            # Sign extend 24-bit offset to 32 bits
            if offset & 0x00800000:
                offset |= 0xFF000000
            # Shift left by 2 (word alignment)
            offset <<= 2
            # Calculate new PC (current PC + 8 + offset)
            self.registers[15] = (pc + 8 + offset) & 0xFFFFFFFF

        elif instruction.instruction_type == 'BL':
            offset = instruction.operands['offset']
            # Sign extend and shift offset
            if offset & 0x00800000:
                offset |= 0xFF000000
            offset <<= 2
            # Store return address in LR (R14)
            self.registers[14] = pc + 4
            # Update PC
            self.registers[15] = (pc + 8 + offset) & 0xFFFFFFFF

    def __str__(self):
        reg_str = ", ".join(
            [f"R{i}: {self.registers[i]:08X}" for i in range(16)])
        cpsr_str = ", ".join([f"{k}: {v}" for k, v in self.cpsr.items()])
        return f"Registers: {reg_str}\nCPSR: {cpsr_str}"
