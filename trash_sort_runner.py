# import RPi.GPIO as GPIO
from gpiozero import AngularServo, MotionSensor
from ultralytics import YOLO

import random
import requests
import subprocess
import time


# Pin numbers are subject to change
MOTION_SENSOR_PIN = 4
TRASH_SERVO_PIN = 23
RECYCLE_SERVO_PIN = 24
COMPOST_SERVO_PIN = 25

IMAGE_PATH = "image0.jpg"
TEXT_FILE_PATH = "data.txt"

# Global Vars
pir = MotionSensor(MOTION_SENSOR_PIN)
host = "http://54.185.46.227:5000/"
g_trash = 0
g_recycle = 0
g_compost = 0

"""
Main runner function for the program

:param: None
:return: None
"""


def main() -> None:
    while True:
        # wait for motion to be detected before doing anything
        print("Waiting for motion")
        pir.wait_for_motion()
        start = time.time()
        print("Motion detected, taking picture now")

        # Take a picture of the objects
        take_picture()

        # ML model predicts what is being seen and that
        # object is being classified as either trash, compost, or recycle
        prediction = ml_predict()
        if (prediction is not None):
            trash_type = classify_object(prediction)
            if trash_type != "None":
                print("Throw your " + prediction + " into " + trash_type)
                open_bin(trash_type)
                send_to_aws()
            else:
                print("Do not throw")
        else:
            print("Nothing detected")
            continue

        print("Time elasped: " + str(time.time() - start))
        pir.wait_for_no_motion()
        # time.sleep(5)


"""
Function that calls the ML model and identifies what was seen

:param: None
:return: String of object that is detected
"""


def ml_predict() -> str:
    model = YOLO('yolov8s.pt')
    results = model.predict(IMAGE_PATH)
    result = results[0]

    try:
        box1 = result.boxes[0]

        return result.names[box1.cls[0].item()]
    except:
        return None


"""
Helper function that classifies objects as either trash, recyclable, or compostable

:param object_name: String that contains the identified object
:return: Category of trash
"""


def classify_object(object_name) -> str:
    recycle = ["bottle", "cup", "wine glass"]
    compost = ["banana", "apple", "donut"]
    trash = ["spoon", "knife", "backpack"]
    if object_name in recycle:
        return "recycle"
    elif object_name in compost:
        return "compost"
    elif object_name in trash:
        return "trash"
    return "None"


"""
Helper function that opens a bin lid by controlling a servo

:param bin_name: Name of the bin that needs to be opened
:return: None
"""


def open_bin(bin_name: str) -> None:
    global g_trash
    global g_recycle
    global g_compost
    bin = bin_name.lower()

    if bin == "compost":
        print("compost")
        compost_servo = AngularServo(COMPOST_SERVO_PIN, min_angle=-180, max_angle=0)
        compost_servo.max() # open
        time.sleep(10)
        compost_servo.min() # close
        time.sleep(3)
        g_compost += 1

    elif bin == "recycle":
        recycle_servo = AngularServo(RECYCLE_SERVO_PIN, min_angle=-180, max_angle=0)
        print("recycle")
        recycle_servo.min()
        time.sleep(10)
        recycle_servo.max()
        time.sleep(3)
        g_recycle += 1

    else:
        print("trash")
        trash_servo = AngularServo(TRASH_SERVO_PIN, min_angle=0, max_angle=180)
        trash_servo.min()
        time.sleep(10)
        trash_servo.max()
        time.sleep(3)
        g_trash += 1

    print("stop")


"""
Helper function that calls libcamera through the CLI
Resulting image is saved in a hardcoded location

:param: None
:return: None
"""


def take_picture() -> None:
    subprocess.run(['libcamera-still -o image0.jpg'], shell=True)


"""
Function that handles http requests to be sent to AWS

:param: None
:return: None
"""


def send_to_aws() -> None:
    json = {'trash': g_trash, 'recycle': g_recycle, 'compost': g_compost}
    status = requests.post(host+"/data", json=json)
    code = status.status_code
    if code == 200:
        print("No issues")
    elif code == 404:
        print("Not found")
    else:
        print("Error occured. Status code: " + str(code))
        print(status.text)


"""
Function that logs data into a text file

:param: None
:returns: None
"""


def write_to_text() -> None:
    with open(TEXT_FILE_PATH, "a") as file:
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        file.write(time_now)
        file.write("\n")
        file.write("Trash: " + str(g_trash) + "\n")
        file.write("Recycle: " + str(g_recycle) + "\n")
        file.write("Compost: " + str(g_compost) + "\n\n")


"""
Generates random numbers to test the format of write_to_text()

:param: None
:returns None
"""


def test_write() -> None:
    global g_trash
    global g_recycle
    global g_compost
    for _ in range(2):
        g_trash = random.randint(1, 10)
        g_recycle = random.randint(1, 10)
        g_compost = random.randint(1, 10)
        write_to_text()


"""
Tester function to test how the servo works

:param: None
:returns: None
"""
def turn_servo() -> None:
    compost_servo = AngularServo(COMPOST_SERVO_PIN, min_angle=-180, max_angle=0)
    print("min")
    compost_servo.min()
    time.sleep(5)
    print("mid")
    compost_servo.mid()
    time.sleep(5)
    print("max")
    compost_servo.max()
    time.sleep(5)
    print("mid")
    compost_servo.mid()
    time.sleep(5)
    print("min")
    compost_servo.min()
    time.sleep(5)

if __name__ == "__main__":
    main()
