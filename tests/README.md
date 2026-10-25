# Regression tests

Run from the repository root with Python 3.10 or newer:

```sh
python -m unittest discover -s tests -v
```

Server tests create temporary profiles and exercise actual damage, reward, packet and lifecycle methods. They do not connect to official servers or require an account. The native Hellstorm lookup test is optional: it runs only when `HELLSTORM_NATIVE_DLL` points to a client `GameAssembly.dll` and Unicorn is installed, and skips otherwise.
