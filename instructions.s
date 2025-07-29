/*
-------------------------------------------------------
instructions.s
-------------------------------------------------------
Author: Ali Syed Muhammed, Abrar Usman, Obada Zarzour, Awais Zegham
ID:
Email:
Date: 2025-06-19
-------------------------------------------------------
15 ARM Instructions to fetch, decode and execute.
-------------------------------------------------------
*/
.org 0x00  // Start at memory location 00
.text        // Code section
.global _start
_start:

MOV r0, #0x80 // Instruction #1: MOV (Move Data)
LDR r1, [pc]   // Instruction #2: LDR (Load Data)
LDR r2, [r1]
STR r2, [R1]     // Instruction #3: STR (Store Data)
ADD r3, r1, r2   // Instruction #4: ADD (Addition)
SUB r4, r2, r3   // Instruction #5: SUB (Subtraction)
MUL r5, r1, r4   // Instruction #6: MUL (Multiplication)
SUB r5, r4, r5
CMP r0, r5       // Instruction #7: CMP (Compare)
AND r6, r0, r5   // Instruction #8: AND (AND Logic Gate)
ORR r7, r0, r5   // Instruction #9: ORR (OR Logic Gate)
SUBNE r0, r0, r5 // Instruction #10: NE (Not Equal)
CMP r7, r8
ADDEQ r6, r7, r8 // Instruction #11: EQ (Equal)
LSL r1, r0, #2   // Instruction #12: LSL (Logical Shift Left)
LSR r2, r0, #2   // Instruction #13: LSR (Logical Shift Right)
ASR r4, r1, #5   // Instruction #14: ASR (Arithmetic Shift Right)
ROR r0, r0, #2   // Instruction #15: ROR (Rotate Right)

_stop:
b _stop

.end
