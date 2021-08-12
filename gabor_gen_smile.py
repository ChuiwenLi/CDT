# import numpy as np
import random
from smile.common import *
from gabor_config_smile import *

from scipy.stats import truncnorm
import numpy as np
from math import ceil
from itertools import combinations, combinations_with_replacement

"""Chuiwen's TS training"""

"""
We will be creating dictionaries with the following keys:
    contrast_L          (0,1)
    contrast_R          (0,1)
    contrast_C          (0,1)                 
    CR                  L or R
"""

if DEV_MODE:
    loc_to_CR = {'left': ['F'],
                 'right': ['J']}
else:
    loc_to_CR = {'left': [1],
                 'right': [2]}

def Diff(ls1,ls2): # difference between lists. used to find combinations needed.
    return (list(list(set(ls1)-set(ls2))+list(set(ls2)-set(ls1))))

def gabortrials_origin(contrast_levels = [0.2, 1], rn=3, bn = 3, eq_repeatnum = 1, simplern = 2):
    """tn must be an interger multiple of len(contrast_levels)^2. bn * tn = total trial number"""
    """tn: trial number; bn: block number"""
    # rn = int(tn/len(contrast_levels))

    blocksofgabors = []
    for one_block in range(bn):
        this_block = []
        for one_repeat in range(rn):
            for i in contrast_levels: # contrast_left
                for j in contrast_levels: # contrast_right
                    # contrast_C = i if i > j else j
                    if i < j:
                        CR = loc_to_CR['right']
                    elif i > j:
                        CR = loc_to_CR['left']

                    if i != j:
                    #     CR = 9 # do nothing
                    # else:
                        this_trial = {'CTRST_L':i,
                                      'CTRST_R':j,
                                      'CR':CR, 
                                      'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                                      'pulse_dur': random.uniform(0.05,0.4),}
                        this_block.append(this_trial)
        for re in range(eq_repeatnum):
            for eq in loc_to_CR:
                for ctrst in contrast_levels:
                    this_trial = {'CTRST_L':ctrst,
                                'CTRST_R':ctrst,
                                'CR':loc_to_CR[eq],
                                'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                                'pulse_dur': random.uniform(0.05,0.4),}
                    this_block.append(this_trial)
        for sr in range(simplern):
            for answer in loc_to_CR:
                for target in [1,]:
                    for distractor in [.1,]:
                        if answer == 'left':
                            ctrst_l=max(target,distractor)
                            ctrst_r=min(target,distractor)
                        else:
                            ctrst_l=min(target,distractor)
                            ctrst_r=max(target,distractor)
                        this_trial = {'CTRST_L':ctrst_l,
                                    'CTRST_R':ctrst_r,
                                    'CR':loc_to_CR[answer],
                                    'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                                    'pulse_dur': random.uniform(0.05,0.4),}
                        this_block.append(this_trial)
        random.shuffle(this_block)
        for k in this_block:
            blocksofgabors.append(k)
    return blocksofgabors


def gabortrials_2sides(contrast_target = [0.5, 1], 
                        contrast_distractor = [0.1,0.5],
                        sides=[0,1], # left or right
                        bn = 5, rn = 1):
    """tn must be an interger multiple of len(contrast_levels)^2. bn * tn = total trial number"""
    """bn: block number; rn: repeat number for unequal trials; eq_repeatnum: for equal trials"""
    repeatnum = rn

    blocksofgabors = []
    for one_block in range(bn):
        this_block = []
        for one_repeat in range(repeatnum):
            for i in contrast_target: 
                for j in contrast_distractor: 
                    for k in sides:
                        # contrast_C = i if i > j else j
                        if k == 0: #left
                            CR = loc_to_CR['left']
                            CTRST_L = max(i,j)
                            CTRST_R = min(i,j)
                        else:
                            CR = loc_to_CR['right']
                            CTRST_L = min(i,j)
                            CTRST_R = max(i,j)
                        # if i == j:
                        #     CR = 9 # do nothing
                        # else:
                        this_trial = {'CTRST_L':CTRST_L,
                                        'CTRST_R':CTRST_R,
                                        'CR':CR, 
                                        'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                                        'pulse_dur': random.uniform(0.05,0.4), }
                        this_block.append(this_trial)
        random.shuffle(this_block)
        for k in this_block:
            blocksofgabors.append(k)
    return blocksofgabors

def gabortrials_singleside(contrast_levels = [.2, .5, .8, 1], rn = 2, bn = 2):
    """tn must be an interger multiple of 2*len(contrast_levels). bn * tn = total trial number"""
    """tn: trial number; bn: block number"""
    repeatnum = rn

    blocksofgabors = []
    for one_block in range(bn):
        this_block = []
        for one_repeat in range(repeatnum):
            for i in range(1,3): # i = 1 or 2 # the gabor shows on the left or right.
                for j in contrast_levels: # the contrast of the gabor.
                    contrast_C = j
                    if i == 1: # left
                        CR = loc_to_CR['left']
                        left = j
                        right = 0
                    else: # right, i == 2
                        CR = loc_to_CR['right']
                        left=0
                        right = j
                    this_trial = {'CTRST_L':left,
                                    'CTRST_R':right,
                                    'CTRST_C': contrast_C,
                                    'CR':CR, }
                    this_block.append(this_trial)
        random.shuffle(this_block)
        for k in this_block:
            blocksofgabors.append(k)
    return blocksofgabors


def gabortrials_alternate(contrast_levels = [.1,.2,.3,.4], eq_repeatnum = 0, simplern = 0,
                            rn = 2, bn=2, window_size=2,sides=[0,1],simple_comb = [(1,.1),]):
    """tn must be an interger multiple of len(contrast_levels)^2. bn * tn = total trial number"""
    """bn: block number; rn: repeat number for unequal trials; eq_repeatnum: for equal trials"""
    """simple condition = 1 vs 0.1"""
    # generate all combinations:
    comb_all=list(combinations_with_replacement(contrast_levels,2))
    comb_no_equal=list(combinations(contrast_levels,2))
    def Diff(ls1,ls2):
        return (list(list(set(ls1)-set(ls2))+list(set(ls2)-set(ls1))))
    comb_equal =Diff(comb_all,comb_no_equal)
    # simple_comb=[(1,0.1),]

    # for one_block in range(bn):
    stims = (comb_no_equal*rn + comb_equal*eq_repeatnum +simple_comb*simplern ) * bn
    random.shuffle(stims) 

    cr=[]
    tn=len(stims)
   # window_size=4 # consecutive repeat number < window_size
    for i in [(41)]*(tn//41)+[(tn%41)]:
        #generate a 0/1 list
        cr_list=[]
        for x in range(int(ceil(i/len(sides)))):
            for y in sides:
                cr_list.append(y)
        #randomize the list
        random.shuffle(cr_list)
        #test if the list has consecutive repeats (consecutive number>window_size)
        convolve_result = np.convolve(cr_list, np.ones((window_size,)),mode='valid')
        while any((x==window_size)|(x==0) for x in convolve_result):
            random.shuffle(cr_list)
            convolve_result = np.convolve(cr_list, np.ones((window_size,)),mode='valid')
        for ele in cr_list:
            cr.append(ele)
    
    blocksofgabors = []      
    for idx in range(tn):
        # cr[idx]
        if cr[idx] == 0: #left
            CR = loc_to_CR['left']
            CTRST_L = max(stims[idx][0],stims[idx][1])
            CTRST_R = min(stims[idx][0],stims[idx][1])
        else:
            CR = loc_to_CR['right']
            CTRST_L = min(stims[idx][0],stims[idx][1])
            CTRST_R = max(stims[idx][0],stims[idx][1])
        this_trial = {'CTRST_L':CTRST_L,
                    'CTRST_R':CTRST_R,
                    'CR':CR, 
                    # 'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                    # 'pulse_dur': truncnorm(a=pul_a,b=pul_b, loc=my_mean, scale=my_std).rvs(1)[0],
                    }
        blocksofgabors.append(this_trial)

    return blocksofgabors

# use hi/lo list separately to control experiment combinations
def gabortrials_alternate_2(con_hi = [1,0.975,0.95], con_lo = [0.1,0.125,0.15],
                            simplern = 0, equalrn = 0,
                            rn = 2, bn=2, window_size=20,sides=[0,1],
                            simple_comb = [(1,.1),]):
    """tn must be an interger multiple of len(contrast_levels)^2. bn * tn = total trial number"""
    """bn: block number; rn: repeat number for unequal trials; eq_repeatnum: for equal trials"""
    """simple condition = 1 vs 0.1"""
    
    # all combs:
    comb_all=list(combinations_with_replacement(con_hi+con_lo,2))
    # all combs within hi/lo list:
    comb_within=list(combinations_with_replacement(con_hi,2))+list(combinations_with_replacement(con_lo,2))
    # all unequal combs within hi/lo list:
    comb_unequal_within=list(combinations(con_hi,2))+list(combinations(con_lo,2))
    
    #all combs between hi & lo without equal combs:
    comb_between =Diff(comb_all,comb_within) 
    # all equal combs:
    comb_equal=Diff(comb_within,comb_unequal_within)

    # for one_block in range(bn):
    stims = (comb_between*rn +simple_comb*simplern+comb_equal*equalrn) * bn
    random.shuffle(stims) 

    cr=[]
    tn=len(stims)
   # window_size=4 # consecutive repeat number < window_size
    for i in [(41)]*(tn//41)+[(tn%41)]:
        #generate a 0/1 list
        cr_list=[]
        for x in range(int(ceil(i/len(sides)))):
            for y in sides:
                cr_list.append(y)
        #randomize the list
        random.shuffle(cr_list)
        #test if the list has consecutive repeats (consecutive number>window_size)
        convolve_result = np.convolve(cr_list, np.ones((window_size,)),mode='valid')
        while any((x==window_size)|(x==0) for x in convolve_result):
            random.shuffle(cr_list)
            convolve_result = np.convolve(cr_list, np.ones((window_size,)),mode='valid')
        for ele in cr_list:
            cr.append(ele)
    
    blocksofgabors = []      
    for idx in range(tn):
        # cr[idx]
        if cr[idx] == 0: #left
            CR = loc_to_CR['left']
            CTRST_L = max(stims[idx][0],stims[idx][1])
            CTRST_R = min(stims[idx][0],stims[idx][1])
        else:
            CR = loc_to_CR['right']
            CTRST_L = min(stims[idx][0],stims[idx][1])
            CTRST_R = max(stims[idx][0],stims[idx][1])
        this_trial = {'CTRST_L':CTRST_L,
                    'CTRST_R':CTRST_R,
                    'CR':CR, 
                    # 'right_wait':truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0],
                    # 'pulse_dur': truncnorm(a=pul_a,b=pul_b, loc=my_mean, scale=my_std).rvs(1)[0],
                    }
        blocksofgabors.append(this_trial)

    return blocksofgabors


# test=gabortrials_origin(contrast_levels = [.1,.5,1], 
#                     rn = 1, bn = 1, 
#                     eq_repeatnum = 0)
# eq=0
# noteq = 0
# for one in test:
#     if one['CTRST_L'] == one ['CTRST_R']:
#         eq+=1
#     else:
#         noteq+=1

# print('eq:',eq, 'noeq:', noteq)


