import sys
import subprocess as sp

from typing import List

def main(arguments: List[str]) -> None:
    if arguments:
        match repl := arguments[0]:
            case 'coqtop':
                run_coqtop(arguments)
            case _:
                print(f'{repl} is not supported, sorry')
    else:
        print('Usage: morji [repl command] > output_file')

def run_coqtop(arguments: List[str]) -> None:
    coqtop = sp.Popen(arguments, stdin=sp.PIPE)
    try:
        for line in sys.stdin:
            coqtop.stdin.write(line.encode('utf-8'))
            coqtop.stdin.flush()
    except OSError:
        pass
    coqtop.stdin.close()
    coqtop.wait()
