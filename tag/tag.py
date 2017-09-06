"""
taganchor.py: Orion tag system anchor.
"""

import os
import time

import iio
import numpy as np


# physical device name
DEVICE_NAME = "ad9361-phy"

# streaming channel name
DEVICE_TX_NAME = "cf-ad9361-dds-core-lpc"

# operational mode
ENSM_MODE = "tx"

# port selection
TX_PORT_SELECT = "A"

# hardware gain value (in dB)
TX_GAIN_VALUE = 0


class PicoZedSDR1(object):

    def __init__(self, bandwidth, samp_rate, center_freq, buff_size):

        self.bandwidth = bandwidth
        self.samp_rate = samp_rate
        self.center_freq = center_freq
        self.buff_size = buff_size

        # create local IIO context
        self.context = iio.Context()

        # configure the AD9361 devices
        self._configure_ad9361_phy()
        self._create_buffer()

    def _configure_ad9361_phy(self):

        # access physical devices
        self.device = self.context.find_device(DEVICE_NAME)

        # set mode to TX only
        self.device.attrs["ensm_mode"].value = ENSM_MODE

        # LO channel is always output
        chan = self.device.find_channel("voltage0", is_output=True)
        chan_lo = self.device.find_channel("altvoltage1", is_output=True)

        # set gain parameter
        chan.attrs["hardwaregain"].value = str(TX_GAIN_VALUE)

        # set channel attributes
        chan.attrs["rf_port_select"].value = TX_PORT_SELECT
        chan.attrs["rf_bandwidth"].value = str(self.bandwidth)
        chan.attrs["sampling_frequency"].value = str(self.samp_rate)

        # set LO channel attributes
        chan_lo.attrs["frequency"].value = str(self.center_freq)

        # TODO(liuf): gain value must be set again (for some reason)
        chan.attrs["hardwaregain"].value = str(TX_GAIN_VALUE)

    def _create_buffer(self):

        self.device_tx = self.context.find_device(DEVICE_TX_NAME)

        # configure master streaming devices
        # 1x1 SDR contains only two channels
        for n in range(2):
            name = "voltage{0}".format(n)
            chan = self.device_tx.find_channel(name, is_output=True)
            chan.enabled = True

        # create buffer
        self.buffer_tx = iio.Buffer(self.device_tx, self.buff_size, 
                                    cyclic=True)

    def push_samples(self, i_data, q_data):
        """
            Pushes a set of I/Q data to the buffer.
        """

        assert i_data.size == q_data.size, "I length != Q length"
        assert i_data.size <= self.buff_size, "input data too long"

        # scale I and Q data
        i_data = i_data / i_data.max() * 32767
        q_data = q_data / q_data.max() * 32767
        i_data = np.rint(i_data).astype(np.int16)
        q_data = np.rint(q_data).astype(np.int16)

        # pad zeros as needed
        pad_size = self.buff_size - i_data.size
        i_data = np.pad(i_data, (0, pad_size), "constant")
        q_data = np.pad(q_data, (0, pad_size), "constant")

        # interleave I/Q data into new array
        signal = np.empty((i_data.size + q_data.size, ), dtype=np.int16)
        signal[0::2] = i_data
        signal[1::2] = q_data

        # write samples to buffer
        data = bytearray(signal.tostring())
        self.buffer_tx.write(data)
        self.buffer_tx.push()


def main(args):

    tag_num = args.tag_num
    bandwidth = args.bandwidth
    samp_rate = args.samp_rate
    center_freq = args.center_freq
    period = args.period

    # load bits to transmit
    dir_path = os.path.dirname(os.path.realpath(__file__))
    seqs_path = os.path.join(dir_path, "seqs_4095.npy")
    bits = np.load(seqs_path)[tag_num,:]

    # compute buffer size given transmission period
    buff_size = int(np.rint(args.period * samp_rate))
    buff_size = max(buff_size, bits.size)

    # create the PicoZed SDR object
    picozed = PicoZedSDR1(bandwidth, samp_rate, center_freq, buff_size)

    # transmit signal (TX uses 12-bit DAC in 16-bit format)
    picozed.push_samples(bits, bits)

    # block for cyclic buffer
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return 0

