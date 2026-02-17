\# RARS Accessibility Wrapper



\## What's this?



This is a wrapper script for the \[RARS](https://github.com/TheThirdOne/rars) (RISC-V Assembler and Runtime Simulator) CLI. It is designed to act as an accessible bridge, allowing you to interactively debug and execute RISC-V assembly code such as stepping through instructions one by one without needing to rely on the inaccessible graphical interface or manually wrangle the verbose command-line arguments for every single step.



\## Why's this?



I am currently taking \[CMPUT 229](https://apps.ualberta.ca/catalogue/course/cmput/229) (Computer Organization and Architecture) at the University of Alberta. I am also fully blind.



The standard tool for this course is RARS. Unfortunately, RARS is built using Java Swing, a GUI toolkit that draws its own controls rather than using the operating system's native ones. While the \*Java Access Bridge\* theoretically connects Java apps to screen readers like NVDA or JAWS, it fails significantly here. RARS does not expose accessibility properties (like names, roles, or states) for its custom components, nor does it hook into accessibility libraries like \[tolk](https://github.com/dkager/tolk), \[accessible\_output2](https://github.com/accessibleapps/accessible\_output2) or \[UniversalSpeech](https://github.com/qtnc/UniversalSpeech) to announce dynamic changes, such as the output window updating or registers changing values. In practice, this means that I can perform basic navigation items (tab through the window to various controls, space/enter to activate, alt f4 to close, alt to activate and navigate menu) but this is the upper limit. The editor, almost certainly built using custom UI elements, for example, is entirely inaccessible.



This caused me to hit a wall immediately in the first lab: stepping through code. In the UI, a sighted student can click "Step" and immediately see what line is running and which register changed. To do the same thing in the CLI requires a verbose command, manual calculation of steps, and sifting through a massive dump of text just to find one changed value.



I am not new to the prospect of visually impaired students having to do >=2x more work than sighted peers to keep up, especially in the stem field. I have been trying my best to make this not the case or at least a lot less of a case than before. This is another one of those, albeit small, contributions towards that endeavour and making people less afraid to take up STEM courses, and to prevent burnout once in.



\## How this solves the problem



"Solves" might be a bit generous; I would say it acts as a much-needed smoothing bridge. It wraps the native RARS CLI commands and handles the messy work for you.



Instead of needing to learn complex argument flags and manually parse the output every time you want to move forward, this script lets you run your code interactively. You press `Enter`, and it handles the backend logic—running the simulator, calculating the difference in registers, and presenting you with exactly what you need to know (what changed and what printed) without the bloat.



\## Features



\* Interactive Stepping: Step through your code instruction-by-instruction with a simple key press, mimicking the "Step" button in the UI.

\* Smart Register Tracking: Automatically detects and announces only the registers that have changed value, so you don't have to scan a full table.

\* Noise Filtering: Strips away the RARS copyright headers and execution logs, delivering clean program output.

\* Crash Reporting: Catches assembler errors and reports the specific line number immediately.

\* Argument Support: Seamlessly passes command-line arguments to your assembly program.



\## Future Plans



Please keep in mind that this is a learning and iterative process. I am adding features as I progress through the course and discover new needs. The timeline of these updates will likely depend on my course schedule.



Hopefully, by the time I'm finished, this can serve as a one-stop solution for an accessible RARS CLI wrapper.



\*\*Planned Features:\*\*



\* Memory Inspection: A structured way to view memory segments. Right now, scanning memory tables in a linear fashion via the raw CLI dump is a nightmare; we need a way to query specific addresses easily.

\* Breakpoint Management: Interactive commands to run until a specific line or label.

\* An (\*\*Accessible\*\*) UI: I understand that not everyone is a terminal geek like me. Many people still prefer a UI for friendliness. I want to reduce this trend that Access means having to learn an entirely different way of working just to do what everyone else can do in a more beginner-friendly way. I am exploring a text-based UI (TUI) or a simple web front-end to help with this. It would also aid in things like the aforementioned memory inspection problem, as a table could be presented and navigated by screen readers as a table rather than a linear dump.



---



Ideally, accessibility should be baked into the core application, not taped on the side. I am a huge proponent of inclusive software design. Due to their inherent limitations, I do appreciate it when we do get software that makes otherwise inaccessible things accessible, but I also very much appreciate it when they are baked into existing apps that everyone else uses rather than isolated separate programs we have to run, causing more social isolation and segregation.



My "dream" scenario involves one of two paths:



1\. A massive PR to RARS: Porting the UI to a modern, accessible Java library (like SWT) or implementing the Java Accessibility API properly into the existing one. The latter alternative, though, I foresee being a web of spaghetti code and hacky workarounds.

2\. A Rewrite in Rust: Rebuilding the entire simulator in Rust. The ecosystem already exists; crates like `riscv` handle the emulation, and `ratatui` could generate a beautiful, screen-reader-accessible terminal UI. Better, but hardest.



I love building software, especially ones that break barriers. However, I do not like doing it halfway or compromising on quality. Optimizing my software for best results by truly knowing conceptually and practically  what goes on behind the scene is, as per my understanding, at the core of computing science, and is why I took this course. Many people can learn how to program these days. Most can code even without touching it now. But writing \*\*good\*\* software is what takes exercising that mental muscle.



Thus, I don't feel confident enough in low-level systems programming \*yet\* to tackle a full emulator rewrite, but after CMPUT 229, who knows; I might give it a go. If anyone wants to collaborate on that, please reach out.



\## Instructions



1\. Place the `rars\_cli.py` script in the same folder as your `rars.jar`.

2\. Run the script with your assembly file:

```bash

python rars\_cli.py lab1-hello.s

```



3\. If your program requires arguments, just add them to the end:

```bash

python rars\_cli.py lab1-hello.s arg1 arg2

```



\## Conclusion



So, that's what this is. I hope you find it useful. Feedback is always welcome, as are contributions in the form of issues (or even better, pull requests!).

