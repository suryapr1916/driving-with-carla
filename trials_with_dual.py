import glob
import os
import sys
import time


import carla

import random
import numpy as np
import cv2
import pygame
from pygame.locals import *



IM_WIDTH = 200
IM_HEIGHT = 150

# function teleport vehicle to colect data with noise
def add_noise_teleport(vehicle):

    transform = vehicle.get_transform()

    if np.absolute(vehicle.get_control().steer) < 0.02 and np.absolute(transform.rotation.pitch) < 1:

        print(transform.location)

        angle = transform.rotation.yaw * np.pi / 180.
        print(angle)
        distance = (np.random.random() * 2 - 1) * 1.9         # distance -1.5 m < d < 1.5 m
        #distance = 1.5

        location = carla.Location(transform.location.x + np.sin(angle) * distance, transform.location.y + np.cos(angle) * distance, transform.location.z)
        rotation = carla.Rotation(transform.rotation.pitch, transform.rotation.yaw + (np.random.random() * 2 - 1) * 5, transform.rotation.roll)

        #print(np.absolute(transform.rotation.pitch))
        print(location)
        vehicle.set_transform(carla.Transform(location, rotation))



# function procces data for storing
def process_img(image, training_data, vehicle, display):
    raw_image = np.array(image.raw_data)
    image_bgra = raw_image.reshape((IM_HEIGHT, IM_WIDTH, 4))
    image_bgr = image_bgra[:, :, :3]
    #cv2.imshow("", image_bgr)
    #cv2.waitKey(20)
    r_image_bgr = np.transpose(image_bgr, axes = (1,0,2))

    rsurface = pygame.surfarray.make_surface(r_image_bgr)
    display.blit(rsurface, (0, 0))


    our_vehicle_controll = vehicle.get_control()
    throttle = our_vehicle_controll.throttle
    steer = our_vehicle_controll.steer


    text_surface_throttle = myfont.render('throtlee: '+str(throttle), False, (0, 0, 0))
    text_surface_steer = myfont.render('steer: '+str(steer), False, (0, 0, 0))

    display.blit(text_surface_throttle, (20, 20))
    display.blit(text_surface_steer, (20, 50))
    pygame.display.flip()

    #print(np.absolute(vehicle.get_transform().rotation.yaw))

    control = [throttle, steer]
    training_data.append([image_bgr,control])

    if len(training_data) % 25 == 0:
        print(len(training_data))


# defining Carla client
client = carla.Client('localhost', 2000)
client.set_timeout(2.0)

# get world and set some weather
world = client.get_world()
weather = carla.WeatherParameters(
    cloudiness=10.0,
    precipitation=10.0,
    sun_altitude_angle=70.0)
world.set_weather(weather)


# set all traffic to green
traffic_lights = world.get_actors().filter('traffic.traffic_light')
for traffic_light in traffic_lights:
    traffic_light.set_state(carla.TrafficLightState.Green)
    traffic_light.freeze(True)

# create actor and vehicle list
actor_list = []
vehicle_list = []

# get all blueprints
blueprint_library = world.get_blueprint_library()
# get all vehicles blueprints
vehicles = blueprint_library.filter('vehicle.*')

# get all spawn points
spawn_points = world.get_map().get_spawn_points()

# get random spawn point
spawn_point = random.choice(spawn_points)

# get model 3 from vehicles blueprints
vehicle_bp = blueprint_library.filter('model3')[0]

# spawn vehicle
vehicle = world.spawn_actor(vehicle_bp, spawn_point)

# set autopilot
vehicle.set_autopilot(True)

# add vehicle to actor list
actor_list.append(vehicle)

# get blueprint of left and right rgb cameras
camera_bp = blueprint_library.find('sensor.camera.rgb')
camera_bp.set_attribute('image_size_x', f'{IM_WIDTH}')
camera_bp.set_attribute('image_size_y', f'{IM_HEIGHT}')
camera_bp.set_attribute('fov', '90')

# spawn left camera
camera_transform = carla.Transform(carla.Location(x=1.5, z=2.4))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
actor_list.append(camera)

# spawn right camera
camera_transform = carla.Transform(carla.Location(x=-1.5, z=2.4))
camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
actor_list.append(camera)

# start driving the car
vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))

# visualize with cv2
pygame.init()
display = pygame.display.set_mode((IM_WIDTH, IM_HEIGHT), pygame.HWSURFACE | pygame.DOUBLEBUF)
myfont = pygame.font.SysFont('Comic Sans MS', 30)
