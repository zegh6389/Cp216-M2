import struct


def hex_to_bin(hexword):
    return int(hexword, 16)


def generate_binary(file):

    # Instruction 1: MOV r0, #0x80 (value of 129)
    instr1 = hex_to_bin("E3A00080")

    # Instruction 2: LDR R1, [pc]
    instr2 = hex_to_bin("E59F1000")

    # Instruction 3: STR r2, [R1]
    instr3 = hex_to_bin("E5812000")

    # Instruction 4: ADD r3, r1, r2
    instr4 = hex_to_bin("E0813002")

    # Instruction 5: SUB r4, r2, r3
    instr5 = hex_to_bin("E0424003")

    # Instruction 6: MUL r5, r1, r4
    instr6 = hex_to_bin("E0050194")

    # Instruction 7: CMP r0, r5
    instr7 = hex_to_bin("E1500005")

    # Instruction 8: AND r6, r0, r5
    instr8 = hex_to_bin("E0006005")

    # Instruction 9: ORR r7, r0, r5
    instr9 = hex_to_bin("E1807005")

    # Instruction 10: SUBNE r0, r0, r5 (Condition NE)
    instr10 = hex_to_bin("10400005")

    # Instruction 11: ADDEQ r6, r7, r8 (Condition EQ)
    instr11 = hex_to_bin("00876008")

    # Instruction 12: LSL r1, r0, #2 (Similar to MOV)
    instr12 = hex_to_bin("E1A01100")

    # Instruction 13: LSR r2, r0, #2 (Similar to MOV)
    instr13 = hex_to_bin("E1A02120")

    # Instruction 14: ASR r4, r1, #5
    instr14 = hex_to_bin("E1A042C1")

    # Instruction 15: ROR r0, r0, #2
    instr15 = hex_to_bin("E1A00160")

    binary_words = [instr1, instr2, instr3, instr4, instr5, instr6, instr7,
                    instr8, instr9, instr10, instr11, instr12, instr13, instr14, instr15]
    with open(file, "wb") as f:
        for i in binary_words:
            f.write(struct.pack(">I", i))

    print(f"Generated binary file: {file}")


if __name__ == "__main__":
    import os
current_dir = os.path.dirname(os.path.abspath(__file__))
generate_binary(os.path.join(current_dir, "instructions1.bin"))

