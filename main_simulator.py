
from arm_decoder import decode_instructions
from arm_executor import ARMCPU
from memory import Block
from memory import Cache
import struct


def simulation(binary_file_path):
    cpu = ARMCPU()

    # Preload memory at PC + 4 (0x08) with value 1234 so LDR R1, [PC] loads it
    cpu.memory[8:12] = struct.pack("<I", 1234)

    print("Memory at 0x0C (should be 1234):",
          struct.unpack("<I", cpu.memory[8:12])[0])

    print("--- Registers before Operations ---")
    print(cpu)
    print("-------------------------")

    with open(binary_file_path, "rb") as f:
        binary_data = f.read()

    instructions = decode_instructions(binary_data)
    pc = 0

    for i, instruction in enumerate(instructions):
        print(f"Program Counter: {pc}")
        print(f"\n--- Executing Instruction {i+1} ---")
        print(f"Decoded: {instruction}")
        cpu.execute_instruction(instruction)
        print("--- CPU State After Execution ---")
        print(cpu)
        print("---------------------------------")
        pc = (i * 4)


if __name__ == "__main__":
    simulation("instructions1.bin")
