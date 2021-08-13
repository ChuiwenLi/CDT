# from smile.startup import InputSubject
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

from gabor_gen_smile import *
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
    loc_to_PV = Ref.object({'left': [5.0, 0.0],
                            'right': [0.0, 5.0],
                            'center': [True]})
    read_licker.start()
    write_reward.start()
    write_center.start()

@Subroutine
def BlankScrLickPunish(self, interval, penalty=2, **kwargs):
    self.not_done = True
    self.interval = interval
    self.time_left = interval
    self.passed_time = 0.0
    self.total_penalty = 0.0
    with Loop(conditional=self.not_done):
        with Parallel():
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
                tol_penalty_time=self.total_penalty,
                initdelay=interval,
                log_dict=kwargs,)
    

@Subroutine
def Trial(self, CTRST_L, CTRST_R, CR):#,right_wait,pulse_dur):
    self.ctrst_l=CTRST_L
    self.ctrst_r=CTRST_R 
    self.cr=CR
    self.pulse_dur=Func(truncnorm(a=pul_a,b=pul_b, loc=my_mean, scale=my_std).rvs).result
    # self.inidelay = Func(random.random).result
    self.right_wait = Func(truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs).result

    # Debug(pulse_duration=self.pulse_dur)
    
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
                                contrast = CTRST_L)#,color_one = [0,0,0,1], color_two = [1,1,1,1]) # left
            uw_g2 = UpdateWidget(g2, center_x=exp.screen.center_x + side_distance, alpha=1,
                                rotate=270, rotate_origin=[coord_x + side_distance,coord_y],
                                contrast = CTRST_R)#,color_one = [0,0,0,1], color_two = [1,1,1,1]) # right
        # wait until the change takes place
        Wait(until=uw_g.appear_time)
        with Parallel():
            g.slide(phase=phase_abs,duration=2*5)
            g2.slide(phase=-phase_abs,duration=2*5)
            # uw_g4.slide(phase=-24,duration=0.6)
        # try to get a response
        with UntilDone():
            if DEV_MODE:
                nic = KeyPress(keys=["F", "J"], correct_resp=CR,
                            #    duration=max_dur,
                            base_time=uw_g.appear_time['time'])
            else:
                nic = NIChangeDetector(task=read_licker, tracked_indices=[1, 2],
                                    threshold=thresh, correct_resp=CR,
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
            self.reward_time = reward_pulse.appear_time
        else:
            # determine the correct push vals
            Debug(rt=nic.rt, reward_dur=self.pulse_dur)
            self.pv = loc_to_PV[CR_to_loc[CR[0]]]
            reward_pulse = NIPulse(task=write_reward,
                                   vals=self.pv, dur=self.pulse_dur)
                                   
            Wait(until=reward_pulse.pulse_start_time)
            self.reward_time = reward_pulse.pulse_start_time

            # wait until we're done sending the pulse
            Wait(until=reward_pulse.pulse_end_time)

        # add a wait for the correct amount
        kw4delay = {'correct':nic.correct,
                    'rt_resp':nic.rt,
                    'trial_start':g.appear_time
                    }
        BlankScrLickPunish(interval=self.right_wait,**kw4delay)
        #Wait(right_wait)
    with Else():
        # they got it wrong
        if DEV_MODE:
            Label(text=u"\u2717", color='red', font_size=s(72),
                  duration=feedbacktime, font_name='DejaVuSans.ttf')

        # no reward
        self.reward_time = event_time(0,0)
  
        # add in extra wait
        self.wrongwait=Func(expon(scale=sc).pdf,x=nic.rt).result + up + self.right_wait
        Debug(wrongwait=self.wrongwait)
        kw4delay = {'correct':nic.correct,
                    'rt_resp':nic.rt,
                    'trial_start':g.appear_time
                    }
        BlankScrLickPunish(interval=self.wrongwait,**kw4delay)

    # log the trial info
    if DEV_MODE:
        # pull out the response
        self.resp = nic.pressed
        self.resp_time = nic.press_time
    else:
        self.resp = nic.changed_channels[0]
        self.resp_time = nic.change_time
           
    Log(name="trial_data",
        ctrst_l = self.ctrst_l,
        ctrst_r = self.ctrst_r,
        correctanswer=self.cr,
        resp=self.resp,
        resp_time=self.resp_time,
        rt=nic.rt,
        pulse_dur=self.pulse_dur,
        base_time=nic.base_time,
        correct=nic.correct,
        reward_time=self.reward_time,
        choice_start=uw_g.appear_time,
        trial_start=g.appear_time,
        disappear_time=uw_g.disappear_time,
        )
    

# set up the experiment
exp = Experiment(background_color=[0.5,0.5,0.5,1], name="CDT_exp_timeout", resolution=(1280,1024),
                #  fullscreen=False, resolution = (800,600), #"gray",
                 show_splash=False, debug=True)
Wait(.25)


# loop over some trials
# gabortrials = gabortrials_2sides(rn = num_repeats, bn = num_blocks, 
#                                 sides = [1,0],
#                                 contrast_distractor=ctrst_distractor,
#                                 contrast_target=contrast_target)

# gabortrials = gabortrials_origin(contrast_levels = contrast_level, 
#                                  rn = num_repeats, bn = num_blocks, 
#                                  eq_repeatnum = num_equal, simplern = num_simple)

# gabortrials = gabortrials_2sides(rn = num_repeats, bn = num_blocks,
#                                   contrast_distractor=ctrst_distractor,
#                                   contrast_target=contrast_target,
#                                   sides=sides)

gabortrials=gabortrials_alternate_2(con_hi = contrast_target, con_lo = ctrst_distractor,
                                    #contrast_levels = contrast_level, 
                                    #eq_repeatnum = num_equal, 
                                    simplern = num_simple, equalrn=num_equal,
                                    rn=num_repeats, bn=num_blocks, window_size=window_size,sides=sides,
                                    simple_comb=simple_comb,)


with Loop(gabortrials) as d:
    Trial(CTRST_L=d.current['CTRST_L'], CTRST_R= d.current['CTRST_R'], 
          CR=d.current['CR'], )
          #right_wait=d.current['right_wait'],pulse_dur=d.current['pulse_dur'] )


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
