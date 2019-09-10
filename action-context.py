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
INTENT_LIGHT_COLOR = "LLUWE19:setColor"
INTENT_LIGHT_BRIGHTNESS = "setBrightness"
INTENT_TV_ON = "LLUWE19:putTvOn"
INTENT_TV_OFF = "LLUWE19:putTvOff"

INTENT_ARRIVE_HOME = "LLUWE19:arriveHome"
INTENT_LEAVE_HOME = "LLUWE19:leaveHome"
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
        self.arriving = True
        self.last_question = None
        self.light_on = False
        self.light_color = None
        self.light_brightness = None
        self.tv_on = False
        self.steward = SnipsHomeManager(self.autho, self.header)

        # start listening to MQTT
        self.start_blocking()

    def turn_light_on(self, hermes, intent_message, rooms):
        """
        Process a command:
        Either turn on a specific choice of light/s or turn on every connected light.
        """
        print("[DEBUG] (turn_light_on)")
        if len(rooms) > 0:
            sentence = "turning on the "
            for room in rooms:
                print("Turning on ", room)
                sentence += " " + room
                self.steward.light_on(room)
            sentence += " lights"
        else:
            sentence = "lights on"
            self.steward.light_on_all()
        hermes.publish_end_session(intent_message.session_id, sentence)

    def turn_light_off(self, hermes, intent_message, rooms):
        """
        Process a command:
        Either turn off a specific choice of light/s or turn off every connected light.
        """
        print("[DEBUG] (turn_light_off)")
        if len(rooms) > 0:
            sentence = "turning off the "
            for room in rooms:
                self.steward.light_off(room)
                sentence += " " + room
            sentence += " lights"
        else:
            self.steward.light_off_all()
            sentence = "lights off"
        hermes.publish_end_session(intent_message.session_id, sentence)

    def set_light_color(self, hermes, intent_message, rooms):
        """
        Process a command:
        Either set the color of a specific choice of light/s or change the color of every connected light.
        """
        print("[DEBUG] (set_light_color)")
        color = self.extract_color(intent_message)
        if len(rooms) > 0:
            sentence = "changing  "
            for room in rooms:
                sentence += " " + room
                self.steward.light_color(room, color)
            sentence += " lights to " + color
        else:
            self.steward.light_color_all(color)
            sentence = "changing lights to " + color
        hermes.publish_end_session(intent_message.session_id, sentence)

    def set_light_brightness(self, hermes, intent_message, rooms):
        """
        Process a command:
        Either change the brightness of a specific choice of light/s or of every connected light.
        """
        print("[DEBUG] set_light_brightness ")
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

    def turn_tv_on(self, hermes, intent_message):
        """
        Process a command:
        Turn the tv on.
        """
        self.steward.tv_on()
        sentence = "TV on"
        hermes.publish_end_session(intent_message.session_id, sentence)

    def turn_tv_off(self, hermes, intent_message):
        """
        Process a command:
        Turn the tv off.
        """
        self.steward.tv_off()
        sentence = "TV off"
        hermes.publish_end_session(intent_message.session_id, sentence)

    def welcome_home(self, hermes, intent_message):
        """
        Begin a conversation:
        Triggered with the "I'm home intent", starts a conversation setting lights and switches in the house.
        """
        print("[DEBUG] (welcome_home)")
        sentence = "welcome home. would you like the lights on"
        self.last_question = sentence
        self.context_commands = False
        self.arriving = True
        hermes.publish_continue_session(intent_message.session_id, sentence, [INTENT_GIVE_ANSWER])

    def good_bye(self, hermes, intent_message):
        """
        Begin a conversation:
        Triggered with the "I'm leaving intent", starts a conversation setting lights and switches in the house.
        """
        print("[DEBUG] (good_bye)")
        sentence = "okay. would you like the lights on"
        self.last_question = sentence
        self.context_commands = False
        self.arriving = False
        hermes.publish_continue_session(intent_message.session_id, sentence, [INTENT_GIVE_ANSWER])

    def conversation(self, hermes, intent_message):
        """
        Becomes the main callback function when the conversation context is triggered (i.e when "context_commands" is false.
        Will ask for a number of user preferences and carry them out at the end of the conversation.
        """
        print("[DEBUG] conversation")
        session_id = intent_message.session_id

        answer = None
        if intent_message.slots.answer:
            answer = intent_message.slots.answer.first().value
            print("The user answered: " + answer)

        if intent_message.slots.color:
            print("message with color")
            self.light_color = intent_message.slots.color.first().value

        if intent_message.slots.percent:
            print("message with brightness")
            self.light_brightness = intent_message.slots.percent.first().value
            # Need to add some error checking to ensure that value is between 0 and 100 percent

        """Registering the users answers"""
        if self.last_question == "welcome home. would you like the lights on" \
                or self.last_question == "okay. would you like the lights on":
            if answer == "yes":
                self.light_on = True
                sentence = "okay. what color do you want the light"
                self.last_question = sentence
                hermes.publish_continue_session(session_id, sentence, [INTENT_LIGHT_COLOR])
            else:
                self.light_on = False
                sentence = "okay. did you want the TV on"
                self.last_question = sentence
                hermes.publish_continue_session(session_id, sentence, [INTENT_GIVE_ANSWER])
        elif self.last_question == "okay. what color do you want the light":
            sentence = "okay. how bright do you want the light"
            self.last_question = sentence
            hermes.publish_continue_session(session_id, sentence, [INTENT_LIGHT_BRIGHTNESS])
        elif self.last_question == "okay. how bright do you want the light":
            sentence = "okay. did you want the TV on"
            self.last_question = sentence
            hermes.publish_continue_session(session_id, sentence, [INTENT_GIVE_ANSWER])
        elif self.last_question == "okay. did you want the TV on":
            if answer == "yes":
                self.tv_on = True
            else:
                self.tv_on = False
            if self.arriving:
                sentence = "okay. welcome home"
            else:
                sentence = "okay. see you later"
            if self.tv_on:
                self.steward.tv_on()
            else:
                self.steward.tv_off()
            if self.light_on:
                self.steward.set_lights_all(self.light_color, self.light_brightness)
            else:
                self.steward.light_off_all()
            self.context_commands = True
            self.last_question = sentence
            hermes.publish_end_session(session_id, sentence)

    def master_intent_callback(self,hermes, intent_message):
        """
        Callback function to provide extra processing and routing for either commands or conversations.
        Commands or conversations are managed using the "context_commands" boolean. E.g. if the "context_commands" is
        true, then the system is in command mode and will listen and execute intents that issue commands. (turn light on).
        If it is false it will continue to call back the conversation function until the conversation has been
        processed.
        """
        rooms = self.extract_house_rooms(intent_message)
        intent_name = intent_message.intent.intent_name
        print("[DEBnUG] (master_intent_callback) intent_name: " + intent_name)
        if self.context_commands:
            print("[DEBUG] (master_intent_callback) In command mode")
            if intent_name == INTENT_LIGHT_ON:
                self.turn_light_on(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_OFF:
                self.turn_light_off(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_COLOR:
                self.set_light_color(hermes, intent_message, rooms)
            elif intent_name == INTENT_LIGHT_BRIGHTNESS:
                self.set_light_brightness(hermes, intent_message, rooms)
            elif intent_name == INTENT_TV_ON:
                self.turn_tv_on(hermes, intent_message)
            elif intent_name == INTENT_TV_OFF:
                self.turn_tv_off(hermes, intent_message)
            elif intent_name == INTENT_ARRIVE_HOME:
                self.welcome_home(hermes, intent_message)
            elif intent_name == INTENT_LEAVE_HOME:
                self.good_bye(hermes, intent_message)
        else:
            print("[DEBUG] (master_intent_callback) Conversation mode")
            self.conversation(hermes, intent_message)

    def start_blocking(self):
        """
        Subscribe and start listening to the MQTT broker
        """
        with Hermes(MQTT_ADDR) as h:
            print("Start Blocking")
            h.subscribe_intents(self.master_intent_callback).start()

    def extract_house_rooms(self, intent_message):
        """
        Extracts the rooms which the user has specified in the intent message
        :param intent_message:
        :return: A list of rooms
        """
        house_rooms = []
        if intent_message.slots.house_room:
            for room in intent_message.slots.house_room.all():
                type(room.value)
                house_rooms.append(room.value)
        return house_rooms

    def extract_percentage(self, intent_message, default_percentage):
        """
        Extracts a percentage from a percent slot in an intent message. Used for changing lights brightness.
        :param intent_message:
        :param default_percentage:
        :return: a double, percentage
        """
        percentage = default_percentage
        if intent_message.slots.percent:
            percentage = intent_message.slots.percent.first().value
        if percentage < 0:
            percentage = 0
        if percentage > 100:
            percentage = 100
        return percentage

    def extract_color(self, intent_message):
        """
        Extracts the color specified from the user in the intent_messages slot.
        :param intent_message:
        :return: string, color name
        """
        color_code = None
        if intent_message.slots.color:
            color_code = intent_message.slots.color.first().value
        return color_code


if __name__ == "__main__":
    HomeManager()

