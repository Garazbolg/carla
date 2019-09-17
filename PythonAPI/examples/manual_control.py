#!/usr/bin/env python

# Copyright (c) 2019 Computer Vision Center (CVC) at the Universitat Autonoma de
# Barcelona (UAB).
#
# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

# Allows controlling a vehicle with a keyboard. For a simpler and more
# documented example, please take a look at tutorial.py.

"""
Welcome to CARLA manual control for keyboard and steering wheel.

Use ARROWS or WASD keys for control.

    W            : throttle
    S            : brake
    AD           : steer
    Q            : toggle reverse
    Space        : hand-brake
    P            : toggle autopilot
    M            : toggle manual transmission
    ,/.          : gear up/down

    TAB          : change sensor position
    `            : next sensor
    [1-9]        : change to sensor [1-9]
    C            : change weather (Shift+C reverse)
    Backspace    : change vehicle

    R            : toggle recording images to disk

    CTRL + R     : toggle recording of simulation (replacing any previous)
    CTRL + P     : start replaying last recorded simulation
    CTRL + +     : increments the start time of the replay by 1 second (+SHIFT = 10 seconds)
    CTRL + -     : decrements the start time of the replay by 1 second (+SHIFT = 10 seconds)

    F1           : toggle HUD
    H/?          : toggle help
    ESC          : quit

Or use the steering wheel

    To drive start by preshing the brake pedal.
    Change your wheel_config.ini according to your steering wheel.

    To find out the values of your steering wheel use jstest-gtk in Ubuntu.

"""

from __future__ import print_function


# ==============================================================================
# -- find carla module ---------------------------------------------------------
# ==============================================================================


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


# ==============================================================================
# -- imports -------------------------------------------------------------------
# ==============================================================================


import carla

from carla import ColorConverter as cc

import argparse
import collections
import datetime
import logging
import math
import random
import re
import weakref

if sys.version_info >= (3, 0):

    from configparser import ConfigParser

else:

    from ConfigParser import RawConfigParser as ConfigParser

try:
    import pygame
    from pygame.locals import KMOD_CTRL
    from pygame.locals import KMOD_SHIFT
    from pygame.locals import K_0
    from pygame.locals import K_9
    from pygame.locals import K_BACKQUOTE
    from pygame.locals import K_BACKSPACE
    from pygame.locals import K_COMMA
    from pygame.locals import K_DOWN
    from pygame.locals import K_ESCAPE
    from pygame.locals import K_F1
    from pygame.locals import K_LEFT
    from pygame.locals import K_PERIOD
    from pygame.locals import K_RIGHT
    from pygame.locals import K_SLASH
    from pygame.locals import K_SPACE
    from pygame.locals import K_TAB
    from pygame.locals import K_UP
    from pygame.locals import K_a
    from pygame.locals import K_c
    from pygame.locals import K_d
    from pygame.locals import K_h
    from pygame.locals import K_m
    from pygame.locals import K_p
    from pygame.locals import K_q
    from pygame.locals import K_r
    from pygame.locals import K_s
    from pygame.locals import K_w
    from pygame.locals import K_l
    from pygame.locals import K_MINUS
    from pygame.locals import K_EQUALS
except ImportError:
    raise RuntimeError('cannot import pygame, make sure pygame package is installed')

try:
    import numpy as np
except ImportError:
    raise RuntimeError('cannot import numpy, make sure numpy package is installed')


#import rospy
import numpy
#from sensor_msgs.msg import Image
#from std_msgs.msg import String
#import carla_ros_bridge
#from carla_ros_bridge import *
#from cv_bridge import CvBridge,CvBridgeError
#cv_bridge = CvBridge()
#import imageio

import NoiseGenerator
import UDP
UDP.Sender.init()
import TCP
import YUV
import time

running = True

# ==============================================================================
# -- Global functions ----------------------------------------------------------
# ==============================================================================


def find_weather_presets():
    rgx = re.compile('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)')
    name = lambda x: ' '.join(m.group(0) for m in rgx.finditer(x))
    presets = [x for x in dir(carla.WeatherParameters) if re.match('[A-Z].+', x)]
    return [(getattr(carla.WeatherParameters, x), name(x)) for x in presets]


def get_actor_display_name(actor, truncate=250):
    name = ' '.join(actor.type_id.replace('_', '.').title().split('.')[1:])
    return (name[:truncate - 1] + u'\u2026') if len(name) > truncate else name


# ==============================================================================
# -- World ---------------------------------------------------------------------
# ==============================================================================


