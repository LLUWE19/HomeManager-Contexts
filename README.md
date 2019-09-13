## Home Manager
Use this as a Snips skill/ action to control the lights and TV.

Makes use of 2 'modes', command mode and conversation mode. Whilst in command mode one line commands can be made e.g. "hey snips, turn the bedroom light off". The conversation mode is triggered using intents like "hey snips, im home" or "hey snips, im leaving". Whilst in this mode Snips will ask a series of questions to manage the state of the home e.g. lights on? how bright? what color? tv on? It will then carry out the requests.

This skill is also open to device expansion. E.g. any lights can be added to Home Assistant and will work with this skill. The requirement is that the entity_id follows the name of the room. E.g. kitchen_light, or garden_light, as will extract the first work in the entity_id and match it to the intent_messages slot. 
