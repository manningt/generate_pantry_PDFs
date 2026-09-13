#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.13"
# dependencies = [
#   "requests",
# ]
# ///

from get_guests_visits import load_token
import time as unix_time
import requests
import json

'''
The following code was in generator.py to get a list of guests with landlines:
   Test registration GET:
      with open("my-priority.json", "r") as fp:
         clients_with_priority_list = json.load(fp)
      get_registrations(pantrysoft_token, clients_with_priority_list)

   Get the latest client registrations for all clients:
      make_priority_landline_lists(pantrysoft_token, client_info_dict)

   Make a list of all landline phone numbers:
      with open("my-landlines.json", "r") as fp:
         landline_client_info_dict = json.load(fp)
      for client_id in landline_client_info_dict:
         print(f"{client_info_dict[client_id][3]} {client_info_dict[client_id][1]} {client_info_dict[client_id][0]}")
'''

'''
currently used as a prototype for testing registration data
   inputs is the client_id_list - which is a dictionary of client_id's and client data items
   iterates through the client_list dictionary and gets the most recent registration data
   returns nothing
   prints out 2 lists: clients with priority, clients with landline.  These were copied into a json file

   1 run showed:
      the following client_id's without registration data:  818, 1186, 1236, 1258, 1321
      the following output for performance:
         done: 829 guest's registrations retrieved in 346.30 seconds; average_per_page=2.39
'''
def make_priority_landline_lists(token, client_info_dict):

   PRINT_CLIENTS_WITHOUT_REGISTRATIONS = False

   clients_with_priority = {}
   clients_with_landlines = {}

   # https://app.pantrysoft.com/api/v1/registration/?limit=1&sort=registrationDatetime&order=DESC&client_id=109'
   url = "https://app.pantrysoft.com/api/v1/registration/"
   params = {
      "client_id": 0,
      "limit": 1,
      "sort": "registrationDatetime",
      "order": "DESC",
   }
   headers = {
      "accept": "application/json",
      "X-Auth-Token": token
   }

   query_count = 0
   start_time = unix_time.time()
   # print('Fetching registrations per client', end='', flush=True)
   for client_id, value in client_info_dict.items():
      # print(f"{client=}")
      params["client_id"] = client_id
      response = requests.get(url, headers=headers, params=params)
      if response.status_code != 200:
         print(f"Request failed with status code {response.status_code}")
         print(response.text)
         exit()

      query_count += 1
      response_list = response.json()
      # print(f"{client[0]} {response_list['data'][0]['registration_questions']['Priority']}")
      try:
         questions = response_list['data'][0]['registration_questions']
      except:
         if PRINT_CLIENTS_WITHOUT_REGISTRATIONS:
            print(f"{client_id} does not have registration_questions.")
         continue
      if 'Priority' in questions:
         has_priority = questions['Priority']
      else:
         has_priority = False

      if 'registration_cell' in questions:
         if questions['registration_cell'].lower() == "yes":
            is_landline = False
         else:
            is_landline = True
      else:
         print(f"{client_id} {value[0]} does not have registration_cell in questions, assuming cell")
         is_landline = False

      # print(f"{client_id} {value[0]} {value[1]} {has_priority=} {is_landline=}")
      if has_priority:
         clients_with_priority[client_id] = value[1]
         # break
      if is_landline:
         clients_with_landlines[client_id] = [value[1], value[0]]

      if query_count % 100 == 0:
         print(f'{query_count} queries; {len(clients_with_priority)=} {len(clients_with_landlines)=}')

      # client_info_dict, clients_added_count = parse_client_response(response_list['data'], client_info_dict)

      # print(' .', end='', flush=True)
   # print(f'Priority: {len(clients_with_priority)}: {clients_with_priority}')
   # print(f'/nLandlines: {len(clients_with_landlines)}: {clients_with_landlines}')
   elapsed_time = unix_time.time() - start_time
   average_time_per_page = query_count/elapsed_time
   print(f" done: {query_count} guest's registrations retrieved in {elapsed_time:.2f} seconds; average_per_page={average_time_per_page:.2f}", flush=True)

   return clients_with_priority, clients_with_landlines

