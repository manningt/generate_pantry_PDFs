import enum

FRIDAY_IDX = 0
SATURDAY_IDX = 1
FRIDAY_SPLIT_REPORT_HOUR = 3 # the time in the afternoon to split into before/after pickup lists

class GUEST_LIST_IDX_E(enum.Enum): 
   Pickup_Friday_before_3 = 0
   Pickup_Friday_after_3 = 1
   Pickup_Saturday = 2
   Delivery = 3

# used in report generation:
DELIVERY_TYPE = 'Delivery'  # used for delivery guest lists
AM_PM_TYPE = 'AM_PM'  # used for AM/PM guest lists

class Table_def_pickup_by_name:
   number_of_columns = 2
   number_of_rows_on_a_page = 40
   header = ["First", "Last", "Time", "Items"]
   column_widths = [64, 90, 54, 36]
   column_font = [12, 12, 12, 12]
   center_spacer_width = 50

class Table_def_delivery_expeditor:
   number_of_columns = 1
   number_of_rows_on_a_page = 39
   header = ["Bag", "Bags","Route", "First", "Last", "Items", "Phone"]
   column_widths = [30, 34, 190, 72, 84, 36, 90]
   column_font = [14, 14, 14, 14, 14, 14, 14]
   center_spacer_width = 0 # unused

class Table_def_delivery_2column:
   number_of_columns = 2
   number_of_rows_on_a_page = 38
   header = ["First", "Last", "Route", "Items"]
   column_widths = [64, 90, 54, 36]
   column_font = [12, 12, 12, 12]
   center_spacer_width = 40
