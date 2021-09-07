# from smile.startup import InputSubject
# from threading import current_thread
from smile.niusb_interface import *

# from smile.common import *
from common_CW import *
from smile.video import *
from smile.experiment import Experiment
from smile.state import UntilDone, Meanwhile, Wait, Loop, Debug, Subroutine

from smile.keyboard import KeyPress
from smile.scale import scale as s
from smile.clock import clock

import random

from gabor_gen_smile_bias_correction import *
from gabor_config_smile import *

"""Chuiwen's experimental version for tree shrews"""
"""CDT: contrast discrimination task"""

# set up nidaq
if not DEV_MODE:
    # NIDAQMX task inits
    read_licker = Task("ReadFromAI") # SMILE DAQmx task 
    read_licker.ai_channels.add_ai_voltage_chan('Dev1/ai0:2',
                                                "licker",
                                                min_val=0.0,
                                                max_val=5.0,)
    write_reward = Task("WriteToAO")
    write_reward.ao_channels.add_ao_voltage_chan('Dev1/ao0:1',
                                                 "rewards",
                                                 min_val=0.0,
                                                 max_val=5.0)
    write_center = Task("WriteToDO")
    write_center.do_channels.add_do_chan('Dev1/port0/line0',
                                         line_grouping=nidaqmx.constants.LineGrouping.CHAN_PER_LINE)

    # response mappings (need to be refs to delay evaluation below)
    CR_to_loc = Ref.object({0: 'center',
                            1: 'left',
                            2: 'right'})
    loc_to_PV = Ref.object({1: [5.0, 0.0], #left
                            2: [0.0, 5.0], #right
                            0: [True]}) #center
    read_licker.start()
    write_reward.start()
    write_center.start()

@Subroutine
def BlankScrLickPunish(self, interval, rect_threshold,penalty=2,  **kwargs):
    self.not_done = True
    self.interval = interval
    self.time_left = interval
    self.passed_time = 0.0
    self.total_penalty = 0.0
    with Loop(conditional=self.not_done):
        with If(interval>rect_threshold):
            with Loop():
                rect = Rectangle(color="red", width=400, height=240,duration=0.05,
                                bottom=exp.screen.bottom+100, blocking=True)
                Wait(until=rect.disappear_time)
                ResetClock(rect.disappear_time['time'])
                Wait(.03)
                  
        with UntilDone():
        # with Parallel():
            if DEV_MODE:
                delaylick = KeyPress(keys=["SPACEBAR"], correct_resp=["SPACEBAR"],
                                     duration=self.time_left)
                               
            else:
                delaylick = NIChangeDetector(task=read_licker,
                                             tracked_indices=[0],
                                             correct_resp=[0],
                                             threshold=thresh,
                                             duration=self.time_left)
            
        with If(delaylick.correct):
            # keep track of passed time
            self.passed_time += delaylick.rt
            # update the total delay interval
            self.interval = Func(max,self.passed_time+penalty ,self.interval).result
            # calculate how much delay is left
            self.time_left = self.interval - self.passed_time
            Debug(time_left=self.time_left)
            with If(self.time_left <= 0.0):
                self.not_done = False
            if DEV_MODE:
                self.del_lick_time = delaylick.press_time
            else:
                self.del_lick_time = delaylick.change_time
            Log(name="penalty_data",
                rel_t=delaylick.rt,
                base_t=delaylick.base_time,
                abs_t=self.del_lick_time,
                log_dict=kwargs,)
        with Else():
            self.total_penalty = self.interval - interval
            Debug(total_penalty=self.total_penalty)
            self.not_done = False
            Log(name="penalty_data",
                tol_penalty=self.total_penalty,
                init_delay=interval,
                tol_delay=self.interval,
                log_dict=kwargs,)
    

# @Subroutine
# def Trial(self, conhi, conlo, loc2cr, rect_thresh, counter, lprob):#,right_wait,pulse_dur):
# set up the experiment
exp = Experiment(background_color=[0.5,0.5,0.5,1], name="CDT_exp_timeout", resolution=(1280,1024),
                #  fullscreen=False, resolution = (800,600), #"gray",
                 show_splash=False, debug=True)
