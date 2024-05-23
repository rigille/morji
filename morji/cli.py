import os
import sys
import subprocess as sp
from collections import deque
from enum import Enum
from select import select
from dataclasses import dataclass

import sigchld

from typing import List

def main(arguments: List[str]) -> None:
    if arguments:
        match repl := arguments[0]:
            case 'coqtop':
                coqtop(arguments)
            case _:
                print(f'{repl} is not supported, sorry')
    else:
        print('Usage: morji [repl command] >> target_file')

def coqtop(arguments: List[str]) -> None:
    child = sp.Popen(arguments, stdin=sp.PIPE,
                     stdout=sp.PIPE, stderr=sp.PIPE)
    state = deque()
    for event in coqtop_stream(arguments, child):
        print(event, state)
        match (event, state):
            case (ChildExit(status), _):
                break
            case (Data(content, InputOrigin.User), None):
                child.stdin.write(content)
                child.stdin.flush()
                state = deque()
            case (Data(content, InputOrigin.User), _):
                state.append(content)
            case (Data(content, InputOrigin.ChildStderr), _):
                if content == b'\nCoq < ':
                    if isinstance(state, deque):
                        if not state:
                            state = None
                        else:
                            child.stdin.write(state.popleft())
                            child.stdin.flush()
                    else:
                        assert False, f"illegal state for prompt: {state}"
                payload = content.decode('utf-8')
                sys.stderr.write(payload)
                sys.stderr.flush()

@dataclass(slots=True)
class ChildExit:
    status: int

class InputOrigin(Enum):
    User = 0
    ChildStdout = 1
    ChildStderr = 2

@dataclass(slots=True)
class Data:
    content: bytes
    origin: InputOrigin

def coqtop_stream(arguments: List[str], child):
    child_fd = sigchld.fd()
    user_fd = sys.stdin.fileno()
    out_fd = child.stdout.fileno()
    err_fd = child.stderr.fileno()
    incomplete_line = b""
    fds = [child_fd, err_fd, out_fd, user_fd]
    for fd in fds:
        os.set_blocking(fd, False)
    running = True
    while running:
        inbox, _, _ = select(fds, [], [])
        for fd in inbox:
            if fd == child_fd:
                running = False
            elif fd == err_fd:
                content = child.stderr.read()
                if content:
                    origin = InputOrigin.ChildStderr
                    yield Data(content, origin)
                else:
                    running = False
            elif fd == out_fd:
                content = child.stdout.read()
                if content:
                    origin = InputOrigin.ChildStdout
                    yield Data(content, origin)
                else:
                    running = False
            elif fd == user_fd:
                content = sys.stdin.read().encode('utf-8')
                if content:
                    origin = InputOrigin.User
                    content = incomplete_line + content
                    lines = content.split(b'\n')
                    for line in lines[:-1]:
                        yield Data(line + b'\n', origin)
                    incomplete_line = lines[-1]
                else:
                    child.stdin.close()
                    running = False
            else:
                assert False, "Unknown file descriptor " \
                              "in coqtop_stream"
    yield ChildExit(child.wait())
