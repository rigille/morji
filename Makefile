all:
	gcc -shared -o morji/sigchld.so -fPIC -I/nix/store/ywlgipc99d3xm377anr9kz8aqnbyl522-python3-3.11.8/include/python3.11 c/main.c
