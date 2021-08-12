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
"""gabor match task"""

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
def BlankScrLickPunish(self, interval, max_penalty, penalty, lick_pause=0.8):
    """4s timeout"""
    self.not_done = True
    self.interval = interval
    self.total_penalty = 0.0
    with Loop(conditional=self.not_done):
        with Parallel():
            if DEV_MODE:
                delaylick = KeyPress(keys=["SPACEBAR"], correct_resp=["SPACEBAR"],
                                     duration=self.interval)
            else:
                delaylick = NIChangeDetector(task=read_licker,
                                             tracked_indices=[0],
                                             correct_resp=[0],
                                             threshold=thresh,
                                             duration=self.interval)
        with If(delaylick.correct):
            # calculate how much is left
            self.interval = self.interval - delaylick.rt

            # add penalty if we haven't maxed out
            with If(self.total_penalty + penalty < max_penalty):
                self.cur_penalty = penalty
            with Else():
                self.cur_penalty = max_penalty - self.total_penalty
            self.total_penalty = self.total_penalty + self.cur_penalty
            self.interval = self.interval + self.cur_penalty - lick_pause
            # Debug(interval = self.interval, penalty = self.total_penalty)
            with If(self.interval <= 0.0):
                self.not_done = False
            with Else():
                Wait(lick_pause)
        with Else():
            self.not_done = False


@Subroutine
def Trial(self):#,right_wait,pulse_dur):
    self.pulse_dur=Func(truncnorm(a=pul_a,b=pul_b, loc=my_mean, scale=my_std).rvs).result
    # self.right_wait = Func(truncnorm((lower-mu)/sigma,(upper-mu)/sigma, loc=mu, scale=sigma).rvs).result

    coord_x=exp.screen.center_x
    coord_y=exp.screen.bottom+(gabor_size/2)+50
    rotate_origin = [coord_x,coord_y]
    with Parallel():
        # LEFT GABOR
        g = CWGrating(width=gabor_size, height=gabor_size, envelope='g',alpha=.6,#std_dev=50,
            frequency=frequency, bottom=exp.screen.bottom+50, center_x=exp.screen.center_x,
            contrast = 1, rotate=0, rotate_origin = rotate_origin, color_one = [0,0,0,0.1], color_two = [1,1,1,.1])
        # RIGHT GABOR
        g2 = CWGrating(width=gabor_size, height=gabor_size, envelope='g',alpha=.6, #std_dev=50,
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
            centerreward=NIPulse(task=write_center, dur=self.pulse_dur, vals=[True])
            Wait(until=centerreward.pulse_start_time)
                # wait until we're done sending the pulse
            Wait(until=centerreward.pulse_end_time)
     
    BlankScrLickPunish(interval=4, max_penalty=8-4, penalty=1)

    # if DEV_MODE:
    #     # pull out the response
    #     self.resp = ini.pressed
    #     self.resp_time = ini.press_time
    # else:
    #     self.resp = ini.changed_channels[0]
    #     self.resp_time = ini.change_time

    Log(name="center_port_training",
        rt=ini.rt,
        )
    

# set up the experiment
exp = Experiment(background_color=[0.5,0.5,0.5,1], name="GABOR", resolution=(1280,1024),
                #  fullscreen=False, resolution = (800,600), #"gray",
                 show_splash=False, debug=True)
Wait(.25)

center_training_repeats=10
gabortrials=range(center_training_repeats)
with Loop(gabortrials) as d:
    Trial()
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
