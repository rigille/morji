#include <Python.h>

#include <stdio.h>
#include <signal.h>
#include <sys/signalfd.h>

static PyObject* childfd(PyObject* self, PyObject* args) {
    sigset_t mask;
    sigemptyset(&mask);
    sigaddset(&mask, SIGCHLD);

    int file = signalfd(-1, &mask, 0);
    if (file < 0) {
        PyErr_SetString(PyExc_IOError, "Could not open file");
        return NULL;
    }

    return Py_BuildValue("i", file);
}

static PyMethodDef methods[] = {
    {"fd", childfd, METH_VARARGS, "Returns a new file descriptor to listen for SIGCHLD signals"},
    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "sigchld",
    "Module for file operations",
    -1,
    methods
};

PyMODINIT_FUNC PyInit_sigchld(void) {
    return PyModule_Create(&module);
}

