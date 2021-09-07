import random
from smile.common import *
from gabor_config_smile import *

from scipy.stats import truncnorm, expon
import numpy as np
from math import ceil
from itertools import combinations, combinations_with_replacement

def Diff(ls1,ls2): # difference between lists. used to find combinations needed.
    return (list(list(set(ls1)-set(ls2))+list(set(ls2)-set(ls1))))

def gaborpairs(con_hi = [0,.5,1], con_lo = [0,.5,1],
               simplern = 2, equalrn = 1,
               rn = 2, bn=2, window_size=20,sides=[0,1],
               simple_comb = [(1,0),]):
    
    # all combs:
    comb_all=list(combinations_with_replacement(con_hi+con_lo,2))
    # all combs within hi/lo list:
    comb_within=list(combinations_with_replacement(con_hi,2))+list(combinations_with_replacement(con_lo,2))
    # all unequal combs within hi/lo list:
    comb_unequal_within=list(combinations(con_hi,2))+list(combinations(con_lo,2))

    #all combs between hi & lo without equal combs:
    comb_between=Diff(comb_all,comb_within) 
    # all equal combs:
    comb_equal=Diff(comb_within,comb_unequal_within)

    stim=[]
    for one_block in range(bn):
        thisblock = comb_between*rn +simple_comb*simplern+comb_equal*equalrn
        random.shuffle(thisblock) 
    #     stim.append(thisblock)
        stim+=thisblock
    
    for pair in stim:
        if pair[0]<pair[1]:
            pair[0],pair[1]=pair[1],pair[0]
    
    blocksofgabors = []
    for pair in stim:
        this_trial = {'conhi':pair[0],
                    'conlo':pair[1],
                    }
        blocksofgabors.append(this_trial)
    return blocksofgabors


# if DEV_MODE:
#     loc_to_CR = {'left': ['F'],
#                  'right': ['J']}
# else:
#     loc_to_CR = {'left': [1],
#                  'right': [2]}