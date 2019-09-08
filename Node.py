#!/usr/bin/python
# -*- coding: utf-8 -*-

# Node.py (c) Till Haenisch till.haenisch@dhbw-heidenheim.de
#

import os
from random import randrange,random,sample,uniform

# Difficulties and capabilities are highly nonlinear.
# User gives value from 1 to 6 where
# 1 means very low/very easy (e.g. everyone)
# 2 means low/easy (e.g. some skills required/some problems)
# 3 means middle (well, middle)
# 4 means high (e.g. expert level)
# 5 means very high/very difficult (e.g. highly motivated hacker/criminal)
# 6 means extremly high/extremly difficult (e.g. government agency level)

# translation to "probablility" values
Difficulties = []
Capabilities = []
#                0    1    2    3    4    5    6
Difficulties = [0.0, 0.1, 0.3, 0.5, 0.8, 0.9, 0.99]
Capabilities = [0.0, 0.1, 0.3, 0.5, 0.8, 0.9, 0.99]
#Difficulties = [1.0, 0.9, 0.7, 0.5, 0.2, 0.1, 0.01]
#Capabilities = [1.0, 0.9, 0.7, 0.5, 0.2, 0.1, 0.01]

# Track all nodes here, so we don't have to walk the walk if we just want to talk
all_nodes = []
def get_all_nodes():
    return all_nodes

def log(level, s):
    limit = 0
    if level <= limit:
        print(s)

def quote(s):
    return '"' + s + '"'



