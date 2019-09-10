import requests as rq
import json
import time
import io


# url = 'http://192.168.0.136:8123/api/states/light/'
# autho = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE4ODIyNzYxMjQsImlhdCI6MTU2NjkxNjEyNCwiaXNzIjoiN2ZiMTNlNTBhYWYyNDQ1NWIxZmY5MjZmMjU2N2E4M2MifQ.bcrR8dSTYdFfTOfsnpem2dS15vvEMMAsgeK-RgnofPs'
# headers = {
#             'Authorization': autho,
#             'content-type': 'application/json',
#           }
#
# response = rq.get(url, headers=headers)
#
# print(response)
#


contexts = {
    "arrive_home": False,
    "at_home": False,
    "leaving_home": False,
    "out_home": False
}


if contexts['arrive_home']:
    print("True")

print(contexts)
# resp = response.json()
#
# print(resp)
#
# brightness = resp['attributes']['brightness']
#
# print(brightness)
#
# print("Brightness: ", brightness)