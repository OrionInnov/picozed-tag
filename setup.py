#!/usr/bin/env python

from distutils.core import setup

setup(name="picozed1-tag",
      version="1.0",
      description="PicoZed 1x1 SDR tag emulator.",
      author="Orion Innovations",
      packages=["tag"],
      package_data={"tag": ["seqs_4095.npy"]},
     )

