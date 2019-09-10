#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from snipsTools import SnipsConfigParser
from hermes_python.hermes import Hermes
from hermes_python.ontology import *
from snips_home_manager import SnipsHomeManager
from enum import Enum
import io

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

MQTT_IP_ADDR = "192.168.0.136"
MQTT_PORT = 1883
MQTT_ADDR = "{}:{}".format(MQTT_IP_ADDR, str(MQTT_PORT))

INTENT_LIGHT_ON = "turnOn"
INTENT_LIGHT_OFF = "turnOff"
INTENT_LIGHT_COLOR = "setColor"
INTENT_LIGHT_BRIGHTNESS = "setBrightness"

INTENT_ARRIVE_HOME = "arriveHome"
INTENT_LEAVE_HOME = "leaveHome"
INTENT_GIVE_ANSWER = "LLUWE19:giveAnswer"


class HomeManager(object):
    """
    The HomeManager is used to manage the discussion between Snips and Hass via MQTT (using Hermes).
    The HomeManager listens for intents and implements the logic to carry out required actions. The HomeManager passes
    on the actual task of calling Hass services and communicating with Hass onto the "SnipsHomeManager" who makes calls
    to the Hass REST API via HTTP.
    """
    def __init__(self):
        print("Loading HomeManager")
        try:
            self.config = SnipsConfigParser.read_configuration_file(CONFIG_INI)
        except:
            self.config = None
            print("[Warning] No config file")
        self.autho = self.config['secret']['http_api_token']
        self.header = {
            'Authorization': self.autho,
            "Content-Type": "application/json",
        }
        self.context_commands = True
        self.last_question = None
        self.light_on = False
        self.light_color = None
        self.light_brightness = None
        self.steward = SnipsHomeManager(self.autho, self.header)

        # start listening to MQTT
        self.start_blocking()

    def turn_light_on(self, hermes, intent_message, rooms):
        if len(rooms) > 0:
            sentence = "Turning on the "
            for room in rooms:
                print("Turning on ", room)
                sentence += " " + room
                self.steward.light_on(room)
            sentence += " lights"
        else:
            sentence = "Turning on all the lights"
            self.steward.light_on_all()
        hermes.publish_end_session(intent_message.session_id, sentence)

    def turn_light_off(self, hermes, intent_message, rooms):
        if len(rooms) > 0:
            sentence = "Turning off the "
            for room in rooms:
                self.steward.light_off(room)
                sentence += " " + room
            sentence += " lights"
        else:
            self.steward.light_off_all()
            sentence = "Turning off all the lights"
        hermes.publish_end_session(intent_message.session_id, sentence)

    def set_light_color(self, hermes, intent_message, rooms):
        color = self.extract_color(intent_message)
        if len(rooms) > 0:
            sentence = "changing  "
            for room in rooms:
                sentence += " " + room
                self.steward.light_color(room, color)
            sentence += " lights to " + color
        else:
            self.steward.light_color_all(color)
            sentence = "changing color for all lights "
        hermes.publish_end_session(intent_message.session_id, sentence)

    def set_light_brightness(self, hermes, intent_message, rooms):
        percent = self.extract_percentage(intent_message, None)
        if percent is None:
            sentence = "Did not specify the brightness"
            hermes.publish_end_session(intent_message.session_id, sentence)
        if len(rooms) > 0:
            sentence = "Setting  "
            for room in rooms:
                self.steward.light_brightness(room, percent)
                sentence += " " + room
            sentence += " lights to " + str(percent)
        else:
            self.steward.light_brightness_all(percent)
            sentence = "Setting light brightness to " + str(percent)
        hermes.publish_end_session(intent_message.session_id, sentence)

    def start_conversation(self, hermes, intent_message):
        sentence = "welcome home. would you like the lights on"
        self.last_question = sentence
        self.context_commands = False
        hermes.publish_continue_session(intent_message.session_id, sentence, [INTENT_GIVE_ANSWER])

    def conversation(self, hermes, intent_message):
        session_id = intent_message.session_id

        answer = None
        if intent_message.slots.answer:
            answer = intent_message.slots.answer.first().value
            print("The user answered: " + answer)

        if intent_message.slots.color:
            print("message with color")
            self.light_color = intent_message.slots.color.first().value

        if intent_message.slots.percentage:
            print("message with brightness")
            self.light_brightness = intent_message.slots.percentage.first().value
            # Need to add some error checking to ensure that value is between 0 and 100 percent

        """Registering the users answers"""
        if self.last_question == "welcome home. would you like the lights on":
            if answer == "yes":
                self.light_on = True
                sentence = "okay. what color do you want the light"
                self.last_question = sentence
                hermes.publish_continue_session(session_id, sentence, [INTENT_LIGHT_COLOR])
            else:
                self.light_on = False
                sentence = "okay. welcome home"
                self.last_question = sentence
                self.context_commands = True
                hermes.publish_end_session(session_id, sentence)

        elif self.last_question == "okay. what color do you want the light":
            sentence = "okay. how bright do you want the light"
            self.last_question = sentence
            hermes.publish_continue_session(session_id, sentence, [INTENT_LIGHT_BRIGHTNESS])

        elif self.last_question == "okay. how bright do you want the light":
            print("User responded with brightness")
            sentence = "okay. welcome home"
            self.context_commands = True
            self.last_question = sentence
            hermes.publish_end_session(session_id, sentence)

    def master_intent_callback(self,hermes, intent_message):
        rooms = self.extract_house_rooms(intent_message)
        intent_name = intent_message.intent.intent_name
        print("[DEBUG] " + intent_name)
        if ':' in intent_name:
            intent_name = intent_name.split(":")[1]
            print("[DEBUG] intent_name: " + intent_name)

        if self.context_commands:
            print("In command mode")
            if intent_name == INTENT_LIGHT_ON:
                self.turn_light_on(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_OFF:
                self.turn_light_off(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_COLOR:
                self.set_light_color(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_BRIGHTNESS:
                self.set_light_brightness(hermes, intent_message, rooms)
            elif intent_name == INTENT_ARRIVE_HOME:
                self.start_conversation(hermes, intent_message)
        else:
            print("Conversation mode")
            self.conversation(hermes, intent_message)

    def start_blocking(self):
        with Hermes(MQTT_ADDR) as h:
            print("Start Blocking")
            h.subscribe_intents(self.master_intent_callback).start()

    def extract_house_rooms(self, intent_message):
        house_rooms = []
        if intent_message.slots.house_room:
            for room in intent_message.slots.house_room.all():
                type(room.value)
                house_rooms.append(room.value)
        return house_rooms

    def extract_percentage(self, intent_message, default_percentage):
        percentage = default_percentage
        if intent_message.slots.percent:
            percentage = intent_message.slots.percent.first().value
        if percentage < 0:
            percentage = 0
        if percentage > 100:
            percentage = 100
        return percentage

    def extract_color(self, intent_message):
        color_code = None
        if intent_message.slots.color:
            color_code = intent_message.slots.color.first().value
        return color_code

    def extract_scene(self, intent_message):
        scene_code = None
        if intent_message.slots.scene:
            scene_code = intent_message.slots.scene.first().value
        return scene_code


if __name__ == "__main__":
    HomeManager()

