import json
import requests as rq


class SnipsHomeManager:
    """
    Whereas the "action-home-manager" describes the logic and handles the interactions with snips,
    the SnipsHomeManager manages functions that carry out the intents specified by the user.
    The "action-home-manager" will call the appropriate functions from SnipsHomeManager who makes the
    appropriate API request. The SnipsHomeManager in this case is made mostly of calls to the Hass API
    to manage lights and switches.

    The functions in this manager depend on a corresponding naming convention for the Hass entities.
    E.g. each light entity must follow "light.roomname_light"
    """
    def __init__(self, autho, header):
        print("Created the snips home manager")
        self.autho = autho  # Hass API key
        self.header = header  # Header required for REST API
        self.api_address = 'http://192.168.0.136:8123/api/'

    def light_on(self, room):
        """
        Ask Hass to turn on a specific light.
        :param room: String, name of the room
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "light.{}_light".format(room)
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_on_all(self):
        """
        Ask Hass to turn on all of the lights
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "all"
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_off(self, room):
        """
        Asks Hass to turn off a specific light
        :param room: String, room to turn lights off
        :return: None
        """
        url = self.api_address + 'services/light/turn_off'
        body = {
            "entity_id": "light.{}_light".format(room)
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_off_all(self):
        """
        Ask Hass to turn off all of the lights
        :return: None
        """
        url = self.api_address + 'services/light/turn_off'
        body = {
            "entity_id": "all",
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_color(self, room, color):
        """
        Ask Hass to change a specific lights color
        :param room: String, room to change light color
        :param color: String, human readable name of a color e.g. red, blue
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "light.{}_light".format(room),
            "color_name": color
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_color_all(self, color):
        """
        Ask Hass to change all of the lights colors
        :param color:
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "all",
            "color_name": color
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_brightness(self, room, brightness):
        """
        Ask Hass to set a specific lights brightness
        :param room: String, room to change lights brightness
        :param brightness: Int, percentage, how bright the light should be
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "light.{}_light".format(room),
            "brightness": brightness
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def light_brightness_all(self, brightness):
        """
        Ask Hass to change all of the lights brightness
        :param brightness: Int, percentage, how bright the lights should be
        :return: None
        """
        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "all",
            "brightness": brightness
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def shift_light_up(self, room, percent):
        """
        Ask Hass to make a specific light brighter.
        Asks Hass for the current light brightness, then adds on the specified brightness
        :param room: String, room to change lights brightness
        :param percent: Int, percentage, amount to increase the lights brightness
        :return: None
        """
        url = self.api_address + 'states/light.{}_light'.format(room)
        request = rq.get(url, headers=self.header)
        print(request.text)
        response = request.json()
        current_brightness = response['attributes']['brightness']

        new_brightness = current_brightness + percent

        if new_brightness < 0:
            new_brightness = 0
        if new_brightness > 100:
            new_brightness = 100

        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "light.{}_light".format(room),
            "brightness": new_brightness
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def shift_light_up_all(self, percent):
        """
        !!!!!!NEEDS IMPLEMENTATION!!!!!!
        Ask Hass to make the lights brighter.
        :param percent: Int, percentage, amount to increase the lights brightness
        :return: None
        """

    def shift_light_down(self, room, percent):
        """
        Ask Hass to make a specific light dimmer.
        Asks Hass for the current light brightness, then subtracts the specified brightness
        :param percent: Int, percentage, amount to decrease the lights brightness
        :return: None
        """
        url = self.api_address + 'states/light.{}_light'.format(room)
        request = rq.get(url, headers=self.header)
        print(request.text)
        response = request.json()
        current_brightness = response['attributes']['brightness']

        new_brightness = current_brightness - percent

        if new_brightness < 0:
            new_brightness = 0
        if new_brightness > 100:
            new_brightness = 100

        url = self.api_address + 'services/light/turn_on'
        body = {
            "entity_id": "light.{}_light".format(room),
            "brightness": new_brightness
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def shift_light_down_all(self, room, percent):
        """
        !!!!!!NEEDS IMPLEMENTATION!!!!!!
        Ask Hass to make the lights dimmer
        :param percent: Int, percentage, amount to decrease the lights brightness
        :return: None
        """

    def tv_on(self):
        """
        Ask Hass to turn the tv on.
        Could be modified for multiple tvs
        :return: None
        """
        url = self.api_address + 'services/switch/turn_on'
        body = {
            "entity_id": "switch.living_room_tv",
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)

    def tv_off(self):
        """
        Ask Hass to turn the tv off
        :return: None
        """
        url = self.api_address + 'services/switch/turn_off'
        body = {
            "entity_id": "switch.living_room_tv",
        }
        json_body = json.dumps(body)
        request = rq.post(url, data=json_body, headers=self.header)