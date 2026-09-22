# Benchmarking

`benchmarks/run_benchmarks.py` measures the local event/risk path and writes CSV/JSON results. It does not claim the SRS GPU targets. A complete evaluation must run the Appendix B protocol with the intended hardware, model versions, 100 warm-up inferences, 1,000 measured inferences, batch sizes 1/2/4/8/16/32, three repeats, and concurrency replay.
