from collections import deque

def _build_adj_list(G):
    n = len(G)
    adj = [[] for _ in range(n)]
    for v in G:
        adj[v] = list(G[v])
    return adj

def betweenness_centrality_fast(G, normalized=True):
    n = len(G)
    adj = _build_adj_list(G)
    bet = [0.0] * n

    for s in range(n):
        S = []
        P = [[] for _ in range(n)]
        sigma = [0.0] * n
        dist = [-1] * n

        sigma[s] = 1.0
        dist[s] = 0
        Q = deque([s])

        while Q:
            v = Q.popleft()
            S.append(v)
            dv = dist[v] + 1
            sigmav = sigma[v]
            for w in adj[v]:
                if dist[w] < 0:
                    dist[w] = dv
                    Q.append(w)
                if dist[w] == dv:
                    sigma[w] += sigmav
                    P[w].append(v)

        delta = [0.0] * n
        while S:
            w = S.pop()
            coeff = (1.0 + delta[w]) / sigma[w]
            for v in P[w]:
                delta[v] += sigma[v] * coeff
            if w != s:
                bet[w] += delta[w]

    if normalized and n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        for i in range(n):
            bet[i] *= scale

    return {i: bet[i] for i in range(n)}
