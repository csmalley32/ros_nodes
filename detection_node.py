#!/usr/bin/python
from collections import namedtuple
import sys
# import time
import numpy as np
import random
import rospy
# import logging
# import math
import json
from shapely.geometry import LineString, Point
# from ros_nodes.msg import line, Point2D
from sensor_msgs.msg import LaserScan
from threading import Thread
from geometry_msgs.msg import Polygon, Point32
# from rospy.exceptions import ROSInterruptException
# from geometry_msgs.msg import Twist
# import tf
# from robot-motion-planning import utils


def mergeLines(lines, threshold):  # {{{1
    # Check mahalanobis distance less that thresh
    pass


def clusterLaserscan(laserscan, threshold=1, min_points=10):  # {{{1
    # if there is difference in distance greater than thresh
    # break into two clusters
    if not laserscan:
        return laserscan
    clusters = []
    p_prev = laserscan[0]
    i_prev = 0
    for i, p in enumerate(laserscan):
        dist = p.distance(p_prev)
        if dist > threshold:
            clusters.append(laserscan[i_prev:i])
            i_prev = i
        p_prev = p
    clusters = [c for c in clusters if len(c) > min_points]
    return clusters


def SplitAndMerge(laserscan, threshold=3):  # {{{1
    """
    inputs: laser scan
    outputs: list of lines
    """
    pass


# Ransac  {{{1
def Ransac(laserscan,
           numpoints=4,
           iterations=100,
           threshold=4,
           ratio=0.3):
    """
    inputs: laser scan
    outputs: list of lines
    """
    bestLine = None
    bestError = 999999
    for i in range(iterations):
        # PICK RANDOM POINTS
        points = []
        points.append(random.randint(0, len(laserscan) - 1))
        for i in range(numpoints):
            tmp = random.randint(0, len(laserscan) - 1)
            while tmp in points:
                tmp = random.randint(0, len(laserscan) - 1)
            points.append(tmp)
        points.sort()
        # GET LINE PARAMETERS
        tmpline = LineString([laserscan[p] for p in points])
        # FIND INLIERS
        inliers = []
        for p in laserscan:
            dist = p.distance(tmpline)
            if dist < threshold:
                inliers.append(p)
        if len(inliers) > (len(laserscan) * ratio):
            # CALCULATE ERROR OF MODEL
            error = sum([p.distance(tmpline) for p in laserscan])
            if error < bestError:
                bestError = error
                bestLine = tmpline
    return bestLine


class RosDetectionNode(Thread):  # {{{1

    """
    Create a ROS node that implements a object detection algorithms
    inputs: All inputs should be from from sensors? (camera, lidar..)
    outputs: Outputs should be obstacles (type TBD)
    """

    def __init__(self, descr):  # {{{2
        Thread.__init__(self)
        self.state = "init"
        self.name = descr["name"]
        # SET UP RATE FOR LOOP
        self.rate = rospy.Rate(10)  # TODO add to config
        # SET UP PUBLISHING
        self.pub = rospy.Publisher(descr["publishtopic"]['name'],
                                   # publish_topic['topic'])
                                   Polygon)
        # SET UP SUBSCRIBING
        for topic in descr["subscribetopics"]:
            rospy.Subscriber(topic['name'],
                             LaserScan,
                             self.laserScanCallback)
        self.laserscan = []
        # SET UP ALGORITHM FOR NODE
        # self.run()

    def run(self):  # {{{2
        self.state = "running"
        while not rospy.is_shutdown() or self.state == "stop":
            # data = self.policy.step()
            clusters = clusterLaserscan(self.laserscan)
            lines = []
            for cluster in clusters:
                tmpline = Ransac(cluster)
                lines.append(tmpline)
            self.publishObjects(self.pub, lines)
            self.rate.sleep()
        self.stop()
        return

    def stop(self):  # {{{2
        self.state = "stop"
        print("Stopping: ", self.name)

    # Callback functions {{{2
    def cameraCallback(self, data):  # {{{3
        pass

    def laserScanCallback(self, data):  # {{{3
        angleMin = data.angle_min
        inc = data.angle_increment
        phi = angleMin
        self.laserscan = []
        for i, d in enumerate(data.ranges):
            if d == data.range_max:
                continue
            phi = angleMin + inc * i
            rho = d
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            p = Point(x, y)
            self.laserscan.append(p)

    # Publish functions {{{2
    def publishObjects(self, pub, data):  # {{{3
        publine = []
        for obj in data:
            points = list(obj.coords)
            for point in points:
                # tmp = Point2D(x=point[0], y=point[1])
                tmp = Point32(x=point[0], y=point[1])
                publine.append(tmp)
        pub.publish(publine)


# Main function.
if __name__ == '__main__':  # {{{1
    # LOAD CONFIG FILE
    configfilename = sys.argv[1]
    with open(configfilename) as f:
        descr = json.load(f)
    publish_topic = descr["publishtopic"]
    print("publishtopic: ", publish_topic)
    subscribe_topics = descr["subscribetopics"]
    print("subscribetopics: ", subscribe_topics)
    # Initialize the node and name it.
    rospy.init_node(descr['name'])
    model = line
    try:
        ne = RosDetectionNode(subscribe_topics, publish_topic, model)
    except rospy.ROSInterruptException:
        pass
