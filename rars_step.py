import subprocess
import sys

# --- CONFIGURATION ---
RARS_JAR = "rars.jar"

# Watch list (All registers)
ALL_REGS = [
    "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", "s0", "s1",
    "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
    "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
    "ft0", "ft1", "ft2", "ft3", "ft4", "ft5", "ft6", "ft7",
    "fs0", "fs1", "fa0", "fa1", "fa2", "fa3", "fa4", "fa5", "fa6", "fa7",
    "fs2", "fs3", "fs4", "fs5", "fs6", "fs7", "fs8", "fs9", "fs10", "fs11",
    "ft8", "ft9", "ft10", "ft11"
]

def run_rars(filename, step_limit, program_args):
    # Pass program_args at the end of the command
    cmd = ["java", "-jar", RARS_JAR] + ALL_REGS + [str(step_limit), filename] + program_args
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
    except FileNotFoundError:
        print("Error: 'rars.jar' not found.")
        sys.exit(1)

    # --- CRASH DETECTION ---
    # If the assembler fails, RARS usually prints "Error in..." or "terminated"
    # We must catch this before parsing registers.
    if "Error in " in result.stdout or "terminated due to errors" in result.stdout:
        return None, result.stdout

    regs = {}
    program_output = []
    
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line: continue
        
        # --- NOISE FILTER ---
        if "RARS 1.6" in line: continue
        if "Copyright" in line: continue
        if "step limit" in line: continue 
        
        parts = line.split()
        
        # If it looks like a register (e.g., "t0 5"), save it
        if len(parts) >= 2 and parts[0] in ALL_REGS:
            try:
                regs[parts[0]] = int(parts[1], 0)
            except ValueError:
                pass
        else:
            program_output.append(line)

    return regs, "\n".join(program_output)

def main():
    if len(sys.argv) < 2:
        print("Usage: python rars_cli_final.py <filename.s> [arg1] [arg2] ...")
        sys.exit(1)

    filename = sys.argv[1]
    # Capture any extra arguments passed after the filename
    program_args = sys.argv[2:]
    
    step = 0
    prev_regs = {}
    prev_output_len = 0
    
    print(f"--- Loaded {filename} ---")
    if program_args:
        print(f"Arguments: {program_args}")
    print("Press Enter to step. 'q' to quit.")

    while True:
        try:
            cmd = input("") 
            if cmd == 'q': break
        except KeyboardInterrupt:
            break
            
        step += 1
        curr_regs, curr_output_full = run_rars(filename, step, program_args)
        
        # CHECK FOR CRASH
        if curr_regs is None:
            print(f"\n[System] Assembler Error - Execution Stopped:")
            print(curr_output_full)
            break
        
        # 1. Did the program print text?
        if len(curr_output_full) > prev_output_len:
            new_text = curr_output_full[prev_output_len:]
            print(f"\n>>> OUTPUT: {new_text}\n")
            prev_output_len = len(curr_output_full)
        
        # 2. Did registers change?
        changes = []
        for r in ALL_REGS:
            val_now = curr_regs.get(r, 0)
            val_old = prev_regs.get(r, 0)
            if val_now != val_old:
                changes.append(f"{r}: {val_old} -> {val_now}")
        
        # 3. Print the Step
        if changes:
            print(f"[Step {step}] " + ", ".join(changes))
        else:
            print(f"[Step {step}] Executed")

        # 4. Check for Finish (Stack Pointer Reset)
        sp_old = prev_regs.get("sp", 0)
        sp_now = curr_regs.get("sp", 0)
        
        if step > 1 and sp_old != 0 and sp_now == 0:
            print("\n[System] Program Finished Successfully.")
            break
            
        prev_regs = curr_regs

if __name__ == "__main__":
    main()