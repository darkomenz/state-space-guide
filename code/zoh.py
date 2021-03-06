#!/usr/bin/env python3

# Avoid needing display if plots aren't being shown
import sys

if "--noninteractive" in sys.argv:
    import matplotlib as mpl

    mpl.use("svg")
    import latexutils

import frccontrol as frccnt
import matplotlib.pyplot as plt
import numpy as np

plt.rc("text", usetex=True)


class Elevator(frccnt.System):
    def __init__(self, dt):
        """Elevator subsystem.

        Keyword arguments:
        dt -- time between model/controller updates
        """
        state_labels = [("Position", "m"), ("Velocity", "m/s")]
        u_labels = [("Voltage", "V")]
        self.set_plot_labels(state_labels, u_labels)

        # Number of motors
        self.num_motors = 2.0
        # Elevator carriage mass in kg
        self.m = 6.803886
        # Radius of pulley in meters
        self.r = 0.02762679089
        # Gear ratio
        self.G = 42.0 / 12.0 * 40.0 / 14.0

        self.model = frccnt.models.elevator(
            frccnt.models.MOTOR_CIM, self.num_motors, self.m, self.r, self.G
        )
        frccnt.System.__init__(self, self.model, -12.0, 12.0, dt)

        q = [0.02, 0.4]
        r = [12.0]
        self.design_dlqr_controller(q, r)
        self.design_two_state_feedforward(q, r)

        q_pos = 0.05
        q_vel = 1.0
        r_pos = 0.0001
        self.design_kalman_filter([q_pos, q_vel], [r_pos])


def generate_zoh(data, dt, sample_period):
    """Generates zero-order hold of data set.

    Keyword arguments:
    data -- array of position data
    dt -- dt of original data samples
    sample_period -- desired time between samples in zero-order hold
    """
    y = []
    count = 0
    val = 0
    for i in range(len(data)):
        count += 1
        if count >= sample_period / dt:
            val = data[i]
            count = 0
        y.append(val)
    return y


def main():
    dt = 0.00505
    sample_period = 0.1
    elevator = Elevator(dt)

    # Set up graphing
    l0 = 0.1
    l1 = l0 + 5.0
    l2 = l1 + 0.1
    l3 = l2 + 1.0
    t = np.arange(0, l3, dt)

    refs = []

    # Generate references for simulation
    for i in range(len(t)):
        if t[i] < l0:
            r = np.matrix([[0.0], [0.0]])
        elif t[i] < l1:
            r = np.matrix([[1.524], [0.0]])
        else:
            r = np.matrix([[0.0], [0.0]])
        refs.append(r)

    state_rec, ref_rec, u_rec = elevator.generate_time_responses(t, refs)
    pos = elevator.extract_row(state_rec, 0)

    plt.figure(1)
    plt.xlabel("Time (s)")
    plt.ylabel("Position (m)")
    plt.plot(t, pos, label="Continuous")
    y = generate_zoh(pos, dt, sample_period)
    plt.plot(t, y, label="Zero-order hold (T={}s)".format(sample_period))
    plt.legend()
    if "--noninteractive" in sys.argv:
        latexutils.savefig("zoh")
    else:
        plt.show()


if __name__ == "__main__":
    main()
