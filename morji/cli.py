import os
import sys
import subprocess as sp
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
    for event in coqtop_stream(arguments, child):
        print(event)
        match event:
            case ChildExit(status):
                break
            case Data(content, origin):
                if origin == InputOrigin.User:
                    child.stdin.write(content)
                    child.stdin.flush()
                else:
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
                    yield Data(content, origin)
                else:
                    child.stdin.close()
                    running = False
            else:
                assert False, "Unknown file descriptor " \
                              "in coqtop_stream"
    yield ChildExit(child.wait())
