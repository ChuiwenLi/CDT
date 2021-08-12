DEV_MODE = True
# DEV_MODE = False
# fullscr = True
import numpy as np

# subject = 'Human' # do scr 1 gamma correction; make scr1 the main screen; turn the light off
subject = 'TS'

if subject == 'TS':
    # TSID = 'Lebron'
    # TSID = 'Nellie'
    TSID = 'Nellie_demo'
    # TSID = 'Kobe'
    # TSID = 'TS123'
    # TSID = 'TS125'
    phase_abs = 24*5 # define the phase number the side gabors move within 2 s. 0 means static gabors. bigger number means faster movement. 
    window_size=4

    sides = [0,1] # 0=left, 1=right

    if TSID == 'Lebron':
        """Lebron 087""" # threshold: 0.2 < con_diff < 0.3 ?
        c1,c2,c3,c4,c5,c6=np.arange(0,1,1/5.5)+.08
        c1,c2,c3,c4,c5,c6 = [round(float(num), 4) for num in [c1,c2,c3,c4,c5,c6]]
        contrast_target = [c1,c2,c3,c4,c5,c6] 
        ctrst_distractor = [c1,c2,c3,c4,c5,c6]
        num_repeats = 2
        num_blocks = 2
        num_simple = 4  # num_simple added into every block
        num_equal = 1

    elif TSID == 'Nellie':
        """Nellie 101""" # threshold: 0.1 < con_diff < 0.2
        c1,c2,c3,c4,c5,c6=np.arange(0,1,1/6)+.1
        c1,c2,c3,c4,c5,c6 = [round(float(num), 4) 
                                for num in [c1,c2,c3,c4,c5,c6]]
        contrast_target = [c1,c2,c3,c4,c5,c6] 
        ctrst_distractor = [c1,c2,c3,c4,c5,c6]
        num_repeats = 2
        num_blocks = 1
        num_simple = 4  # num_simple added into every block
        num_equal = 1
    
    elif TSID == 'Nellie_demo':
        """Nellie 101""" # threshold: 0.1 < con_diff < 0.2
        c1,c2,c3 = np.arange(0,1,1/3)+.3
        c1,c2,c3 = [round(float(num), 4) 
                                for num in [c1,c2,c3]]
        contrast_target = [c1,c2,c3] 
        ctrst_distractor = [c1,c2,c3]
        num_repeats = 2
        num_blocks = 1
        num_simple = 4  # num_simple added into every block
        num_equal = 0

    elif TSID == 'Kobe':
        """Kobe 085""" # threshold: 0.1 < con_diff < 0.2
        contrast_target = [round(float(num),4) 
                            for num in (np.arange(0,1,1/6)+0.1)]
        ctrst_distractor = contrast_target
        num_repeats = 2
        num_blocks = 1
        num_simple = 4  # num_simple added into every block
        num_equal = 1

    elif TSID == 'TS123':
        """123"""
        # window_size=3
        contrast_target = [round(float(num),4) 
                            for num in (np.arange(0,1,1/6)+0.08)]
        ctrst_distractor = contrast_target
        num_repeats = 2
        num_blocks = 2
        num_simple = 3  # num_simple added into every block
        num_equal = 1

    elif TSID == 'TS125':
        """125"""
        # window_size = 3
        contrast_target = [round(float(num),4) 
                        for num in (np.arange(0,1,1/6)+0.1)]
        ctrst_distractor = contrast_target
        num_repeats = 2
        num_blocks = 2
        num_simple = 3  # num_simple added into every block
        num_equal = 1
    
    simple_comb=[(max(contrast_target),min(ctrst_distractor)),]

elif subject == 'Human':
    DEV_MODE = True
    """contrasts. log_step = 0.04, for human """
    c1 = 0.5011872336272722
    c2 = 0.5495408738576245
    c3 = 0.6025595860743578
    c4 = 0.660693448007596
    c5 = 0.72443596007499
    c6 = 0.7943282347242815

    contrast_level = [c6,c5,c4,c3,c2,c1]
    sides = [0,1]
    # 
    num_repeats = 3
    num_blocks = 2 # 2 * 15 times; or 5 * 6 times
    num_simple = 3
    num_equal = 1
    simple_comb=[(.9,.1),]

"""gabor setup"""
gabor_size =256#264
frequency = 8#8
side_distance = 200

"""response info"""
max_dur = 5
thresh = 3
wrong_wait = 3 #4 # important to slow down the rhythm by using long timeout.
max_timeout = 8 #8
max_ITI = 1.5

MIN_RT = 0.05

# pulse_dur = 0.22 # randomized in experiment
cport_dur = 0#0.004 #.004
interval = 0.9 # for delay lick detection interval

"""for keyboard resp"""
feedbacktime = 0.1

"""for ITI"""
lower,upper=.5,.7
mu, sigma = .6,1
# ITI=truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs(1)[0]

"""for pulse dur"""
myclip_a=0.2
myclip_b=0.4
my_mean=0.1
my_std=0.06
pul_a, pul_b= (myclip_a-my_mean)/my_std, (myclip_b-my_mean)/my_std

"""for exponential timeout"""
sc=0.1 # scale
up=3.7 # timeout baseline
