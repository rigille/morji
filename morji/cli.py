import os
import sys
import subprocess as sp
from collections import deque
from enum import Enum
from select import select
from dataclasses import dataclass
from typing import Optional

import sigchld

from typing import List

debugging = bool(os.getenv('MORJI_DEBUG'))

def main(arguments: List[str]) -> None:
    if arguments:
        match repl := arguments[0]:
            case 'coqtop':
                coqtop(arguments)
            case _:
                print(f'{repl} is not supported, sorry')
    else:
        print('Usage: morji [repl command] >> target_file')

@dataclass(slots=True)
class State:
    queue: Optional[deque]
    staged: str
    committed: str

def coqtop(arguments: List[str]) -> None:
    child = sp.Popen(arguments, stdin=sp.PIPE,
                     stdout=sp.PIPE, stderr=sp.PIPE)
    state = State(deque(), b'', b'')
    print(state) if debugging else None
    for event in coqtop_stream(arguments, child):
        print(event) if debugging else None
        match (event, state):
            case (ChildExit(status), _):
                if status == 0:
                    sys.stdout.write(state.committed.decode('utf-8'))
                    sys.stdout.flush()
                break
            case (Data(content, InputOrigin.User), State(None, _, _)):
                child.stdin.write(content)
                child.stdin.flush()
                state.queue = deque()
                state.staged += content
            case (Data(content, InputOrigin.User), _):
                state.queue.append(content)
            case (Data(content, origin), _):
                if origin is InputOrigin.ChildStderr:
                    if content.endswith(b' < '):
                        if content.count(b'\n') <= 1:
                            state.committed += state.staged
                        if isinstance(state.queue, deque):
                            if not state.queue:
                                state.queue = None
                            else:
                                child.stdin.write(state.queue.popleft())
                                child.stdin.flush()
                    else:
                        assert False, f'illegal state for prompt: {state}'
                else:
                    state.committed += state.staged
                state.staged = b''
                payload = content.decode('utf-8')
                sys.stderr.write(payload)
                sys.stderr.flush()
        print(state) if debugging else None

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
    fds = [child_fd, out_fd, err_fd, user_fd]
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
                    running = False
            else:
                assert False, "Unknown file descriptor " \
                              "in coqtop_stream"
    child.stdin.close()
    os.set_blocking(user_fd, True)
    yield ChildExit(child.wait())
