# Benchmarks

The benchmark harness exercises the built-in SIR and queue scenarios at two sizes. Run it via the CLI:

```bash
fsim bench --quick
```

The harness prints a Markdown table comparing fast-sim against optional adapters for `simpy` and `mesa`. If those packages are unavailable, the table includes "adapter not available" rows and continues.
