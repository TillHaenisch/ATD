
# control.py
#
# Driver program for Attack Tree Simulation
# reads model from defmodel.py in case no arguments are present
# usage python control.py <model> <mode> [runs]
# model is the name of the model file, mode is {print|prob|convert|run}
# if mode == run then the optional parameter runs is the number of runs to do, default is 10000
# (c) Till Haenisch, till.haenisch@dhbw-heidenheim.de


import sys
import os

make_graph = False


# convert to directory structure
#tree.eval_dir()


if (len(sys.argv) != 2):
    print("usage: python control.py <model>")
    exit(0)
else:
    filename = sys.argv[1]
    exec(compile(source=open(filename).read(), filename=filename, mode='exec'))
    if make_graph:
        # Compute static probabilities
        tree.evaluate_prob()

        # show tree with probabilities in GraphViz dot format
        tree.to_gv(True)
    else:
        # we have to do it often .... to get meaningful results
        runs = 10000
        successful = 0
        for run in range(runs):
            if tree.make_walk():
                successful += 1

        important_nodes = sorted(get_all_nodes(),key=lambda x: x.successfull)
        for n in important_nodes:
            print(n.to_csv())

        print("Percentage of successfull attacks: " + str(100.0*successful/runs))
    
