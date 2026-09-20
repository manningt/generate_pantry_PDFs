
from defines import GUEST_LIST_IDX_E
from make_reports import normalize_phone_number
from make_bag_tags_and_report import item_count_to_label_count

#columns:
#2-column:
# tags_for_all_guests:  First Last Time/Route Items  -> sorted by last, first or route, last; 2 column
# pickup: empty, Bags, Time, First, Last, phone   -> sorted by time, last, first; 2 column
#1-column:
# delivery: empty, Bags, Route, First, Last, ?phone -> sorted by route, last, first
# delivery_per_route : Bags, First, Last, Street, Unit, Phone

# Driver_Timing: route #, route name, # orders, Minutes to complete	Completion TIME	First Order Out	Orders Complete	Vehicle/Driver	Driver arrival

def move_delivery_to_pickup(guest_list_list, route_time_tuple_list, client_info):
   # the route_time_tuple specifies which route to match, and what time the pickup is to be
   # it then returns a modified guest_list_list with the matched route moved to a pickup time

   pickup_by_name_list = []
   pickup_by_time_list = []
   delivery_with_item_list = []
   delivery_with_bags_list = []
   # visit_tuple pickup:   client_id, item_count, time, last_name, first_name)
   # visit_tuple delivery: client_id, item_count, None, delivery_route, last_name)
   # route_time_tuple_list = [('Quak','03:45')]
 
   for g_l_index in range(len(guest_list_list)):
      for visit_tuple in guest_list_list[g_l_index]:
         client_id = str(visit_tuple[0])
         if client_id not in client_info:
            print(f"Visit error: {client_id} missing for {visit_tuple=}")
            continue
         first_name = client_info[client_id][0]
         phone = normalize_phone_number(client_info[client_id][3])
         item_count = visit_tuple[1]
         bags = item_count_to_label_count(item_count)
         
         if g_l_index == GUEST_LIST_IDX_E.Delivery.value:
            last_name = visit_tuple[4][:19] # has asterisk in last name for priority
            # move from delivery to pickup:  example route tuple: [('Quak','03:45')]
            for route_time_tuple in route_time_tuple_list:
               # test if route of visit is equal to one of the 
               if route_time_tuple[0] in visit_tuple[3]:
                  # replace 'None' with pickup time and first name with route name
                  # first_name_route_name = visit[3].split("- ")[1][9]
                  moved_visit_with_items = [visit_tuple[0], first_name, last_name, route_time_tuple[1], item_count]
                  pickup_by_name_list.append(moved_visit_with_items)
                  moved_visit_with_bags = [visit_tuple[0], "", bags, route_time_tuple[1], first_name, last_name, item_count, phone]
                  pickup_by_time_list.append(moved_visit_with_bags)
                  break
               else:
                  route = visit_tuple[3].replace(" - ",": ").replace("- ",": ")[:25]
                  delivery_with_item_list.append([visit_tuple[0], first_name[:8], last_name[:13], route[:7], item_count])
                  delivery_with_bags_list.append([visit_tuple[0], "", bags, route, first_name, last_name, item_count, phone])
         else:
            last_name = client_info[client_id][1][:19]
            pickup_time = visit_tuple[2][:5]
            # Saturday pickups will naturally sort to the end when sorting by time since they are 8 to 12.
            visit_with_items = [visit_tuple[0], first_name[:8], last_name[:13], pickup_time, item_count]
            pickup_by_name_list.append(visit_with_items)
            visit_with_bags = [visit_tuple[0], "", bags, pickup_time, first_name, last_name, item_count, phone]
            pickup_by_time_list.append(visit_with_bags)
      
   # for i, visit in enumerate(pickup_by_name_list):
   #    print(f"{visit} ", end="")
   #    if i > 3: print(); break

   pickup_by_name_list.sort(key=lambda x: (x[1], x[2]))  #sort by last_name, first_name
   pickup_by_time_list.sort(key=lambda x: (x[3], x[2]))  #sort by time, last_name

   delivery_with_item_list.sort(key=lambda x: (x[3], x[2], x[1]))  #sort by delivery_route, last_name, first name
   delivery_with_bags_list.sort(key=lambda x: (x[3], x[5]))  #sort by delivery_route, last_name 

   return pickup_by_name_list, pickup_by_time_list, delivery_with_item_list, delivery_with_bags_list