class World(object):
    def __init__(self, carla_world, hud, args):
        self.world = carla_world
        self.actor_role_name = args.rolename
        self.map = self.world.get_map()
        self.hud = hud
        self.player = None
        self.collision_sensor = None
        self.camera_manager = None
        self._weather_presets = find_weather_presets()
        self._weather_index = 0

        self._actor_filter = args.filter
        self._gamma = args.gamma

        self.V3H_IP = "192.168.1.20"

        self.vehicle_index = 14
        self.mixed_reality_mode = True
        #self.mixed_publisher = rospy.Publisher("/eSoft/Mixed/Active",String,queue_size=1)

        self.noise = NoiseGenerator.SoundManager()
        self.warningReceiver = UDP.Receiver(5584,32,self.receive_noise_message)
        #self.noiseSubscriber = rospy.Subscriber("/eSoft/IVI/Index",String,self.receive_noise_message)

        self.retro_left_position = (2.9,-1.1,1)#(5.9,-0.8,1.0)#(3.5,-1.5,1.0)
        self.retro_left_rotation = (0.0,196.4,0.0)#(0.0,196.5,0.0)
        self.retro_left_fov = 80#100

        self.retro_right_position = (3.4,0.9,1.0)
        self.retro_right_rotation = (0.0,164,0.0)
        self.retro_right_fov = 90

        self.curentRetroIndex = 0

        self.mirrors = []

        self.restart()
        self.world.on_tick(hud.on_world_tick)
        self.recording_enabled = False
        self.recording_start = 0

    def restart(self):
        # Keep same camera config if the camera manager exists.
        cam_index = self.camera_manager.index if self.camera_manager is not None else 0
        cam_pos_index = self.camera_manager.transform_index if self.camera_manager is not None else 0
        # Get a specific blueprint selected by ID.
        #for bp in self.world.get_blueprint_library().filter(self._actor_filter):
        #    print(str(bp.id))
        blueprint = next( x for x in self.world.get_blueprint_library().filter(self._actor_filter) if x.id.endswith('esoft.realistic'))
        #blueprint = next( x for x in self.world.get_blueprint_library().filter(self._actor_filter) if x.id.endswith('audi.a2'))
        
        blueprint.set_attribute('role_name', self.actor_role_name)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if blueprint.has_attribute('driver_id'):
            driver_id = random.choice(blueprint.get_attribute('driver_id').recommended_values)
            blueprint.set_attribute('driver_id', driver_id)
        if blueprint.has_attribute('is_invincible'):
            blueprint.set_attribute('is_invincible', 'true')
        # Spawn the player.
        if self.player is not None:
            spawn_point = self.player.get_transform()
            spawn_point.location.z += 2.0
            spawn_point.rotation.roll = 0.0
            spawn_point.rotation.pitch = 0.0
            self.destroy()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        while self.player is None:
            spawn_points = self.map.get_spawn_points()
            spawn_point = random.choice(spawn_points) if spawn_points else carla.Transform()
            self.player = self.world.try_spawn_actor(blueprint, spawn_point)
        # Set up the sensors.
        self.collision_sensor = CollisionSensor(self.player, self.hud,self)
        self.camera_manager = NoCameraManager(self.player, self.hud, self._gamma)
        self.camera_manager.transform_index = cam_pos_index
        self.camera_manager.set_sensor(cam_index, notify=False)
        actor_type = get_actor_display_name(self.player)
        self.hud.notification(actor_type)
        #Setup the mirrors.
        time.sleep(0.5)
        self.init_mirrors()

    def init_mirrors(self):
        for mirror in self.mirrors:
            mirror.destroy()
        self.mirrors = []
        self.mirrors.append(
            Mirror(
                self.player,
                (self.hud.mDim[0],self.hud.mDim[1]),
                (0                               ,self.hud.dim[1]-self.hud.mDim[1]),
                "capture/left/" ,
                self.retro_left_position,
                self.retro_left_rotation,
                not self.mixed_reality_mode,
                self.retro_left_fov,
                "192.168.1.20",5581,
                True))
        self.mirrors.append(
           Mirror(
                self.player,
                (self.hud.mDim[0],self.hud.mDim[1]),
                (self.hud.dim[0]-self.hud.mDim[0],self.hud.dim[1]-self.hud.mDim[1]),
                "capture/right/",
                self.retro_right_position,
                self.retro_right_rotation,
                True,
                self.retro_right_fov,
                "127.0.0.1",5580,
                False))

    def next_weather(self, reverse=False):
        self._weather_index += -1 if reverse else 1
        self._weather_index %= len(self._weather_presets)
        preset = self._weather_presets[self._weather_index]
        self.hud.notification('Weather: %s' % preset[1])
        self.player.get_world().set_weather(preset[0])

    def mixed_reality_toggle(self, value = None):
        if value is None :
            value = not self.mixed_reality_mode
        self.mixed_reality_mode = value
        UDP.Sender.sendString(("1" if self.mixed_reality_mode else "0"),self.V3H_IP,5582)
        UDP.Sender.sendString(("1" if self.mixed_reality_mode else "0"),"127.0.0.1",5582)
        self.init_mirrors()
        
    def updateRetro(self,positive):
        if(self.hud._show_info):
            pas = 0.1 if positive else -0.1
            rot = 10 if positive else -10
            if(self.curentRetroIndex == 0):
                self.retro_left_position = (self.retro_left_position[0] + pas,self.retro_left_position[1],self.retro_left_position[2])
            elif(self.curentRetroIndex == 1):
                self.retro_left_position = (self.retro_left_position[0],self.retro_left_position[1] + pas,self.retro_left_position[2])
            elif(self.curentRetroIndex == 2):
                self.retro_left_rotation = (self.retro_left_rotation[0],self.retro_left_rotation[1] + pas,self.retro_left_rotation[2])
            elif(self.curentRetroIndex == 3):
                self.retro_left_fov = self.retro_left_fov + rot
            elif(self.curentRetroIndex == 4):
                self.retro_right_position = (self.retro_right_position[0]+pas,self.retro_right_position[1],self.retro_right_position[2])
            elif(self.curentRetroIndex == 5):
                self.retro_right_position = (self.retro_right_position[0],self.retro_right_position[1]+pas,self.retro_right_position[2])
            elif(self.curentRetroIndex == 6 ):
                self.retro_right_rotation = (self.retro_right_rotation[0],self.retro_right_rotation[1]+pas,self.retro_right_rotation[2])
            elif(self.curentRetroIndex == 7 ):
                self.retro_right_fov = self.retro_right_fov + rot

            if(self.mirrors is not None):
                if(self.curentRetroIndex == 3 or self.curentRetroIndex == 7):
                    print("Mirror left : "+str(self.retro_left_position)+ " " + str(self.retro_left_rotation) +" fov : "+str(self.retro_left_fov))
                    print("Mirror right : "+str(self.retro_right_position)+ " " + str(self.retro_right_rotation) +" fov : "+str(self.retro_right_fov))
                    self.init_mirrors()
                elif(self.curentRetroIndex<3):
                    print("Mirror left : "+str(self.retro_left_position)+ " " + str(self.retro_left_rotation) +" fov : "+str(self.retro_left_fov))
                    self.mirrors[0].setTransform(self.retro_left_position,self.retro_left_rotation)
                else:
                    print("Mirror right : "+str(self.retro_right_position)+ " " + str(self.retro_right_rotation) +" fov : "+str(self.retro_right_fov))
                    self.mirrors[1].setTransform(self.retro_right_position,self.retro_right_rotation)

    def receive_noise_message(self, msg):
        self.noise.warningActive = True if msg.decode('utf-8') != "0" else False

    def tick(self, clock):
        self.hud.tick(self, clock)
        v = self.player.get_velocity()
        self.noise.velocity = (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2))

    def render(self, display):
        self.camera_manager.render(display)
        for mirror in self.mirrors:
            mirror.render(display)
        self.hud.render(display)

    def destroy_sensors(self):
        self.camera_manager.destroy()

    def destroy(self):
        actors = [
            self.collision_sensor.sensor,
            self.player]
        self.destroy_sensors()
        for actor in actors:
            if actor is not None:
                actor.destroy()
        for mirror in self.mirrors:
            mirror.destroy()
        self.mirrors = []
        self.warningReceiver.Stop()

