all:
	gcc -shared -o morji/sigchld.so -fPIC -I$(PYTHON_INCLUDE) c/main.c
