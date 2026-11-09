# Contributing to Kestrel

Thanks for taking a look at Kestrel. This is a small engine fork, so focused
changes with clear evidence are more useful than broad refactors.

## Before you start

- Kestrel is an engine, not a GUI. UCI compatibility matters.
- The engine is derived from Patricia 5.1. Preserve the MIT notice and the
  existing attribution.
- Submit only code that you can license under the MIT license. Do not copy
  code from projects with incompatible licenses.

## Build and test

Build from the repository root:

```bash
make
```

Run the UCI smoke test on Windows:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File tests/uci-smoke.ps1
```

For engine changes, also run the built-in benchmark and a perft check:

```bash
./engine/kestrel.exe bench
./engine/kestrel.exe perft 5
```

Please include the compiler, platform, and commands you used in the pull
request description.

## Pull requests

- Keep each change focused and explain why it is needed.
- Preserve the UCI option names and behavior unless the change is intentional
  and documented.
- Do not commit build products to `engine/`. The checked-in binary belongs in
  `bin/` and should be updated only for a deliberate release.
- Update `README.md` or `SHA256SUMS` when the packaged binary changes.

## License

By contributing, you agree that your contribution is licensed under the MIT
License in [`LICENSE`](LICENSE).
