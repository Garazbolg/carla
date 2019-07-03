#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""

"""

import glob
import os
import sys

try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass

import carla

import argparse


def list_options(client):
    pass


def inspect(client):
    pass


def main():
    argparser = argparse.ArgumentParser(
        description=__doc__)
    argparser.add_argument(
        '--host',
        metavar='H',
        default='localhost',
        help='IP of the host CARLA Simulator (default: localhost)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port of CARLA Simulator (default: 2000)')
    argparser.add_argument(
        '-m', '--map',
        help='change map')
    argparser.add_argument(
        '-r', '--reload-map',
        help='reload map')
    argparser.add_argument(
        '-d', '--delta-seconds',
        help='set fixed delta seconds, zero for variable delta seconds')
    argparser.add_argument(
        '--fps',
        help='set fixed FPS, zero for variable FPS (same effect as --delta-seconds)')
    argparser.add_argument(
        '--no-rendering',
        help='disable rendering')
    argparser.add_argument(
        '--rendering',
        help='enable rendering')
    argparser.add_argument(
        '--weather',
        help='')
    argparser.add_argument(
        '-l', '--list',
        help='list options')
    argparser.add_argument(
        '-i', '--inspect',
        help='inspect running simulation and return')
    args = argparser.parse_args()

    client = carla.Client(args.host, args.port, worker_threads=1)

    if args.list:
        list_options(client)
        return
    elif args.inspect:
        inspect(client)
        return



if __name__ == '__main__':

    try:

        main()

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
