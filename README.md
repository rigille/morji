# morji
The main intent of this experiment was to allow me to save coqtop interactive sessions like this:
```
morji coqtop > Result.v
```
Ignoring lines that errored out. However it's not easy to infer exactly what was rejected by coqtop because of warnings and also because of lines with many commands. So use it at your own caution.

Probably I'll need to patch coqtop itself to get what I want.

# Try it
Install nix with the Determinate Systems installer if you haven't already and then
```
nix shell
```
This should make `morji` available in your shell session.
