# make_reports.py
import os
from fpdf import FPDF
from defines import GUEST_LIST_IDX_E

def normalize_phone_number(number):
   import re
   clean_number = re.sub("[^0-9]", "", str(number))
   if len(clean_number) != 10:
      print(f"bad phone number: {clean_number}")
   return f'{clean_number[:3]}.{clean_number[3:6]}.{clean_number[6:]}'


def write_expeditor_2column_pdf(guest_list_list, output_directory, expeditor_pdf_filename, client_info, this_weeks_date):
   #
   # NOTE: only supports Pickup guests
   #
   if len(guest_list_list) == 0:
      print("Failure: no guest lists in request to generate PDF report on tag files.")
      return False

   pickup_list = []
   # print(f"\nGenerating {pdf_report_path}: {len(guest_list_list)} guest lists.")
   for g_l_index in range(len(guest_list_list)):
      if g_l_index == GUEST_LIST_IDX_E.Delivery.value:
         continue

      for visit_tuple in guest_list_list[g_l_index]:
         # visit_tuple pickup:   client_id, item_count, time, last_name, first_name)
         # visit_tuple delivery: client_id, item_count, None, delivery_route, last_name)
         # client_info_dict[client_id] =[first, last, delivery_route, phone, street_address, unit_no, city]
         if visit_tuple[2] is None:
            print(f"Make expeditor PDF Error: Pickup time is missing for {visit_tuple=}")
            continue
         client_id = str(visit_tuple[0])
         if client_id not in client_info:
            print(f"Make expeditor PDF Error: {client_id} missing for {visit_tuple=}")
            continue
         first_name = client_info[client_id][0]
         last_name = client_info[client_id][1]
         phone = normalize_phone_number(client_info[client_id][3])
         pickup_list.append([visit_tuple[2][:5],first_name,last_name, phone])

   first_guest_on_saturday_index = \
      len(guest_list_list[GUEST_LIST_IDX_E.Pickup_Friday_before_3.value]) + \
         len(guest_list_list[GUEST_LIST_IDX_E.Pickup_Friday_after_3.value])
   # print(f'{pickup_list[first_guest_on_saturday_index]=}')

   pdf_report_path = os.path.join(output_directory, f'{expeditor_pdf_filename}')
   try:
      pdf = FPDF(orientation="portrait", unit="pt", format="letter")
   except Exception as e:
      print(f"Failure: could not create PDF for {pdf_report_path} exception: {e}")
      return False

   side_margins = 8
   pdf.set_margins(side_margins, 24, side_margins) #left, top, right in points
   printable_pixels = (8.5*72)-(2*side_margins)
   #72 points = 1 inch;  page minus margins is 596 pixels wide
   number_of_rows_on_a_page = 20
   center_spacer_width = 20
   header = ["Bag", "Time", "First", "Last", "Phone"]
   bag_width = 30
   route_time_width = 38
   first_name_width = 60
   last_name_width = 72
   phone_width = 78
   widths = (bag_width, route_time_width, first_name_width, last_name_width, phone_width, \
      center_spacer_width, bag_width, route_time_width, first_name_width, last_name_width, phone_width)
   # print(f"there are {len(widths)} columns with a total width of {sum(widths)} pixels; should not exceed {printable_pixels} pixels")


   guest_list_page_number = 0
   current_guest = 0
   page_count = (len(pickup_list) // (number_of_rows_on_a_page * 2)) + 1
   doing_saturday_pickups = False
   while current_guest < len(pickup_list):
      try:
         pdf.add_page()
         guest_list_page_number += 1
         pdf.set_font("Helvetica", "B", size=11)
         pdf.cell(0,0, f'Pickup expeditor for {this_weeks_date[0][-4:]} & {this_weeks_date[1][-4:]}     Page {guest_list_page_number} of {page_count}', align="C")
         pdf.ln(pdf.font_size+4)
         pdf.set_font("Helvetica", "", size=12)

         with pdf.table(line_height=24, padding=1, width=sum(widths), col_widths=widths) as table:
            pdf_table_row = table.row()
            # header row
            for column_title in header:
               pdf_table_row.cell(column_title)
            if (len(pickup_list) - current_guest) > number_of_rows_on_a_page:
               # only make second column if there is enough data
               pdf_table_row.cell("", border=0) # spacer
               for column_title in header:
                  pdf_table_row.cell(column_title)
            else:
               for _ in range(len(header)):
                  pdf_table_row.cell("", border=0)

            # make dual data columns
            for row_count in range(number_of_rows_on_a_page):
               pdf_table_row = table.row()
               # first column
               pdf_table_row.cell("") #bags, align="R")
               pdf.set_font("Helvetica", "", size=14)
               pdf_table_row.cell(pickup_list[current_guest][0]) #time
               pdf.set_font("Helvetica", "", size=12)
               pdf_table_row.cell(pickup_list[current_guest][1]) #first
               pdf.set_font("Helvetica", "", size=14)
               pdf_table_row.cell(pickup_list[current_guest][2]) #last
               pdf.set_font("Helvetica", "", size=12)
               pdf_table_row.cell(pickup_list[current_guest][3]) #phone
               # second column
               second_column_guest = current_guest + number_of_rows_on_a_page
               if second_column_guest <= len(pickup_list):
                  pdf_table_row.cell("", border=0) #center spacer
                  pdf_table_row.cell("") #bags, align="R")
                  pdf.set_font("Helvetica", "", size=14)
                  pdf_table_row.cell(pickup_list[second_column_guest][0])
                  pdf.set_font("Helvetica", "", size=12)
                  pdf_table_row.cell(pickup_list[second_column_guest][1])
                  pdf.set_font("Helvetica", "", size=14)
                  pdf_table_row.cell(pickup_list[second_column_guest][2])
                  pdf.set_font("Helvetica", "", size=12)
                  pdf_table_row.cell(pickup_list[second_column_guest][3])
               else:
                  for _ in range(len(header)):
                     pdf_table_row.cell("", border=0)   
               current_guest += 1
               if current_guest >= len(pickup_list):
                  # print(f"\t  End of guest list reached at {current_row=}.")
                  break
         current_guest += number_of_rows_on_a_page # skip to next set of rows on a new page
               
      except Exception as e:
         status_string = f"Failure: while making table for {pdf_report_path} exception: {e}"
         print(status_string)
         return status_string
      
   try:
      pdf.output(pdf_report_path)
   except Exception as e:
      #    current_app.logger.warning(f"PDF for {guest} failed: {e}")
      print(f"failed to generate {pdf_report_path} exception: {e}")
      return False
   return True
