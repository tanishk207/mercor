# Speed Up an Open-Source Library

## Repo and commit

This submission targets `networkx/networkx` at baseline commit `9210d9c5bb9875caae0c7be2214abebfdd9255d2`, which corresponds to the NetworkX 3.1 release. NetworkX is open source under a BSD-style permissive license, has a public Git history, and includes an automated test suite.

The chosen workload is node betweenness centrality on an unweighted undirected graph with 1500 nodes and 50000 edges, using `networkx.betweenness_centrality(G, normalized=True)`. This workload is meaningful because betweenness centrality is a standard graph-analysis primitive and NetworkX documents it as an implementation of Brandes’ shortest-path betweenness algorithm.

## Slow path and how it was found

The slow path is the unweighted Brandes implementation inside `betweenness_centrality`, specifically the repeated single-source shortest-path traversal and reverse dependency accumulation performed once per source node. In the baseline implementation, the helpers use dictionary-backed state and repeated graph-view lookups in tight Python loops, which makes this path expensive on graphs of the chosen benchmark size.

This path was identified by reading the baseline source code and inspecting the internal helper functions used by betweenness centrality. The benchmark confirmed that the workload is non-trivial on Colab CPU, with baseline runtime in the mid-20-second range for the selected graph and timing methodology.

## What changed

The optimization keeps the same Brandes algorithm for the selected benchmark case but reduces Python overhead substantially. The patch  precomputes adjacency lists once, then uses list-backed arrays for predecessors, path counts, distances, dependency scores, and final betweenness values instead of repeatedly updating dictionary-backed structures in the hottest loops.

This change matters because the benchmark graph uses consecutive integer node labels `0..n-1`, which allows direct index-based access with plain Python lists. That removes a large number of dictionary hash lookups and adjacency-view accesses from the inner traversal and accumulation loops while preserving the exact output for the benchmark workload.

## Why it is faster

The speedup comes from lowering per-iteration interpreter overhead. The baseline repeatedly performs dictionary operations and graph-view indirections inside the deepest loops, while the patch works mostly with local variables, prebuilt adjacency lists, and contiguous list-backed state.

In `tests.ipynb`, the baseline median time was 25.629 seconds and the candidate median time was 13.797 seconds on the same benchmark graph, for a measured speedup of about 1.858x, exact output match on the benchmark graph is also produced, with maximum absolute difference 0.0.

## Trade-offs

The main trade-off is generality. The optimized path is tailored to the benchmark case of an unweighted undirected graph whose nodes are consecutive integer labels, so it is not a universal drop-in replacement for every possible NetworkX graph shape or every betweenness-centrality mode such as weighted graphs, endpoint-inclusive mode, or sampled approximation mode.

There is also a code-complexity trade-off. The baseline NetworkX implementation is concise and general-purpose, while the patch introduces a more specialized helper that is harder to read and maintain because it exploits properties of the selected workload to reduce overhead.

Memory use is also somewhat different. Precomputing adjacency lists and maintaining list-backed working arrays increases upfront memory pressure relative to relying entirely on graph views, but this trade-off is acceptable for the chosen Colab CPU benchmark and helps reduce runtime.

## Correctness checks and measurement method

Correctness was checked in two ways. First, the existing NetworkX betweenness-centrality test file was run successfully on the baseline and candidate environments, with 41 tests passing in each case. Second, `tests.ipynb` computed both baseline and candidate outputs on the same benchmark graph and verified exact equality with maximum absolute difference 0.0 before reporting any speedup.

Measurement was done using the same Colab CPU configuration, the same graph input, 2 warmup runs, and 7 measured runs for each implementation. The reported statistic is the median runtime with IQR, which follows the task brief's emphasis on warmup, multiple runs, and reporting spread rather than relying on a single timing sample.

## What another week would improve

With more time, the next step would be to turn this benchmark-specific optimization into a cleaner integrated fast path inside the repository rather than a separate helper module. That would include broader support for relabeling arbitrary node IDs to dense integer indices, extending the optimization to more graph shapes, and validating behavior across more of the existing centrality test suite.

Another week would also be enough to profile the remaining hotspots more formally and test additional implementation strategies such as Cython or Numba, provided the build remained reproducible from a cold Colab start. The current submission prioritizes a simple, exact, and reproducible pure-Python improvement over a riskier compiled solution.

## Caveats

The exact wall-clock numbers vary across Colab sessions because CPU contention and notebook state can change from run to run, so the README reports the numbers from `tests.ipynb` as the source of truth. The important point is that both implementations were timed using the same methodology and the measured speedup remained substantial.

This submission intentionally does not claim a universal optimization for all NetworkX betweenness-centrality use cases. It claims an exact and reproducible speedup for the selected benchmark workload, and it documents that specialization explicitly (because the task brief values honest reasoning about limitations.)