# ==============================================================================
# -- KeyboardControl -----------------------------------------------------------
# ==============================================================================


class KeyboardControl(object):
    def __init__(self, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            world.player.set_autopilot(self._autopilot_enabled)
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

    def parse_events(self, client, world, clock):
        global running
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == K_BACKSPACE: # Switch Mixed-Virtual
                    world.mixed_reality_toggle()
                elif event.key == K_F1:
                    world.hud.toggle_info()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud.help.toggle()
                elif event.key == K_l:
                    running = not running
                elif event.key == K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key > K_0 and event.key <= K_9:
                    world.camera_manager.set_sensor(event.key - 1 - K_0)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    world.camera_manager.toggle_recording()
                elif event.key == K_r and (pygame.key.get_mods() & KMOD_CTRL):
                    if (world.recording_enabled):
                        client.stop_recorder()
                        world.recording_enabled = False
                        world.hud.notification("Recorder is OFF")
                    else:
                        client.start_recorder("manual_recording.rec")
                        world.recording_enabled = True
                        world.hud.notification("Recorder is ON")
                elif event.key == K_p and (pygame.key.get_mods() & KMOD_CTRL):
                    # stop recorder
                    client.stop_recorder()
                    world.recording_enabled = False
                    # work around to fix camera at start of replaying
                    currentIndex = world.camera_manager.index
                    world.destroy_sensors()
                    # disable autopilot
                    self._autopilot_enabled = False
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification("Replaying file 'manual_recording.rec'")
                    # replayer
                    client.replay_file("manual_recording.rec", world.recording_start, 0, 0)
                    world.camera_manager.set_sensor(currentIndex)
                elif event.key == K_MINUS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start -= 10
                    else:
                        world.recording_start -= 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                elif event.key == K_EQUALS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start += 10
                    else:
                        world.recording_start += 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification('%s Transmission' %
                                               ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and (event.key == K_COMMA):
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and (event.key == K_PERIOD):
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p and not (pygame.key.get_mods() & KMOD_CTRL):
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                self._control.reverse = self._control.gear < 0
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time())
            world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0 
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_walker_keys(self, keys, milliseconds):
        self._control.speed = 0.0
        if keys[K_DOWN] or keys[K_s]:
            self._control.speed = 0.0
        if keys[K_LEFT] or keys[K_a]:
            self._control.speed = .01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[K_RIGHT] or keys[K_d]:
            self._control.speed = .01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[K_UP] or keys[K_w]:
            self._control.speed = 3.333 if pygame.key.get_mods() & KMOD_SHIFT else 2.778
        self._control.jump = keys[K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)



# ==============================================================================
# -- DualControl -----------------------------------------------------------
# ==============================================================================


class DualControl(object):
    def __init__(self, world, start_in_autopilot):
        self._autopilot_enabled = start_in_autopilot
        if isinstance(world.player, carla.Vehicle):
            self._control = carla.VehicleControl()
            world.player.set_autopilot(self._autopilot_enabled)
            self._control.manual_gear_shift = True
            self._control.gear = 1
        elif isinstance(world.player, carla.Walker):
            self._control = carla.WalkerControl()
            self._autopilot_enabled = False
            self._rotation = world.player.get_transform().rotation
        else:
            raise NotImplementedError("Actor type not supported")
        self._steer_cache = 0.0
        world.hud.notification("Press 'H' or '?' for help.", seconds=4.0)

        # initialize steering wheel
        pygame.joystick.init()

        joystick_count = pygame.joystick.get_count()
        if joystick_count > 1:
            raise ValueError("Please Connect Just One Joystick")

        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        print("Initializing Joystick : " + self._joystick.get_name())

        self._parser = ConfigParser()
        self._parser.read('wheel_config.ini')
        self._steer_idx = int(
            self._parser.get(self._joystick.get_name(), 'steering_wheel'))
        self._throttle_idx = int(
            self._parser.get(self._joystick.get_name(), 'throttle'))
        self._brake_idx = int(self._parser.get(self._joystick.get_name(), 'brake'))
        self._reverse_idx = int(self._parser.get(self._joystick.get_name(), 'reverse'))
        self._handbrake_idx = int(
            self._parser.get(self._joystick.get_name(), 'handbrake'))
        self._mixed_idx = int(self._parser.get(self._joystick.get_name(), 'mixed'))
        self._hud_idx = int(self._parser.get(self._joystick.get_name(), 'hud'))
        self._left_right_idx = int(self._parser.get(self._joystick.get_name(), 'left_right'))
        self._weather_idx = int(self._parser.get(self._joystick.get_name(), 'weather'))
        self._gear_up_idx   = int(self._parser.get(self._joystick.get_name(), 'gear_up'))
        self._gear_down_idx = int(self._parser.get(self._joystick.get_name(), 'gear_down'))
        self._auto_pilot_idx = int(self._parser.get(self._joystick.get_name(), 'auto_pilot'))

    def parse_events(self, client, world, clock):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == self._mixed_idx: #Switch Mixed/Virtual
                    world.mixed_reality_toggle()
                elif event.button == self._hud_idx:
                    world.hud.toggle_info()
                #elif event.button == self._left_right_idx: #Switch Left/Right
                    #world.camera_manager.toggle_camera()
                elif event.button == self._weather_idx:
                    world.next_weather()
                elif event.button == self._reverse_idx:
                    self._control.gear = 1 if self._control.reverse else -1
                elif event.button == 23:
                    world.camera_manager.next_sensor()
                elif self._control.manual_gear_shift and event.button == self._gear_down_idx:
                    self._control.gear = max(-1, self._control.gear - 1)
                elif self._control.manual_gear_shift and event.button == self._gear_up_idx:
                    self._control.gear = self._control.gear + 1
                elif event.button == self._auto_pilot_idx:
                    self._autopilot_enabled = not self._autopilot_enabled
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                    self._control.manual_gear_shift = not self._control.manual_gear_shift
                    self._control.gear = world.player.get_control().gear
                elif event.button == 2:
                    world.updateRetro(False)
                elif event.button == 3:
                    world.updateRetro(True)
                elif event.button == 4:
                    world.curentRetroIndex = (world.curentRetroIndex +1)%8

            elif event.type == pygame.KEYUP:
                if self._is_quit_shortcut(event.key):
                    return True
                elif event.key == K_BACKSPACE:
                    world.mixed_reality_toggle()
                elif event.key == K_F1:
                    world.hud.toggle_info()
                elif event.key == K_h or (event.key == K_SLASH and pygame.key.get_mods() & KMOD_SHIFT):
                    world.hud.help.toggle()
                elif event.key == K_l:
                    running = not running
                elif event.key == K_TAB:
                    world.camera_manager.toggle_camera()
                elif event.key == K_c and pygame.key.get_mods() & KMOD_SHIFT:
                    world.next_weather(reverse=True)
                elif event.key == K_c:
                    world.next_weather()
                elif event.key == K_BACKQUOTE:
                    world.camera_manager.next_sensor()
                elif event.key > K_0 and event.key <= K_9:
                    world.camera_manager.set_sensor(event.key - 1 - K_0)
                elif event.key == K_r and not (pygame.key.get_mods() & KMOD_CTRL):
                    world.camera_manager.toggle_recording()
                elif event.key == K_r and (pygame.key.get_mods() & KMOD_CTRL):
                    if (world.recording_enabled):
                        client.stop_recorder()
                        world.recording_enabled = False
                        world.hud.notification("Recorder is OFF")
                    else:
                        client.start_recorder("manual_recording.rec")
                        world.recording_enabled = True
                        world.hud.notification("Recorder is ON")
                elif event.key == K_p and (pygame.key.get_mods() & KMOD_CTRL):
                    # stop recorder
                    client.stop_recorder()
                    world.recording_enabled = False
                    # work around to fix camera at start of replaying
                    currentIndex = world.camera_manager.index
                    world.destroy_sensors()
                    # disable autopilot
                    self._autopilot_enabled = False
                    world.player.set_autopilot(self._autopilot_enabled)
                    world.hud.notification("Replaying file 'manual_recording.rec'")
                    # replayer
                    client.replay_file("manual_recording.rec", world.recording_start, 0, 0)
                    world.camera_manager.set_sensor(currentIndex)
                elif event.key == K_MINUS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start -= 10
                    else:
                        world.recording_start -= 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                elif event.key == K_EQUALS and (pygame.key.get_mods() & KMOD_CTRL):
                    if pygame.key.get_mods() & KMOD_SHIFT:
                        world.recording_start += 10
                    else:
                        world.recording_start += 1
                    world.hud.notification("Recording start time is %d" % (world.recording_start))
                if isinstance(self._control, carla.VehicleControl):
                    if event.key == K_q:
                        self._control.gear = 1 if self._control.reverse else -1
                    elif event.key == K_m:
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear
                        world.hud.notification('%s Transmission' %
                                               ('Manual' if self._control.manual_gear_shift else 'Automatic'))
                    elif self._control.manual_gear_shift and event.key == K_COMMA:
                        self._control.gear = max(-1, self._control.gear - 1)
                    elif self._control.manual_gear_shift and event.key == K_PERIOD:
                        self._control.gear = self._control.gear + 1
                    elif event.key == K_p:
                        self._autopilot_enabled = not self._autopilot_enabled
                        world.player.set_autopilot(self._autopilot_enabled)
                        world.hud.notification('Autopilot %s' % ('On' if self._autopilot_enabled else 'Off'))
                        self._control.manual_gear_shift = not self._control.manual_gear_shift
                        self._control.gear = world.player.get_control().gear

        if not self._autopilot_enabled:
            if isinstance(self._control, carla.VehicleControl):
                self._parse_vehicle_keys(pygame.key.get_pressed(), clock.get_time())
                self._parse_vehicle_wheel()
                self._control.reverse = self._control.gear < 0
            elif isinstance(self._control, carla.WalkerControl):
                self._parse_walker_keys(pygame.key.get_pressed(), clock.get_time())
            world.player.apply_control(self._control)

    def _parse_vehicle_keys(self, keys, milliseconds):
        self._control.throttle = 1.0 if keys[K_UP] or keys[K_w] else 0.0
        steer_increment = 5e-4 * milliseconds
        if keys[K_LEFT] or keys[K_a]:
            self._steer_cache -= steer_increment
        elif keys[K_RIGHT] or keys[K_d]:
            self._steer_cache += steer_increment
        else:
            self._steer_cache = 0.0
        self._steer_cache = min(0.7, max(-0.7, self._steer_cache))
        self._control.steer = round(self._steer_cache, 1)
        self._control.brake = 1.0 if keys[K_DOWN] or keys[K_s] else 0.0
        self._control.hand_brake = keys[K_SPACE]

    def _parse_vehicle_wheel(self):
        numAxes = self._joystick.get_numaxes()
        jsInputs = [float(self._joystick.get_axis(i)) for i in range(numAxes)]
        # print (jsInputs)
        jsButtons = [float(self._joystick.get_button(i)) for i in
                     range(self._joystick.get_numbuttons())]

        # Custom function to map range of inputs [1, -1] to outputs [0, 1] i.e 1 from inputs means nothing is pressed
        # For the steering, it seems fine as it is
        K1 = 0.55
        #K1 = 0.25
        MinSteer = 100
        steerCmd = K1 *(NoiseGenerator.Clamp01(abs(jsInputs[self._steer_idx])*MinSteer)* jsInputs[self._steer_idx])
        #steerCmd = K1 * math.pow(1 * jsInputs[self._steer_idx],2)*(-1 if jsInputs[self._steer_idx]<0 else 1)

        K2 = 1.6  # 1.6
        throttleCmd = K2 + (2.05 * math.log10(
            -0.7 * jsInputs[self._throttle_idx] + 1.4) - 1.2) / 0.92
        if throttleCmd <= 0:
            throttleCmd = 0
        elif throttleCmd > 1:
            throttleCmd = 1

        brakeCmd = 1.6 + (2.05 * math.log10(
            -0.7 * jsInputs[self._brake_idx] + 1.4) - 1.2) / 0.92
        if brakeCmd <= 0:
            brakeCmd = 0
        elif brakeCmd > 1:
            brakeCmd = 1

        self._control.steer = steerCmd
        self._control.brake = brakeCmd
        self._control.throttle = throttleCmd

        #toggle = jsButtons[self._reverse_idx]

        self._control.hand_brake = bool(jsButtons[self._handbrake_idx])

    def _parse_walker_keys(self, keys, milliseconds):
        self._control.speed = 0.0
        if keys[K_DOWN] or keys[K_s]:
            self._control.speed = 0.0
        if keys[K_LEFT] or keys[K_a]:
            self._control.speed = .01
            self._rotation.yaw -= 0.08 * milliseconds
        if keys[K_RIGHT] or keys[K_d]:
            self._control.speed = .01
            self._rotation.yaw += 0.08 * milliseconds
        if keys[K_UP] or keys[K_w]:
            self._control.speed = 5.556 if pygame.key.get_mods() & KMOD_SHIFT else 2.778
        self._control.jump = keys[K_SPACE]
        self._rotation.yaw = round(self._rotation.yaw, 1)
        self._control.direction = self._rotation.get_forward_vector()

    @staticmethod
    def _is_quit_shortcut(key):
        return (key == K_ESCAPE) or (key == K_q and pygame.key.get_mods() & KMOD_CTRL)


# ==============================================================================
# -- HUD -----------------------------------------------------------------------
# ==============================================================================


class HUD(object):
    def __init__(self, width, height, mDim):
        self.dim = (width, height)
        self.mDim = mDim
        font = pygame.font.Font(pygame.font.get_default_font(), 20)
        fonts = pygame.font.get_fonts()
        default_font = 'ubuntumono'
        mono = default_font if default_font in fonts else fonts[0]
        mono = pygame.font.match_font(mono)
        self._font_mono = pygame.font.Font(mono, 14)
        self._notifications = FadingText(font, (width, 40), (0, height - 40))
        self.help = HelpText(pygame.font.Font(mono, 24), width, height)
        self.server_fps = 0
        self.frame = 0
        self.simulation_time = 0
        self._show_info = False
        self._info_text = []
        self._server_clock = pygame.time.Clock()

    def on_world_tick(self, timestamp):
        self._server_clock.tick()
        self.server_fps = self._server_clock.get_fps()
        self.frame = timestamp.frame
        self.simulation_time = timestamp.elapsed_seconds

    def tick(self, world, clock):
        self._notifications.tick(world, clock)
        if not self._show_info:
            return
        t = world.player.get_transform()
        v = world.player.get_velocity()
        c = world.player.get_control()
        heading = 'N' if abs(t.rotation.yaw) < 89.5 else ''
        heading += 'S' if abs(t.rotation.yaw) > 90.5 else ''
        heading += 'E' if 179.5 > t.rotation.yaw > 0.5 else ''
        heading += 'W' if -0.5 > t.rotation.yaw > -179.5 else ''
        colhist = world.collision_sensor.get_collision_history()
        collision = [colhist[x + self.frame - 200] for x in range(0, 200)]
        max_col = max(1.0, max(collision))
        collision = [x / max_col for x in collision]
        vehicles = world.world.get_actors().filter('vehicle.*')
        self._info_text = [
            'Server:  % 16.0f FPS' % self.server_fps,
            'Client:  % 16.0f FPS' % clock.get_fps(),
            '',
            'Vehicle: % 20s' % get_actor_display_name(world.player, truncate=20),
            'Map:     % 20s' % world.map.name,
            'Simulation time: % 12s' % datetime.timedelta(seconds=int(self.simulation_time)),
            '',
            'Speed:   % 15.0f km/h' % (3.6 * math.sqrt(v.x**2 + v.y**2 + v.z**2)),
            u'Heading:% 16.0f\N{DEGREE SIGN} % 2s' % (t.rotation.yaw, heading),
            'Location:% 20s' % ('(% 5.1f, % 5.1f)' % (t.location.x, t.location.y)),
            'Height:  % 18.0f m' % t.location.z,
            '']
        if isinstance(c, carla.VehicleControl):
            self._info_text += [
                ('Throttle:', c.throttle, 0.0, 1.0),
                ('Steer:', c.steer, -1.0, 1.0),
                ('Brake:', c.brake, 0.0, 1.0),
                ('Reverse:', c.reverse),
                ('Hand brake:', c.hand_brake),
                ('Manual:', c.manual_gear_shift),
                'Gear:        %s' % {-1: 'R', 0: 'N'}.get(c.gear, c.gear)]
        elif isinstance(c, carla.WalkerControl):
            self._info_text += [
                ('Speed:', c.speed, 0.0, 5.556),
                ('Jump:', c.jump)]
        self._info_text += [
            '',
            'Collision:',
            collision,
            '',
            'Number of vehicles: % 8d' % len(vehicles)]
        if len(vehicles) > 1:
            self._info_text += ['Nearby vehicles:']
            distance = lambda l: math.sqrt((l.x - t.location.x)**2 + (l.y - t.location.y)**2 + (l.z - t.location.z)**2)
            vehicles = [(distance(x.get_location()), x) for x in vehicles if x.id != world.player.id]
            for d, vehicle in sorted(vehicles):
                if d > 200.0:
                    break
                vehicle_type = get_actor_display_name(vehicle, truncate=22)
                self._info_text.append('% 4dm %s' % (d, vehicle_type))

    def toggle_info(self):
        self._show_info = not self._show_info

    def notification(self, text, seconds=2.0):
        self._notifications.set_text(text, seconds=seconds)

    def error(self, text):
        self._notifications.set_text('Error: %s' % text, (255, 0, 0))

    def render(self, display):
        if self._show_info:
            info_surface = pygame.Surface((220, self.dim[1]))
            info_surface.set_alpha(100)
            display.blit(info_surface, (0, 0))
            v_offset = 4
            bar_h_offset = 100
            bar_width = 106
            for item in self._info_text:
                if v_offset + 18 > self.dim[1]:
                    break
                if isinstance(item, list):
                    if len(item) > 1:
                        points = [(x + 8, v_offset + 8 + (1.0 - y) * 30) for x, y in enumerate(item)]
                        pygame.draw.lines(display, (255, 136, 0), False, points, 2)
                    item = None
                    v_offset += 18
                elif isinstance(item, tuple):
                    if isinstance(item[1], bool):
                        rect = pygame.Rect((bar_h_offset, v_offset + 8), (6, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect, 0 if item[1] else 1)
                    else:
                        rect_border = pygame.Rect((bar_h_offset, v_offset + 8), (bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect_border, 1)
                        f = (item[1] - item[2]) / (item[3] - item[2])
                        if item[2] < 0.0:
                            rect = pygame.Rect((bar_h_offset + f * (bar_width - 6), v_offset + 8), (6, 6))
                        else:
                            rect = pygame.Rect((bar_h_offset, v_offset + 8), (f * bar_width, 6))
                        pygame.draw.rect(display, (255, 255, 255), rect)
                    item = item[0]
                if item:  # At this point has to be a str.
                    surface = self._font_mono.render(item, True, (255, 255, 255))
                    display.blit(surface, (8, v_offset))
                v_offset += 18
        #self._notifications.render(display)
        self.help.render(display)


# ==============================================================================
# -- FadingText ----------------------------------------------------------------
# ==============================================================================


class FadingText(object):
    def __init__(self, font, dim, pos):
        self.font = font
        self.dim = dim
        self.pos = pos
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)

    def set_text(self, text, color=(255, 255, 255), seconds=2.0):
        text_texture = self.font.render(text, True, color)
        self.surface = pygame.Surface(self.dim)
        self.seconds_left = seconds
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(text_texture, (10, 11))

    def tick(self, _, clock):
        delta_seconds = 1e-3 * clock.get_time()
        self.seconds_left = max(0.0, self.seconds_left - delta_seconds)
        self.surface.set_alpha(500.0 * self.seconds_left)

    def render(self, display):
        display.blit(self.surface, self.pos)


# ==============================================================================
# -- HelpText ------------------------------------------------------------------
# ==============================================================================


class HelpText(object):
    def __init__(self, font, width, height):
        lines = __doc__.split('\n')
        self.font = font
        self.dim = (680, len(lines) * 22 + 12)
        self.pos = (0.5 * width - 0.5 * self.dim[0], 0.5 * height - 0.5 * self.dim[1])
        self.seconds_left = 0
        self.surface = pygame.Surface(self.dim)
        self.surface.fill((0, 0, 0, 0))
        for n, line in enumerate(lines):
            text_texture = self.font.render(line, True, (255, 255, 255))
            self.surface.blit(text_texture, (22, n * 22))
            self._render = False
        self.surface.set_alpha(220)

    def toggle(self):
        self._render = not self._render

    def render(self, display):
        if self._render:
            display.blit(self.surface, self.pos)


# ==============================================================================
# -- CollisionSensor -----------------------------------------------------------
# ==============================================================================


class CollisionSensor(object):
    def __init__(self, parent_actor, hud, world_ref):
        self.sensor = None
        self.history = []
        self._parent = parent_actor
        self.hud = hud
        self.world = world_ref
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.collision')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: CollisionSensor._on_collision(weak_self, event))

    def get_collision_history(self):
        history = collections.defaultdict(int)
        for frame, intensity in self.history:
            history[frame] += intensity
        return history

    @staticmethod
    def _on_collision(weak_self, event):
        self = weak_self()
        if not self:
            return
        actor_type = get_actor_display_name(event.other_actor)
        self.hud.notification('Collision with %r' % actor_type)
        impulse = event.normal_impulse
        intensity = math.sqrt(impulse.x**2 + impulse.y**2 + impulse.z**2)
        self.world.noise.new_impact(self.world.noise.velocity)
        self.history.append((event.frame, intensity))
        if len(self.history) > 4000:
            self.history.pop(0)


# ==============================================================================
# -- LaneInvasionSensor --------------------------------------------------------
# ==============================================================================


class LaneInvasionSensor(object):
    def __init__(self, parent_actor, hud):
        self.sensor = None
        self._parent = parent_actor
        self.hud = hud
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.lane_invasion')
        self.sensor = world.spawn_actor(bp, carla.Transform(), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: LaneInvasionSensor._on_invasion(weak_self, event))

    @staticmethod
    def _on_invasion(weak_self, event):
        self = weak_self()
        if not self:
            return
        lane_types = set(x.type for x in event.crossed_lane_markings)
        text = ['%r' % str(x).split()[-1] for x in lane_types]
        self.hud.notification('Crossed line %s' % ' and '.join(text))

# ==============================================================================
# -- GnssSensor --------------------------------------------------------
# ==============================================================================


class GnssSensor(object):
    def __init__(self, parent_actor):
        self.sensor = None
        self._parent = parent_actor
        self.lat = 0.0
        self.lon = 0.0
        world = self._parent.get_world()
        bp = world.get_blueprint_library().find('sensor.other.gnss')
        self.sensor = world.spawn_actor(bp, carla.Transform(carla.Location(x=1.0, z=2.8)), attach_to=self._parent)
        # We need to pass the lambda a weak reference to self to avoid circular
        # reference.
        weak_self = weakref.ref(self)
        self.sensor.listen(lambda event: GnssSensor._on_gnss_event(weak_self, event))

    @staticmethod
    def _on_gnss_event(weak_self, event):
        self = weak_self()
        if not self:
            return
        self.lat = event.latitude
        self.lon = event.longitude


# ==============================================================================
# -- CameraManager -------------------------------------------------------------
# ==============================================================================


class CameraManager(object):
    def __init__(self, parent_actor, hud, gamma_correction):
        self.sensor_actors = None
        self.surfaces = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        #Attachment = carla.AttachmentType
        self.fov = 45
        self.fov_offset = 0.9
        self.side_offset=0.405
        self.pitch_offset = -5
        self._camera_transforms =([
                    carla.Transform(carla.Location(x=-0.45, y=-self.side_offset, z=1.22),carla.Rotation(pitch=self.pitch_offset,yaw=-self.fov - self.fov_offset ,roll=0)),
                    carla.Transform(carla.Location(x=-0.45, y=-self.side_offset, z=1.22),carla.Rotation(pitch=self.pitch_offset,yaw=0                           ,roll=0)),
                    carla.Transform(carla.Location(x=-0.45, y=-self.side_offset, z=1.22),carla.Rotation(pitch=self.pitch_offset,yaw=+self.fov + self.fov_offset ,roll=0))
                ],
                [
                    carla.Transform(carla.Location(x=-0.4, y=self.side_offset, z=1.15),carla.Rotation(yaw=-self.fov - self.fov_offset)),
                    carla.Transform(carla.Location(x=-0.4, y=self.side_offset, z=1.15)),
                    carla.Transform(carla.Location(x=-0.4, y=self.side_offset, z=1.15),carla.Rotation(yaw=+self.fov + self.fov_offset))
                ]
                ) # <= Adjust depending on the model of car we want to display
        self.surfaces_pos = [
            (0,0),
            (hud.dim[0]/3,0),
            (2*hud.dim[0]/3,0)
        ]
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            bp.set_attribute('image_size_x', str(hud.dim[0]/3))
            bp.set_attribute('image_size_y', str(hud.dim[1]))
            bp.set_attribute('fov',str(self.fov))
            if bp.has_attribute('gamma'):
                bp.set_attribute('gamma', str(gamma_correction))

            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None else \
            (force_respawn or (self.sensors[index][0] != self.sensors[self.index][0]))
        if needs_respawn:
            if self.sensor_actors is not None:
                for sensor in self.sensor_actors:
                    sensor.destroy()
                self.surfaces = None
            self.sensor_actors = []
            self.surfaces = []
            for i in range(3):
                self.sensor_actors.append(self._parent.get_world().spawn_actor(
                    self.sensors[index][-1],
                    self._camera_transforms[self.transform_index][i],
                    attach_to=self._parent,
                    attachment_type=carla.AttachmentType.Rigid))
                # We need to pass the lambda a weak reference to self to avoid
                # circular reference.
                weak_self = weakref.ref(self)
                self.surfaces.append(None)
                if i == 0 :
                    self.sensor_actors[i].listen(lambda image: CameraManager._parse_image0(weak_self, image))
                if i == 1 :
                    self.sensor_actors[i].listen(lambda image: CameraManager._parse_image1(weak_self, image))
                if i == 2 :
                    self.sensor_actors[i].listen(lambda image: CameraManager._parse_image2(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surfaces is not None:
            for i in range(3):
                if self.surfaces[i] is not None :
                    display.blit(self.surfaces[i], self.surfaces_pos[i])

    @staticmethod
    def _parse_image0(weak_self, image):
        CameraManager._parse_image(weak_self,image,0)

    @staticmethod
    def _parse_image1(weak_self, image):
        CameraManager._parse_image(weak_self,image,1)

    @staticmethod
    def _parse_image2(weak_self, image):
        CameraManager._parse_image(weak_self,image,2)

    @staticmethod
    def _parse_image(weak_self, image, surface_id):
        self = weak_self()
        if not self:
            return
        
        #image.convert(self.sensors[self.index][1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surfaces[surface_id] = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)

    def destroy(self):
        for sensor in self.sensor_actors:
            sensor.destroy()
            sensor = None
        self.sensor_actors = None
        self.index = None

class FlatCameraManager(object):
    def __init__(self, parent_actor, hud, gamma_correction):
        self.sensor_actor = None
        self.surface = None
        self._parent = parent_actor
        self.hud = hud
        self.recording = False
        bound_y = 0.5 + self._parent.bounding_box.extent.y
        #Attachment = carla.AttachmentType
        #self.fov = 45
        self.fov = math.atan(math.tan((55/180)*math.pi/2.0)*3)*2/math.pi*180
        self.fov_offset = 0.9
        self.side_offset=0.405
        self.pitch_offset = -5
        self._camera_transforms =(
                    carla.Transform(carla.Location(x=-0.45, y=-self.side_offset, z=1.22),carla.Rotation(pitch=self.pitch_offset,yaw=0                           ,roll=0)),
                    carla.Transform(carla.Location(x=-0.45, y=self.side_offset, z=1.22))
                ) # <= Adjust depending on the model of car we want to display
        self.transform_index = 1
        self.sensors = [
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB'],
            ['sensor.camera.rgb', cc.Raw, 'Camera RGB']]
        world = self._parent.get_world()
        bp_library = world.get_blueprint_library()
        for item in self.sensors:
            bp = bp_library.find(item[0])
            bp.set_attribute('image_size_x', str(hud.dim[0]))
            bp.set_attribute('image_size_y', str(hud.dim[1]))
            bp.set_attribute('fov',str(self.fov))
            if bp.has_attribute('gamma'):
                bp.set_attribute('gamma', str(gamma_correction))

            item.append(bp)
        self.index = None

    def toggle_camera(self):
        self.transform_index = (self.transform_index + 1) % len(self._camera_transforms)
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        index = index % len(self.sensors)
        needs_respawn = True if self.index is None else \
            (force_respawn or (self.sensors[index][0] != self.sensors[self.index][0]))
        if needs_respawn:
            if self.sensor_actor is not None:
                self.sensor_actor.destroy()
            self.surface = None
            self.sensor_actor = (self._parent.get_world().spawn_actor(
                self.sensors[index][-1],
                self._camera_transforms[self.transform_index],
                attach_to=self._parent,
                attachment_type=carla.AttachmentType.Rigid))
            # We need to pass the lambda a weak reference to self to avoid
            # circular reference.
            weak_self = weakref.ref(self)
            
            self.sensor_actor.listen(lambda image: FlatCameraManager._parse_image(weak_self, image))
        if notify:
            self.hud.notification(self.sensors[index][2])
        self.index = index

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording
        self.hud.notification('Recording %s' % ('On' if self.recording else 'Off'))

    def render(self, display):
        if self.surface is not None :
            display.blit(self.surface, (0,0))

    @staticmethod
    def _parse_image(weak_self, image):
        self = weak_self()
        if not self:
            return
        
        #image.convert(self.sensors[self.index][1])
        array = np.frombuffer(image.raw_data, dtype=np.dtype("uint8"))
        array = np.reshape(array, (image.height, image.width, 4))
        array = array[:, :, :3]
        array = array[:, :, ::-1]
        self.surface = pygame.surfarray.make_surface(array.swapaxes(0, 1))
        if self.recording:
            image.save_to_disk('_out/%08d' % image.frame)

    def destroy(self):
        self.sensor_actor.destroy()
        self.sensor_actor = None
        self.index = None

class NoCameraManager(object):
    def __init__(self, parent_actor, hud, gamma_correction):
        self.surface = pygame.Surface((200,200))
        self.surface.fill((255,0,0))
        self.index = 1

    def toggle_camera(self):
        self.set_sensor(self.index, notify=False, force_respawn=True)

    def set_sensor(self, index, notify=True, force_respawn=False):
        self.index=0
        #self.surface = pygame.make_surface()

    def next_sensor(self):
        self.set_sensor(self.index + 1)

    def toggle_recording(self):
        self.recording = not self.recording

    def render(self, display):
        if self.surface is not None :
            display.blit(self.surface, (0,0))

    def destroy(self):
        self.index = None

class Mirror(object):
    def __init__(self, parent_actor, dim, pos, topic, world_position, world_rotation, create_sensor, fov,ip=None, port=None,toYUV=False):
        print('INIT MIRROR')
        self._parent = parent_actor
        self.dim = dim
        self.position = pos
        self.surface = None
        self.topic = topic
        self.debug_OnScreenRender = False
        self.sensor = None
        self.view_publisher = None
        self.file_index = 0
        self.ip = ip
        self.port = port
        self.tcp_client = None
        self.toYUV = toYUV
        if create_sensor :
            world = self._parent.get_world()
            bp_library = world.get_blueprint_library()
            bp = bp_library.find('sensor.camera.rgb')
            bp.set_attribute('image_size_x', str(self.dim[0]))
            bp.set_attribute('image_size_y', str(self.dim[1]))
            bp.set_attribute('fov',str(fov))
            bp.set_attribute('sensor_tick',str(1.0/30))
            bp.set_attribute('enable_postprocess_effects',str(True))
            self.sensor = self._parent.get_world().spawn_actor(
                    bp,
                    carla.Transform(
                        carla.Location(x=world_position[0],y=world_position[1], z=world_position[2]),
                        carla.Rotation(pitch=world_rotation[0],yaw=world_rotation[1],roll=world_rotation[2])),
                    attach_to=self._parent,
                    attachment_type=carla.AttachmentType.Rigid)
            self.sensor.listen(lambda image: Mirror._parse_image(self, image))
            self.frame_id = 0
        if(self.debug_OnScreenRender):
            self.surface = pygame.Surface(self.dim)
            self.surface.fill((0,255,0,0))

    def callback(self,img_msg):
        #array = np.reshape(numpy.repeat(img_msg,4), (self.dim[1], self.dim[0],4)) # From 1D to 3D array (width,height,BGRA)
        array = img_msg[:, :, :3] # Gets rid of the alpha channel
        array = array[:, :, ::-1] #Reverse the color order BGR to RGB
        array = np.swapaxes(array, 0, 1)
        array = np.flip(array,0) # Flip X
        self.surface = pygame.surfarray.make_surface(array)

    def setTransform(self,position,rotation):
        print("enter set transform")
        if(self.sensor is not None):
            self.sensor.set_transform(carla.Transform(
                carla.Location(x=position[0],y=position[1], z=position[2]),
                carla.Rotation(pitch=rotation[0],yaw=rotation[1],roll=rotation[2])))
        print("out set transform")

    def render(self,display):
        if(self.debug_OnScreenRender):
            display.blit(self.surface,self.position)

    def _parse_image(self, image):
        array = numpy.ndarray(
                shape=(image.height, image.width, 4),
                dtype=numpy.uint8, buffer=image.raw_data)
        if(self.debug_OnScreenRender):
            self.callback(array)
        if(self.tcp_client is None):
            self.tcp_client = TCP.Client(self.ip,self.port)
        if(self.toYUV):
            #print(YUV.BGRA2YUV(array))
            #self.tcp_client.Send(bytes(YUV.BGRA2YUV(array)))
            self.tcp_client.Send(YUV.BGRA2YUV(array))
        else:
            self.tcp_client.Send(array.tobytes())

    def destroy(self):
        if self.sensor is not None :
            self.sensor.destroy()
            self.sensor = None
            if(self.tcp_client is not None):
                self.tcp_client.Stop()
                self.tcp_client = None



# ==============================================================================
# -- game_loop() ---------------------------------------------------------------
# ==============================================================================

def game_loop(args):

    pygame.init()
    pygame.font.init()
    pygame.mouse.set_visible(False)
    world = None

    try:
        client = carla.Client(args.host, args.port)
        client.set_timeout(2.0)
        
        display = pygame.display.set_mode(
            (args.width, args.height),
            pygame.HWSURFACE | pygame.DOUBLEBUF | 
            ( pygame.FULLSCREEN if args.fullscreen else 0))
        
        hud = HUD(args.width, args.height,(args.mWidth,args.mHeight))
        world = World(client.get_world(), hud, args)
        
        if args.wheel :
            controller = DualControl(world, args.autopilot)
        else :
            controller = KeyboardControl(world, args.autopilot)

        clock = pygame.time.Clock()
        while True:
            clock.tick_busy_loop(90)
            if controller.parse_events(client, world, clock):
                return
            world.tick(clock)
            world.render(display)
            if(running):
                pygame.display.flip()

    finally:

        if (world and world.recording_enabled):
            client.stop_recorder()

        if world is not None:
            world.destroy()

        pygame.quit()
        return


# ==============================================================================
# -- main() --------------------------------------------------------------------
# ==============================================================================


def main():

    argparser = argparse.ArgumentParser(
        description='CARLA Manual Control Client')
    argparser.add_argument(
        '-v', '--verbose',
        action='store_true',
        dest='debug',
        help='print debug information')
    argparser.add_argument(
        '--host',
        metavar='H',
        default='127.0.0.1',
        help='IP of the host server (default: 127.0.0.1)')
    argparser.add_argument(
        '-p', '--port',
        metavar='P',
        default=2000,
        type=int,
        help='TCP port to listen to (default: 2000)')
    argparser.add_argument(
        '-a', '--autopilot',
        action='store_true',
        help='enable autopilot')
    argparser.add_argument(
        '--res',
        metavar='WIDTHxHEIGHT',
        default='200x200',
        help='window resolution (default: 200x200)')
    argparser.add_argument(
        '--filter',
        metavar='PATTERN',
        default='vehicle.*',
        help='actor filter (default: "vehicle.*")')
    argparser.add_argument(
        '--rolename',
        metavar='NAME',
        default='ego_vehicle',
        help='actor role name (default: "hero")')
    argparser.add_argument(
        '--gamma',
        default=2.2,
        type=float,
        help='Gamma correction of the camera (default: 2.2)')
    argparser.add_argument(
        '-w', '--wheel',
        action='store_true',
        help='enable wheel controls'
    )
    argparser.add_argument(
        '--mirror_size',
        default='1280x800',
        help='mirror resolution (default: 1280x800)')
    argparser.add_argument(
        '--fullscreen',
        action='store_true',
        help='Launch the game in fullscreen'
    )
    args = argparser.parse_args()

    args.width, args.height = [int(x) for x in args.res.split('x')]
    args.mWidth, args.mHeight = [int(x) for x in args.mirror_size.split('x')]

    log_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(format='%(levelname)s: %(message)s', level=log_level)

    logging.info('listening to server %s:%s', args.host, args.port)

    print(__doc__)

    try:
        game_loop(args)

    except KeyboardInterrupt:
        print('\nCancelled by user. Bye!')
    
    return


if __name__ == '__main__':

    main()