Wait(.25)


gabortrials=gaborpairs(con_hi = contrast_target, con_lo = ctrst_distractor,
                        simplern = num_simple, equalrn=num_equal,
                        rn=num_repeats, bn=num_blocks, window_size=window_size,sides=sides,
                        simple_comb=simple_comb,)

if DEV_MODE:
    loc_to_CR = Ref.object({1: ['F'],
                            2: ['J']})
else:
    loc_to_CR = Ref.object({1: [1],
                            2: [2]})

exp.counter=1
exp.lprob=.5
exp.resplist=[]
with Loop(gabortrials) as d:
    conhi=d.current['conhi']
    conlo=d.current['conlo']
    loc2cr=loc_to_CR
    
    exp.pulse_dur=Func(truncnorm(a=pul_a,b=pul_b, loc=my_mean, scale=my_std).rvs).result
    exp.right_wait = Func(truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs).result

    # Debug(counter=self.counter)
    
    # if self.counter>10:
    CR=Func(np.random.choice,a=(1,2),p=(exp.lprob,1-exp.lprob)).result
    with If (CR ==1):
        exp.conl=conhi
        exp.conr=conlo
        # self.crside='left'
    with Elif (CR==2):
        exp.conl=conlo
        exp.conr=conhi
        # self.crside='right'
    exp.cr=loc2cr[CR]
    
    # Put up gabor in the middle and wait for trial initiation
    # center stim coord
    coord_x=exp.screen.center_x
    coord_y=exp.screen.bottom+(gabor_size/2)+50
    rotate_origin = [coord_x,coord_y]
    with Parallel():
        # LEFT GABOR
        g = CWGrating(width=gabor_size, height=gabor_size, envelope='g',alpha=.5,#std_dev=50,
            frequency=frequency, bottom=exp.screen.bottom+50, center_x=exp.screen.center_x,
            contrast = 1, rotate=0, rotate_origin = rotate_origin, color_one = [0,0,0,0.1], color_two = [1,1,1,.1])
        # RIGHT GABOR
        g2 = CWGrating(width=gabor_size, height=gabor_size, envelope='g',alpha=.5, #std_dev=50,
            frequency=frequency, bottom=exp.screen.bottom+50, center_x=exp.screen.center_x,
            contrast = 1, rotate=90, rotate_origin = rotate_origin,color_one = [0,0,0,0.1], color_two = [1,1,1,.1])

    with UntilDone():
        # wait for the dots to show up
        Wait(until=g.appear_time)

        # wait infintely for the center licker to be activated
        if DEV_MODE:
            ini = KeyPress(keys=["SPACEBAR"],
                           base_time=g.appear_time['time'])
        else:
            ini = NIChangeDetector(task=read_licker, tracked_indices=[0],
                                   threshold=thresh)      
            centerreward=NIPulse(task=write_center, dur=cport_dur, vals=[True])
            Wait(until=centerreward.pulse_start_time)
                # wait until we're done sending the pulse
            Wait(until=centerreward.pulse_end_time)

        # the center licker port was activated
        # update the gabor to go to one side
        # Wait(self.inidelay)
        with Parallel():
            uw_g = UpdateWidget(g, center_x=exp.screen.center_x - side_distance, alpha=1,
                                rotate=90,rotate_origin=[coord_x - side_distance,coord_y], 
                                contrast = exp.conl)#,color_one = [0,0,0,1], color_two = [1,1,1,1]) # left
            uw_g2 = UpdateWidget(g2, center_x=exp.screen.center_x + side_distance, alpha=1,
                                rotate=270, rotate_origin=[coord_x + side_distance,coord_y],
                                contrast = exp.conr)#,color_one = [0,0,0,1], color_two = [1,1,1,1]) # right
        # wait until the change takes place
        Wait(until=uw_g.appear_time)
        with Parallel():
            g.slide(phase=phase_abs,duration=2*5)
            g2.slide(phase=-phase_abs,duration=2*5)
            # uw_g4.slide(phase=-24,duration=0.6)
        # try to get a response
        with UntilDone():
            if DEV_MODE:
                nic = KeyPress(keys=["F", "J"], correct_resp=exp.cr,
                            #    duration=max_dur,
                            base_time=uw_g.appear_time['time'])
            else:
                nic = NIChangeDetector(task=read_licker, tracked_indices=[1, 2],
                                    threshold=thresh, correct_resp=exp.cr,
                                    #    duration=max_dur,
                                    base_time=uw_g.appear_time['time'])
        # Debug(active=nic.changed_channels, values=nic.values, time=nic.change_time,
        #     rt=nic.rt, correct=nic.correct)

    with If(nic.correct & (nic.rt>MIN_RT)):
        # They got it right!
        if DEV_MODE:
            reward_pulse = Label(text=u"\u2713", color='green', font_size=s(72),
                                 duration=feedbacktime, font_name='DejaVuSans.ttf')
            Wait(until=reward_pulse.appear_time)
            exp.reward_time = reward_pulse.appear_time
        else:
            # determine the correct push vals
            Debug(rt=nic.rt, reward_dur=exp.pulse_dur)
            exp.pv = loc_to_PV[CR]
            reward_pulse = NIPulse(task=write_reward,
                                   vals=exp.pv, dur=exp.pulse_dur)
                                   
            Wait(until=reward_pulse.pulse_start_time)
            exp.reward_time = reward_pulse.pulse_start_time

            # wait until we're done sending the pulse
            Wait(until=reward_pulse.pulse_end_time)

        # add a wait for the correct amount
        kw4delay = {'correct':nic.correct,
                    'rt_resp':nic.rt,
                    'trial_start':g.appear_time
                    }
        BlankScrLickPunish(interval=exp.right_wait,rect_threshold=rect_thresh, **kw4delay)
        #Wait(right_wait)
    with Else():
        # they got it wrong
        if DEV_MODE:
            Label(text=u"\u2717", color='red', font_size=s(72),
                  duration=feedbacktime, font_name='DejaVuSans.ttf')

        # no reward
        exp.reward_time = event_time(0,0)
  
        # add in extra wait
        exp.wrongwait=Func(expon(scale=sc).pdf,x=nic.rt).result + up + exp.right_wait
        Debug(wrongwait=exp.wrongwait)
        kw4delay = {'correct':nic.correct,
                    'rt_resp':nic.rt,
                    'trial_start':g.appear_time
                    }
        BlankScrLickPunish(interval=exp.wrongwait,rect_threshold=rect_thresh,**kw4delay)

    # log the trial info
    if DEV_MODE:
        # pull out the response
        with If (nic.pressed == 'F'):
            exp.resp=1
        with Else():
            exp.resp=2
        exp.resp_time = nic.press_time
    else:
        exp.resp = nic.changed_channels[0]
        exp.resp_time = nic.change_time
    Debug(cr=exp.cr)
    Log(name="trial_data",
        ctrst_l = exp.conl,
        ctrst_r = exp.conr,
        correctanswer=exp.cr[0],
        resp=exp.resp,
        resp_time=exp.resp_time,
        rt=nic.rt,
        pulse_dur=exp.pulse_dur,
        base_time=nic.base_time,
        correct=nic.correct,
        reward_time=exp.reward_time,
        choice_start=uw_g.appear_time,
        trial_start=g.appear_time,
        disappear_time=uw_g.disappear_time,
        )
    with If (exp.counter<=10):
        with If (nic.correct):
            exp.resplist+=[1.5]
        with Else():
            exp.resplist+=[exp.resp]
    with Else():
        with If (nic.correct):
            exp.resplist=exp.resplist[1:]+[1.5]
        with Else():
            exp.resplist=exp.resplist[1:]+[exp.resp]
        resplist=exp.resplist
        Debug(respls=resplist)
        exp.lprob=Func(np.mean,resplist).result-1
        Debug(leftprob=exp.lprob)

    exp.counter+=1
    



if __name__ == '__main__':
    exp.run()
    # exp.run(trace=False)
    if DEV_MODE == False:
        read_licker.stop()
        write_reward.stop()
        write_center.stop()
        read_licker.close()
        write_reward.close()
        write_center.close()