class Node:
    # Every node has at least the attributes name, type, difficulty and capability
    # In addition every node has a unique ID in the attribute ID which is used for
    # identification. The ID is a number starting with 0
    ID = 1
    def __init__(self, name, type='threat', frequency=1.0, capability=0, difficulty=0, children=[]):
        self.ID = 'NODE' + str(Node.ID)
        Node.ID += 1
        self.name = name
        self.capability = capability
        self.difficulty = difficulty
        self.frequency = frequency
        self.type = type
        self.children = children
        self.successfull = 0
        log(2, "created Node " + self.name)
        all_nodes.append(self)

    @staticmethod
    def alternatives(l):
        return [Node('or', type='group', children=l)]

    @staticmethod
    def composition(l):
        return [Node('and', type='group', children=l)]

    @staticmethod
    def sequence(l):
        return [Node('seq', type='group', children=l)]

    def __str__(self):
        return self.type + ' ' + self.name + ' ' + str(self.successfull)

    def to_csv(self):
        return self.type + ";" + self.name + ";" + str(self.successfull)

    def to_cli(self, s):
        print(s)

    def get_capability_prob(self):
        return Capabilities[self.capability]

    def get_prob(self):
        # threat nodes (and their children) have positive probabilities, measure nodes have negative ones
        sign = 1
        if self.type == "measure":
            sign = -1
        p = self.frequency * (1.0 - Capabilities[self.capability] * Difficulties[self.difficulty])
        log(2, "get_prob for " + self.name + " is: " + str(sign*p))
        return sign*p

    def is_leaf(self):
        # A leaf node has explicit values for difficulty and capability,
        # grouping nodes in a hierarchy have the default value 0
        # Leaf does not (!) exactly mean a leaf in the tree but the lowest node with a given type.
        # That might be (and often is !) a threat node with measure children ...
        # Our definition of a leaf is given above
        return (self.capability != 0) and (self.difficulty != 0)

    def evaluate_prob(self):
        # depth first tree traversal
        p = 1.0
        log(1, self.type + ' ' + self.name)

        if self.type == 'group':
            if self.name == 'or':
                p = 0.0
            else:
                p = 1.0
            children = self.children
            sign = 1
            # TODO check if all children have the same sign, they should, but if not this modeling error should be handled
            for child in children:
                if child.type == "measure":
                    # if one child is a measure, all children (well, the complete sub-hierary) are (well, should be) measures
                    sign = -1

                if self.name == 'or':
                    p = p + child.evaluate_prob()

                if self.name == 'and' or self.name == 'seq':
                    # sign information is lost during multiplication --> handle that later
                    p = p * child.evaluate_prob()

            if sign < 0:
                # clean up sign mess
                if p > 0:
                    p = -1 * p
                p = max(p, -1.0)
            else:
                p = min(p, 1.0)
        else:
            # either threat or measure
            children = self.children
            if len(children) > 1:
                # Multiple children of a "real" node are considered a logical OR --> modelling error ?
                for child in children:
                    p = p + child.evaluate_prob()
                p = min(p, 1.0) # Fix that we don't have real probabilities in OR
            elif len(children) == 1:
                p = children[0].evaluate_prob()

            if self.is_leaf():
                # Only leafs have (own) probabilities, for nodes in a hierarchy the prob. is the cumulated prob of the children only
                p = p*self.get_prob()
                log(2, "Leaf " + self.name + ", calculating local probability=" + str(self.get_prob()) + ", difficulty " + str(self.difficulty) + " capability " + str(self.capability))
                # If I am a threat and I have measure childs, this is the place, where the magic happens:
                # a measure reduces my probability of success. I cannot just ask my child for its type,
                # cause there are grouping nodes (or, and, seq), so we use the sign of the probability as
                # a discriminator for the type of hieryrchy below me. If it is negative, then I have measure childs
                # which will hinder me doing the fun stuff.
                if self.type == 'threat' and (p < 0):
                    # Basically my probability will be reduced by a measure, I will multiply my (local)
                    # probability by (1-<success probability of the measure>)
                    p_measure = p
                    p = self.get_prob() * (1+p) # p is negative, if measure ...
                    log(2, "Threat (p=" + str(self.get_prob()) + ") with measure children (p=" + str(-1*p_measure) + ")")

        log(1, self.name + ': ' + str(p))
        # Remember probability of node (to show in graphical output for debugging)
        self.prob = p
        return p

    def pick_alternative(self,alternatives):
        # first version:
        # very simple implementation, pick with uniform distribution
        # in reality, an attacker might pick the one, which is easiest (as far as he knows --> capability based decision)
        # number = len(alternatives)
        # return alternatives[randrange(number)]

        # a bit more complex: The probability for chosing an (or) alternative is weighted by the required capability
        # as a first approximation we chose the associated probabilities from the Capability -> Probability table defined above
        # What we do: 
        # We shuffle the alternatives to avoid dependance on the (artificial) sequence of definition.
        # Then we add the "probabilities" of the alternatives for normalization.
        # Then we generate a random number between 0.0 and the sum of probabilities and add up the "probabilities" till we reach this number
        # The corresponding alternative is the one we chose. 
        # This is basically a roulette wheel selection as used in genetic optimization, see for example
        # Adam Lipowski, Dorota Lipowska, Roulette-wheel selection via stochastic acceptance, arXiv:1109.3627
        # or D.E. Goldberg Genetic Algorithms in Search, Optimization, and Machine Learning (Addison-Wesley, Reading, Massachusetts, 1989).
  
        choices = sample(alternatives,len(alternatives))
        sum_probs = 0.0
        for c in choices:
            sum_probs += c.get_capability_prob()
        
        threshold = uniform(0.0,sum_probs)
        sum_probs = 0.0
        choice = len(choices) - 1
        for c in choices:
            sum_probs += c.get_capability_prob()
            if sum_probs >= threshold:
                choice = c
                break
        return choice


    def make_walk(self):
        # make one (random) walk through the tree and look, where we come out (and if we succeed)
        # Algorithm:
        # Walk down the tree till we are at the bottom (usually called leaf, but we have different leaf types ... threat and measure)
        # While going back, check, how things work. If a measure catches, the attack has failed, the measure succeeded (this is logged)
        # If the measure succeeded, the threats on the way back have failed as a consequence
        # If the measure hasn't succeeded (or we have no measure), we make random attempts with the threats on our way up.
        # If a threat fails, everything up to the next "or" on our way back has also failed.
        #
        # make_walk returns true, if the inspected (sub) trees attacks were successfull, false, if not
        # (means a successfull measure returns false) 
        log(2, 'visiting ' + self.type + ' ' + self.name)

        if self.type == 'group':
            if self.name == 'or':
                # pick one randomly
                where_to_go = [self.pick_alternative(self.children)]
            else:
                # We have to check all of them, if any one fails, the attack has failed (up to here. But that means, it has failed
                # in total, because we have reduced the "or"-subtrees to one by choosing randomly one of the alternatives.
                #where_to_go = self.children

                # Now we shuffle the threats at "and" groups and do in sequence only with "seq"
                if self.name == "seq":
                    where_to_go = self.children
                else:
                    where_to_go = sample(self.children,len(self.children))

            for w in where_to_go:
                if (w.make_walk() == False):
                    return False
            return True # redundant, catchall return True would take it, but in this way we keep things nicely local ;-)

        if self.is_leaf():
            if (self.type == "measure"):
                p = abs(self.get_prob())
                log(2,"in measure " + self.name + " " + str(p))
                # Check, if the measure catches the attack. If not, that doesn't mean, the attack is successfull,
                # but only, that we have to calculate the probability of success for this threat ...
                if random() < p:
                    # measure successfull
                    # IST DAS AUCH FÜR OR RICHTIG ???? DER ATTACKER KÖNNTE JA AUCH NOCH EINEN ANDEREN ZWEIG AUSPROBIEREN !!
                    log(1,"measure " + self.name + ' was successfull, attack stopped !')
                    self.successfull += 1
                    return False
            else:
                # We are a threat
                if (len(self.children) > 0):
                    # We have "measure" children ...
                    # Well, we shouldn't have more than one measure child .... HACK HACK
                    if (self.children[0].make_walk() == False):
                        return False
                # If we arrive here, it have the power to make bad things happen ... we ARE the force .... if we are lucky ....
                p = self.get_prob() # Achtung: Erst prüfen, ob attack erfolgreich, dann measure children auswerten !! Sonst sind die Trefferquoten nachher falsch !
                if random() > p:
                    # Threat not successfull
                    log(1,"threat " + self.name + ' has failed, attack stopped !')
                    self.successfull += 1                    
                    return False
        else:
            # Should have only one child ...
            # and at least one, is not leaf
            # So we consider only the first one HACK HACK --> Leafs mit mehreren Kindern als or remodeln
            return self.children[0].make_walk()
        return True


    def get_color(self, node_type):
        colors = {}
        colors['group'] = 'cornsilk1'
        colors['or'] = 'grey'
        colors['and'] = 'grey'
        colors['threat'] = 'red'
        colors['measure'] = 'greenyellow'
        return colors[node_type]


    def node_gv(self, s, with_prob):
        str_p = ''
        if with_prob:
            str_p = "|p = " + "{0:.3f}".format(abs(self.prob))
        print(self.ID + ' [shape = "record", fillcolor = "' \
            + self.get_color(self.type) + '", label = "{{' + self.name +str_p \
            + '}|{' + str(self.frequency) + '|' \
            + str(self.capability) + '|' + str(self.difficulty) \
            + '}}"]')

    def traversal_gv(self, to_node):
        log(2,self.ID)
        log(2,to_node.ID)
        out = self.ID + ' -> ' + to_node.ID
        print(out)

    def eval_dir(self):
        os.mkdir(self.name)
        os.chdir(self.name)
        f = open("info.txt", "w")
        f.write("Name=" + self.name + "\n")
        f.write("Type=" + self.type + "\n")
        f.write("Capability=" + str(self.capability) + "\n")
        f.write("Frequency=100\n")
        f.write("Difficulty=" + str(self.difficulty) + "\n")
        f.flush()
        f.close()
        for c in self.children:
            c.eval_dir()
        os.chdir("..")

  
    def evaluate(self, level, with_prob):
        log(2, "---------------evaluate " + self.name)
        # depth first tree traversal, apply fun to every node, count current level
        out = level * '-'
        level += 1
        out += self.name
        self.node_gv(out, with_prob)
        for child in self.children:
            self.traversal_gv(child)
            child.evaluate(level, with_prob)

    def to_gv(self, with_prob=False):
        header = \
            """
digraph G {
node [fontname = Verdana, fontsize = 12]
node [style = filled, shape = "box"]
node [fillcolor = "#EEEEEE"]
node [color = "#000000"]
edge [color = "#000000"]
edge [dir = "none"]
graph [rankdir = TB, size = "10, 13"]
"""
        print(header)
        self.evaluate(0, with_prob)
        print('}')

        
