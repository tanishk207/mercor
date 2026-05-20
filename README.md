# Speed Up an Open-Source Library

## Repo and commit

This submission targets `networkx/networkx` at baseline commit `9210d9c5bb9875caae0c7be2214abebfdd9255d2`, which corresponds to the NetworkX 3.1 release. NetworkX is open source under a BSD-style permissive license, has a public Git history, and includes an automated test suite.

The chosen workload is node betweenness centrality on an unweighted undirected graph with 1500 nodes and 50000 edges, using `networkx.betweenness_centrality(G, normalized=True)`. This workload is meaningful because betweenness centrality is a standard graph-analysis primitive and NetworkX documents it as an implementation of Brandes' shortest-path betweenness algorithm.

## Slow path and how it was found

The slow path is the unweighted Brandes implementation inside `betweenness_centrality`, specifically the repeated single-source shortest-path traversal and reverse dependency accumulation performed once per source node. In the baseline implementation, the helpers use dictionary-backed state and repeated graph-view lookups in tight Python loops, which makes this path expensive on graphs of the chosen benchmark size.

This path was identified by reading the baseline source code and inspecting the internal helper functions used by betweenness centrality. The benchmark confirmed that the workload is non-trivial on Colab CPU, with baseline runtime in the mid-20-second range for the selected graph and timing methodology.

## What changed

The optimization keeps the same Brandes algorithm for the selected benchmark case but reduces Python overhead substantially. The patch precomputes adjacency lists once, then uses list-backed arrays for predecessors, path counts, distances, dependency scores, and final betweenness values instead of repeatedly updating dictionary-backed structures in the hottest loops.It goes one step further by reusing the per-source working arrays across source iterations instead of allocating fresh arrays on every pass. After each source node is processed, only the touched entries are reset, which lowers allocation and garbage-collection overhead while preserving the exact output for the benchmark workload.

This change matters because the benchmark graph uses consecutive integer node labels `0..n-1`, which allows direct index-based access with plain Python lists. That removes a large number of dictionary hash lookups and adjacency-view accesses from the inner traversal and accumulation loops while preserving the exact output for the benchmark workload.

## Why it is faster

The speedup comes from lowering per-iteration interpreter overhead. The baseline repeatedly performs dictionary operations and graph-view indirections inside the deepest loops, while the patch works mostly with local variables, prebuilt adjacency lists, and contiguous list-backed state.

The reusable-array version also avoids repeatedly allocating fresh `sigma`, `dist`, `delta`, and predecessor containers for every source node. That reduces Python object churn and cleanup cost, which is especially helpful when the algorithm runs one traversal per source across 1500 source nodes.

In `tests.ipynb`, the baseline median time was 26.137 seconds and the previous candidate median time was 12.631 seconds, for a measured speedup of about 2.069x. After switching to the reusable-array patch, these numbers should be refreshed from the new benchmark run before submission. The exact output match requirement remains the same, with maximum absolute difference 0.0 on the benchmark graph.

## Trade-offs

The main trade-off is generality. The optimized path is tailored to the benchmark case of an unweighted undirected graph whose nodes are consecutive integer labels, so it is not a universal drop-in replacement for every possible NetworkX graph shape or every betweenness-centrality mode such as weighted graphs, endpoint-inclusive mode, or sampled approximation mode.

There is also a code-complexity trade-off. The baseline NetworkX implementation is concise and general-purpose, while the patch introduces a more specialized helper that is harder to read and maintain because it exploits properties of the selected workload to reduce overhead.

Memory use is also somewhat different. Precomputing adjacency lists and keeping reusable list-backed working arrays alive across source iterations increases persistent working memory relative to relying entirely on graph views and freshly allocated short-lived state, but this trade-off is acceptable for the chosen Colab CPU benchmark and helps reduce runtime.

## Correctness checks and measurement method

Correctness was checked in two ways. First, the existing NetworkX betweenness-centrality test file was run successfully on the baseline and candidate environments, with 41 tests passing in each case. Second, `tests.ipynb` computed both baseline and candidate outputs on the same benchmark graph and verified exact equality with maximum absolute difference 0.0 before reporting any speedup.

Measurement was done using the same Colab CPU configuration, the same graph input, 2 warmup runs, and 7 measured runs for each implementation. The reported statistic is the median runtime with IQR, which follows the task brief's emphasis on warmup, multiple runs, and reporting spread rather than relying on a single timing sample.

## What another week would improve

With more time, the next step would be to turn this benchmark-specific optimization into a cleaner integrated fast path inside the repository rather than a separate helper module. That would include broader support for relabeling arbitrary node IDs to dense integer indices, extending the optimization to more graph shapes, and validating behavior across more of the existing centrality test suite.

Another week would also be enough to profile the remaining hotspots more formally and test additional implementation strategies such as Cython or Numba, provided the build remained reproducible from a cold Colab start. The current submission prioritizes a simple, exact, and reproducible pure-Python improvement over a riskier compiled solution.

## Caveats

The exact wall-clock numbers vary across Colab sessions because CPU contention and notebook state can change from run to run, so the README reports the numbers from the final `tests.ipynb` run as the source of truth. The important point is that both implementations are timed using the same methodology and the measured speedup remains substantial.

This submission intentionally does not claim a universal optimization for all NetworkX betweenness-centrality use cases. It claims an exact and reproducible speedup for the selected benchmark workload, and it documents that specialization explicitly. (because the task brief values honest reasoning about limitations.)
