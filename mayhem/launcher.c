/* launcher.c — a tiny ELF that exec()s a Python entry point, forwarding argv.
 *
 * Mayhem requires every fuzz target `cmd:` to be an ELF binary (it rejects a script /
 * shebang wrapper, and fuzz-smoke.sh checks the ELF magic). python-pptx is pure Python,
 * so the Atheris libFuzzer harness is a `.py`. This shim is the ELF Mayhem launches; it
 * immediately execs `python3 <PY_SCRIPT> <args...>`, handing the libFuzzer/Atheris flags
 * straight through. The Python process then IS the libFuzzer target (it iterates inputs).
 *
 * The same shim also fronts the behavioral test runner (mayhem/run_tests.py) so the
 * verify-repo sabotage oracle (an LD_PRELOAD constructor that _exit(0)s every NON-system
 * executable) can neuter it: the system /usr/bin/python3 is spared, but this /mayhem/<name>
 * ELF is not, so under sabotage it exits before the suite runs and test.sh reports failure.
 *
 * Built with $DEBUG_FLAGS (DWARF < 4) per SPEC §6.2 item 10, and dynamically linked so the
 * sabotage oracle's LD_PRELOAD constructor can reach it.
 */
#include <stdlib.h>
#include <unistd.h>

#ifndef PY_SCRIPT
#define PY_SCRIPT "/mayhem/mayhem/fuzz_load.py"
#endif

int main(int argc, char **argv) {
    char **nv = (char **)malloc((size_t)(argc + 2) * sizeof(char *));
    if (!nv) return 1;
    nv[0] = (char *)"python3";
    nv[1] = (char *)PY_SCRIPT;
    for (int i = 1; i < argc; i++) nv[i + 1] = argv[i];
    nv[argc + 1] = NULL;
    execvp("python3", nv);
    return 127; /* exec failed */
}