'''
currently used as a prototype for testing registration data
   inputs are a list of tuples with last_name, client_id.  The last_name is just for print outs
      exmaple priority_list = [["Kriajeva", 370], ["Reynoso", 109], ["Mirzayee", 401]]
   returns nothing
   prints out whether a client has a landline and/or priority
'''
def get_registrations(token, priority_list):
   
   # https://app.pantrysoft.com/api/v1/registration/?limit=1&sort=registrationDatetime&order=DESC&client_id=109'
   url = "https://app.pantrysoft.com/api/v1/registration/"
   params = {
      "client_id": 0,
      "limit": 1,
      "sort": "registrationDatetime",
      "order": "DESC",
   }
   headers = {
      "accept": "application/json",
      "X-Auth-Token": token
   }

   start_time = unix_time.time()
   # print('Fetching registrations per client', end='', flush=True)
   for client in priority_list:
      params["client_id"] = client[1]
      response = requests.get(url, headers=headers, params=params)
      if response.status_code != 200:
         print(f"Request failed with status code {response.status_code}")
         print(response.text)
         exit()

      response_list = response.json()
      # print(f"{client[0]} {response_list['data'][0]['registration_questions']['Priority']}")
      questions = response_list['data'][0]['registration_questions']
      if 'Priority' in questions:
         has_priority = questions['Priority']
      else:
         has_priority = False

      if 'registration_cell' in questions:
         if questions['registration_cell'].lower() == "yes":
            is_landline = False
         else:
            is_landline = True
      else:
         print(f"{client[0]} id={client[1]} does not have registration_cell in questions, assuming cell")
         is_landline = False

      print(f"{client[0]} id={client[1]} {has_priority=} {is_landline=}")

      # print(' .', end='', flush=True)
      elapsed_time = unix_time.time() - start_time
      average_time_per_page = len(priority_list)/elapsed_time
      # print(f' done: {len(client_info_dict)} active guests retrieved in {elapsed_time:.2f} seconds; average_per_page={average_time_per_page:.2f}', flush=True)

   return

def compare_json_dictionaries(current_json, new_json):
   with open(current_json, "r") as fp:
      current_dict = json.load(fp)

   with open(new_json, "r") as fp:
      new_dict = json.load(fp)

   # print(f"{current_dict=}\n{new_dict=}")
   # return

   same_dict = True
   for key, value in current_dict.items():
      if key not in new_dict:
         print(f"{key}: {value} not in {new_json}")
         same_dict = False
      elif value != new_dict[key]:
         print(f"value differences for {key}: Current={value}  Updated={new_dict[key]}")
         same_dict = False

   for key, value in new_dict.items():
      if key not in current_dict:
         print(f"{key}: {value} added in {new_json}")
         same_dict = False

   if same_dict:
      print("{new_json} is equal to {current_json}")


if __name__ == "__main__":
   CURRENT_GUESTS_WITH_PRIORITY_FILENAME = "my-priority.json"
   UPDATED_GUESTS_WITH_PRIORITY_FILENAME = "my-priority-update.json"
   CLIENT_LIST_FILENAME = "my-guests.json"
   TOKEN_FILENAME = "my-pantrysoft_token.json"

   try:
      pantrysoft_token = load_token(TOKEN_FILENAME)
   except:
      print(f"Quitting: failed to load {TOKEN_FILENAME}.")
      exit()

   try:
      with open(CLIENT_LIST_FILENAME, "r") as fp:
         client_info_dict = json.load(fp)
      print(f'Using saved guest/client file {CLIENT_LIST_FILENAME} which has {len(client_info_dict)} guests', flush=True)
   except:
      print(f"Quitting: failed to load {CLIENT_LIST_FILENAME}")
      exit()

   clients_with_priority, clients_with_landlines = make_priority_landline_lists(pantrysoft_token, client_info_dict)
   try:
      with open(UPDATED_GUESTS_WITH_PRIORITY_FILENAME, "w") as fp:
         json.dump(clients_with_priority , fp)
   except:
      print(f"Failed to write {UPDATED_GUESTS_WITH_PRIORITY_FILENAME}")
      exit()

   compare_json_dictionaries(CURRENT_GUESTS_WITH_PRIORITY_FILENAME, UPDATED_GUESTS_WITH_PRIORITY_FILENAME)
