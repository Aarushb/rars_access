import subprocess
import sys

# --- CONFIGURATION ---
RARS_JAR = "rars.jar"

# Watch list (All RISC-V Registers)
ALL_REGS = [
    "zero", "ra", "sp", "gp", "tp", "t0", "t1", "t2", "s0", "s1",
    "a0", "a1", "a2", "a3", "a4", "a5", "a6", "a7",
    "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9", "s10", "s11", "t3", "t4", "t5", "t6",
    "ft0", "ft1", "ft2", "ft3", "ft4", "ft5", "ft6", "ft7",
    "fs0", "fs1", "fa0", "fa1", "fa2", "fa3", "fa4", "fa5", "fa6", "fa7",
    "fs2", "fs3", "fs4", "fs5", "fs6", "fs7", "fs8", "fs9", "fs10", "fs11",
    "ft8", "ft9", "ft10", "ft11"
]

class RarsSession:
    def __init__(self, filename, args):
        self.filename = filename
        self.program_args = args
        self.current_step = 0
        self.prev_regs = {}
        self.prev_output_len = 0
        # Safety limit for 'Run' (5 million steps)
        self.MAX_RUN_STEPS = 5000000 

    def execute(self, mode="step"):
        """
        Runs RARS with specific parameters.
        mode: "step" (increment by 1) or "run" (go to max limit)
        """
        
        cmd = ["java", "-jar", RARS_JAR]

        # Determine limits and flags based on mode
        if mode == "step":
            self.current_step += 1
            limit = self.current_step
            # CRITICAL: We MUST ask for registers in Step mode to see changes
            cmd += ALL_REGS
        elif mode == "run":
            limit = self.current_step + self.MAX_RUN_STEPS
            # CRITICAL: We DO NOT ask for registers in Run mode.
            # 1. It improves performance.
            # 2. It prevents the "Input File interpreted as Source" bug in RARS CLI.
            # If user hits breakpoint, they can Step once to see regs.
        else:
            limit = self.current_step
            cmd += ALL_REGS

        # Add limit, filename, and args
        cmd += [str(limit), self.filename] + self.program_args
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
        except FileNotFoundError:
            print("Error: 'rars.jar' not found in this directory.")
            sys.exit(1)

        return self.parse_result(result, mode)

    def parse_result(self, result, mode):
        """
        Parses stdout from RARS to extract registers, output, and status.
        """
        # 1. Check for Crashes/Errors immediately
        if "Error in " in result.stdout or "terminated due to errors" in result.stdout:
            return None, result.stdout, "error"

        output_lines = result.stdout.splitlines()
        regs = {}
        program_output = []
        status = "running"
        
        # 2. Check for Breakpoints
        if "paused at breakpoint" in result.stdout.lower():
            status = "breakpoint"
            
        for line in output_lines:
            line = line.strip()
            if not line: continue
            
            # Filter noise
            if "RARS 1.6" in line: continue
            if "Copyright" in line: continue
            if "step limit" in line: continue 
            
            parts = line.split()
            
            # Parse Registers (Only present if we asked for them in 'step' mode)
            if len(parts) >= 2 and parts[0] in ALL_REGS:
                try:
                    regs[parts[0]] = int(parts[1], 0)
                except ValueError:
                    pass
            else:
                # Capture standard program output
                program_output.append(line)

        # 3. Detect Program Finish
        sp_old = self.prev_regs.get("sp", 0)
        sp_now = regs.get("sp", 0)
        
        # Finish logic varies by mode
        if mode == "run":
            # In Run mode, we don't track SP (regs are hidden). 
            # We assume finish if no breakpoint and no crash.
            if status != "breakpoint":
                status = "finished"
        else:
            # In Step mode, we check Stack Pointer reset
            if sp_old != 0 and sp_now == 0:
                status = "finished"
        
        return regs, "\n".join(program_output), status

    def print_changes(self, new_regs, full_output):
        """
        Calculates differences and prints them accessibly.
        """
        # 1. Output Text
        if len(full_output) > self.prev_output_len:
            new_text = full_output[self.prev_output_len:]
            print(f"\n>>> OUTPUT: {new_text}\n")
            self.prev_output_len = len(full_output)

        # 2. Register Changes
        changes = []
        for r in ALL_REGS:
            val_now = new_regs.get(r, 0)
            val_old = self.prev_regs.get(r, 0)
            if val_now != val_old:
                changes.append(f"{r}: {val_old} -> {val_now}")

        # Only print execution status if we have info or are stepping
        if changes:
            print(f"[{self.current_step}] " + ", ".join(changes))
        elif new_regs: # If we have regs but no changes (e.g. nop)
             print(f"[{self.current_step}] Executed")
        
        self.prev_regs = new_regs

def main():
    if len(sys.argv) < 2:
        print("Usage: python rars_cli.py <filename.s> [arg1] [arg2] ...")
        sys.exit(1)

    filename = sys.argv[1]
    args = sys.argv[2:]
    
    session = RarsSession(filename, args)
    
    print(f"--- Loaded {filename} ---")
    if args:
        print(f"Arguments: {args}")
    print("Commands:")
    print("  <Enter> : Step (1 instruction)")
    print("  r       : Run (Until completion or breakpoint)")
    print("  q       : Quit")

    while True:
        try:
            cmd = input(f"[{session.current_step}]> ").strip().lower()
        except KeyboardInterrupt:
            break

        if cmd == 'q':
            break
        
        mode = "step"
        if cmd == 'r':
            mode = "run"
            print("[System] Running...")

        regs, output, status = session.execute(mode)

        if status == "error":
            print(f"\n[System] Assembler Error - Execution Stopped:")
            print(output)
            break
            
        if status == "breakpoint":
            print(f"\n[System] Paused at Breakpoint.")
            # We don't have regs yet in Run mode, but user can hit Enter to see them next.
            
        session.print_changes(regs, output)

        if status == "finished":
            print("\n[System] Program Finished Successfully.")
            break

if __name__ == "__main__":
    main()