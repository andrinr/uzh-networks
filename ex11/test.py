import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from simulation import Simulation

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.cm as cmx

def sample_ER(N, p):
    rd = np.random.rand(N,N)
    A = np.triu(rd < (p))
    np.fill_diagonal(A, 0)
    return A
    
def gen_com_graph(N, n_coms, p_high, p_low):
    N_pc = int(N / n_coms)
    A_struct = np.zeros((N,N))
    for i in range(n_coms):
        A_struct[i*N_pc:(i+1)*N_pc, i*N_pc:(i+1)*N_pc] = sample_ER(N_pc, p_high)
    A_random = sample_ER(N, p_low)
    A = A_struct + A_random
    
    return nx.from_numpy_matrix(A), A_struct, A_random
G, _, _ = gen_com_graph(100, 1, 0.16, 0.001)


nx.draw(G, with_labels=True)

sim = Simulation(G, 1.0, 0.1, 0.001, 0.1)\
    .init_walkers_uniform(5000)\
    .infect_walkers(0.01)\
    .run(10)

fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(9, 12))

jet = cm = plt.get_cmap('tab20c') 
cNorm  = colors.Normalize(vmin=0, vmax=sim.G.number_of_nodes())
scalarMap = cmx.ScalarMappable(norm=cNorm, cmap=jet)

ax1.plot(sim.timeline, np.sum(sim.infected_log, axis=1), label='infected')

ax1.set_title('All walkers start at node 10')
ax1.set_xlabel('Time')
ax1.set_ylabel('Fraction of walkers')

plt.show()
