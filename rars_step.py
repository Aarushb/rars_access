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
        # A safety limit for 'Run' to prevent infinite loop hangs
        self.MAX_RUN_STEPS = 100000 

    def execute(self, mode="step"):
        """
        Runs RARS with specific parameters.
        mode: "step" (increment by 1) or "run" (go to max limit)
        """
        
        # Determine the step limit for this execution
        if mode == "step":
            self.current_step += 1
            limit = self.current_step
        elif mode == "run":
            # For 'Run', we set a high limit relative to current
            # This allows us to fast-forward
            limit = self.current_step + self.MAX_RUN_STEPS
        else:
            limit = self.current_step

        # Build Command
        # java -jar rars.jar [regs...] [limit] filename [args...]
        cmd = ["java", "-jar", RARS_JAR] + ALL_REGS + [str(limit), self.filename] + self.program_args

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
        output_lines = result.stdout.splitlines()
        regs = {}
        program_output = []
        status = "running"
        
        # 1. Check for Crashes/Errors immediately
        if "Error in " in result.stdout or "terminated due to errors" in result.stdout:
            return None, result.stdout, "error"

        # 2. Check for Breakpoints or Completion
        # RARS usually prints "Execution paused at breakpoint" or similar text
        is_paused = "paused at breakpoint" in result.stdout.lower()
        
        for line in output_lines:
            line = line.strip()
            if not line: continue
            
            # Filter noise
            if "RARS 1.6" in line: continue
            if "Copyright" in line: continue
            if "step limit" in line: continue 
            
            # Detect Breakpoint explicitly in output lines
            if "paused at breakpoint" in line.lower():
                status = "breakpoint"
                continue

            parts = line.split()
            
            # Parse Registers
            if len(parts) >= 2 and parts[0] in ALL_REGS:
                try:
                    regs[parts[0]] = int(parts[1], 0)
                except ValueError:
                    pass
            else:
                # Capture standard program output (Print calls)
                program_output.append(line)

        # 3. Detect Program Finish (Stack Pointer Check)
        # If sp was non-zero before and is 0 now, RARS likely reset (finished)
        sp_old = self.prev_regs.get("sp", 0)
        sp_now = regs.get("sp", 0)
        
        # If we ran and didn't hit a breakpoint, and SP is 0, we finished.
        if mode == "run" and status != "breakpoint":
            if sp_now == 0 and sp_old != 0:
                status = "finished"
        
        # Return format: (Registers, Full Text Output, Status String)
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

        if changes:
            print(f"[{self.current_step}] " + ", ".join(changes))
        else:
            print(f"[{self.current_step}] Executed (No register changes)")

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
        
        # --- EXECUTION LOGIC ---
        mode = "step"
        if cmd == 'r':
            mode = "run"
            print("[System] Running...")

        regs, output, status = session.execute(mode)

        # Handle Crash
        if status == "error":
            print(f"\n[System] Assembler Error - Execution Stopped:")
            print(output)
            break
            
        # Handle Breakpoint
        if status == "breakpoint":
            print(f"\n[System] Paused at Breakpoint.")
            # If we were running, we need to update our internal step count
            # Note: RARS CLI doesn't easily give us the exact step count on break.
            # We assume the user will inspect registers here.
            
        # Print what happened
        session.print_changes(regs, output)

        # Handle Finish
        if status == "finished":
            print("\n[System] Program Finished Successfully.")
            break
        
        # If we ran fast, updating the step number for display is tricky
        # because RARS resets every time.
        # We assume the user continues stepping from where they left off visually.

if __name__ == "__main__":
    main()