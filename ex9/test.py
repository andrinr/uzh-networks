
G, _, _ = gen_com_graph(20, 1, 0.16, 0.001)

sim = Simulation(10000, G, 0.1, 200)
sim.run()

nx.draw(G, with_labels=True)

fig, ax1 = plt.subplots(nrows=1, ncols=1, figsize=(9, 4))

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

for i in range(0, sim.G.number_of_nodes(), 1):
    ma_window = 200
    ma = moving_average(sim.node_log[:,i], ma_window)
    ax1.plot(sim.timeline[ma_window-1:], ma, label=i)
    #ax1.plot(sim.timeline, sim.node_log, label=i)

ax1.legend(np.linspace(0, sim.G.number_of_nodes()-1, sim.G.number_of_nodes(), dtype=int))
plt.show()