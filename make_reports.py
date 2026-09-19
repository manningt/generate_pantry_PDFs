# make_reports.py
from defines import SATURDAY_IDX
import os
from fpdf import FPDF, table
from defines import GUEST_LIST_IDX_E, FRIDAY_IDX, SATURDAY_IDX

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

   pickup_list = [[],[]]
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
         last_name = client_info[client_id][1][:20]
         phone = normalize_phone_number(client_info[client_id][3])
         if g_l_index == GUEST_LIST_IDX_E.Pickup_Saturday.value:
            pickup_list[SATURDAY_IDX].append([visit_tuple[2][:5],first_name,last_name, phone])
         else:
            pickup_list[FRIDAY_IDX].append([visit_tuple[2][1:5],first_name,last_name, phone])
   # print(f"{len(pickup_list[FRIDAY_IDX])=} {len(pickup_list[SATURDAY_IDX])=}")

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
   bag_width = 26
   route_time_width = 38
   first_name_width = 62
   last_name_width = 74
   phone_width = 78
   widths = (bag_width, route_time_width, first_name_width, last_name_width, phone_width, \
      center_spacer_width, bag_width, route_time_width, first_name_width, last_name_width, phone_width)
   # print(f"there are {len(widths)} columns with a total width of {sum(widths)} pixels; should not exceed {printable_pixels} pixels")

   guest_list_page_number = 0
   page_count = ((len(pickup_list[FRIDAY_IDX]) + len(pickup_list[SATURDAY_IDX])) // (number_of_rows_on_a_page * 2)) + 1
   for day_index, days_list in enumerate(pickup_list):
      current_guest = 0
      while current_guest < len(days_list):
         try:
            pdf.add_page()
            guest_list_page_number += 1
            pdf.set_font("Helvetica", "B", size=11)
            pdf.cell(0,0, f'Pickup expeditor for {this_weeks_date[day_index][-4:]}       Page {guest_list_page_number} of {page_count}', align="C")
            pdf.ln(pdf.font_size+4)
            pdf.set_font("Helvetica", "", size=12)

            with pdf.table(line_height=24, padding=1, width=sum(widths), col_widths=widths) as table:
               pdf_table_row = table.row()
               # header row
               for column_title in header:
                  pdf_table_row.cell(column_title)
               if (len(days_list) - current_guest) > number_of_rows_on_a_page:
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
                  pdf_table_row.cell("") #bags
                  pdf.set_font("Helvetica", "", size=14)
                  pdf_table_row.cell(days_list[current_guest][0], align="R") #time
                  pdf.set_font("Helvetica", "", size=12)
                  pdf_table_row.cell(days_list[current_guest][1]) #first name
                  pdf.set_font("Helvetica", "", size=14)
                  pdf_table_row.cell(days_list[current_guest][2]) #last
                  pdf.set_font("Helvetica", "", size=12)
                  pdf_table_row.cell(days_list[current_guest][3]) #phone
                  # second column
                  second_column_guest = current_guest + number_of_rows_on_a_page
                  if second_column_guest < len(days_list):
                     # print(f"\t  {current_guest=} {days_list[current_guest]}\n\t\t {second_column_guest=} {days_list[second_column_guest]}")
                     pdf_table_row.cell("", border=0) #center spacer
                     pdf_table_row.cell("") #bags, align="R")
                     pdf.set_font("Helvetica", "", size=14)
                     pdf_table_row.cell(days_list[second_column_guest][0], align="R")
                     pdf.set_font("Helvetica", "", size=12)
                     pdf_table_row.cell(days_list[second_column_guest][1])
                     pdf.set_font("Helvetica", "", size=14)
                     pdf_table_row.cell(days_list[second_column_guest][2])
                     pdf.set_font("Helvetica", "", size=12)
                     pdf_table_row.cell(days_list[second_column_guest][3])
                  else:
                     for _ in range(len(header)):
                        pdf_table_row.cell("", border=0)   
                  current_guest += 1
                  if current_guest >= len(days_list):
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

def write_expeditor_2column_pdf2(guest_list_list, output_directory, expeditor_pdf_filename, client_info, this_weeks_date):
   #
   # NOTE: only supports Pickup guests
   #
   if len(guest_list_list) == 0:
      print("Failure: no guest lists in request to generate PDF report on tag files.")
      return False

   delivery_list = []
   # print(f"\nGenerating {pdf_report_path}: {len(guest_list_list)} guest lists.")

   route_set = set([])

   for visit_tuple in guest_list_list[GUEST_LIST_IDX_E.Delivery.value]:
      # visit_tuple pickup:   client_id, item_count, time, last_name, first_name)
      # visit_tuple delivery: client_id, item_count, None, delivery_route, last_name)
      # client_info_dict[client_id] =[first, last, delivery_route, phone, street_address, unit_no, city]
      # if visit_tuple[2] is None:
      #    print(f"Make expeditor PDF Error: Pickup time is missing for {visit_tuple=}")
      #    continue
      client_id = str(visit_tuple[0])
      if client_id not in client_info:
         print(f"Make expeditor PDF Error: {client_id} missing for {visit_tuple=}")
         continue
      first_name = client_info[client_id][0]
      last_name = client_info[client_id][1][:20]
      route_set.add(client_info[client_id][2])
      route = client_info[client_id][2].replace(" - ", ": ").replace("- ", ": ").replace(" and ", " & ")
      route = route.replace("West","W")
      route = route.replace("NBPT ","Nbpt-")
      route = route.replace("Newbury","Nwbry")
      route = route[:19]
      delivery_list.append([route,first_name,last_name])

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
   header = ["Bag", "Route", "First", "Last"]
   bag_width = 26
   route_time_width = 120
   first_name_width = 62
   last_name_width = 74
   # phone_width = 78
   widths = (bag_width, route_time_width, first_name_width, last_name_width, \
      center_spacer_width, bag_width, route_time_width, first_name_width, last_name_width)
   # print(f"there are {len(widths)} columns with a total width of {sum(widths)} pixels; should not exceed {printable_pixels} pixels")

   guest_list_page_number = 0
   delivery_list_len = len(delivery_list)
   page_count = (delivery_list_len // (number_of_rows_on_a_page * 2)) + 1
   current_guest = 0
   while current_guest < delivery_list_len:
      try:
         pdf.add_page()
         guest_list_page_number += 1
         pdf.set_font("Helvetica", "B", size=11)
         pdf.cell(0,0, f'Delivery expeditor for {this_weeks_date[0][-4:]}       Page {guest_list_page_number} of {page_count}', align="C")
         pdf.ln(pdf.font_size+4)
         pdf.set_font("Helvetica", "", size=12)

         with pdf.table(line_height=24, padding=1, width=sum(widths), col_widths=widths) as table:
            pdf_table_row = table.row()
            # header row
            for column_title in header:
               pdf_table_row.cell(column_title)
            if (delivery_list_len - current_guest) > number_of_rows_on_a_page:
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
               pdf_table_row.cell("") #bags
               pdf.set_font("Helvetica", "", size=12)
               pdf_table_row.cell(delivery_list[current_guest][0]) #time
               pdf_table_row.cell(delivery_list[current_guest][1]) #first name
               pdf.set_font("Helvetica", "", size=14)
               pdf_table_row.cell(delivery_list[current_guest][2]) #last
               # second column
               second_column_guest = current_guest + number_of_rows_on_a_page
               if second_column_guest < delivery_list_len:
                  # print(f"\t  {current_guest=} {days_list[current_guest]}\n\t\t {second_column_guest=} {days_list[second_column_guest]}")
                  pdf_table_row.cell("", border=0) #center spacer
                  pdf_table_row.cell("") #bags, align="R")
                  pdf.set_font("Helvetica", "", size=12)
                  pdf_table_row.cell(delivery_list[second_column_guest][0])
                  pdf_table_row.cell(delivery_list[second_column_guest][1])
                  pdf.set_font("Helvetica", "", size=14)
                  pdf_table_row.cell(delivery_list[second_column_guest][2])
               else:
                  for _ in range(len(header)):
                     pdf_table_row.cell("", border=0)   
               current_guest += 1
               if current_guest >= delivery_list_len:
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

   route_list = sorted(route_set)
   with open('output_files/route_list.txt', mode='wt', encoding='utf-8') as myfile:
      myfile.write('\n'.join(route_list))
   return True

def write_report_pdf(guest_list, report_title, output_directory, pdf_report_filename, table_def):
   if len(guest_list) == 0:
      print("Failure: no guest lists in request to generate PDF report on tag files.")
      return False
   
   pdf_report_path = os.path.join(output_directory, pdf_report_filename)
   try:
      pdf = FPDF(orientation="portrait", unit="pt", format="letter")
   except Exception as e:
      print(f"Failure: could not create PDF for {pdf_report_path} exception: {e}")
      return False

   #72 points = 1 inch;
   pdf.set_margins(12, 24, 12) #left, top, right in points
   widths = table_def.column_widths
   if table_def.number_of_columns == 1:
      pass
   elif table_def.number_of_columns == 2:
      if len(guest_list) > table_def.number_of_rows_on_a_page:
         widths.append(table_def.center_spacer_width)
         widths.extend(table_def.column_widths)
   else:
      print(f"Unsupported number of columns: {table_def.number_of_columns}; either 1 or 2")
      return
   
   # print(f"{sum(widths)=} {widths=}")
   print(f"\nGenerating {pdf_report_path}: {len(guest_list)} guest lists. {report_title=}")
   current_row = 0
   guest_list_page_number = 0
   page_count = (len(guest_list) // (table_def.number_of_rows_on_a_page * 2)) + 1
   try:
      while current_row < len(guest_list):
         pdf.add_page()
         guest_list_page_number += 1
         pdf.set_font("Helvetica", "B", size=14)
         pdf.cell(0,0, f'{report_title}      Page {guest_list_page_number} of {page_count}', align="L")
         pdf.ln(pdf.font_size+4)
         pdf.set_font("Helvetica", "B", size=12)
         with pdf.table(align="L", line_height=pdf.font_size, padding=2, width=sum(widths), col_widths=widths) as table:
            pdf_table_row = table.row()
            for column_title in table_def.header:
               pdf_table_row.cell(column_title)
            if table_def.number_of_columns == 2 and len(guest_list) > table_def.number_of_rows_on_a_page:
               # print("Adding 2nd column")
               pdf_table_row.cell("", border=0) # spacer
               for column_title in table_def.header:
                  pdf_table_row.cell(column_title)
            pdf.set_font("Helvetica")
            # make dual data columns
            for _ in range(table_def.number_of_rows_on_a_page):
               pdf_table_row = table.row()
               this_guest = guest_list[current_row].copy()
               del this_guest[0] # delete client_id
               for idx, item in enumerate(this_guest):
                  pdf.set_font("Helvetica",  size=int(table_def.column_font[idx]))
                  pdf_table_row.cell(str(item))

               second_column_guest_index = current_row + table_def.number_of_rows_on_a_page
               if table_def.number_of_columns == 2 and second_column_guest_index <= len(guest_list):
                  pdf_table_row.cell("", border=0) # center row
                  this_guest = guest_list[second_column_guest_index].copy()
                  del this_guest[0] # delete client_id
                  for idx, item in enumerate(this_guest):
                     pdf.set_font("Helvetica",  size=int(table_def.column_font[idx]))
                     pdf_table_row.cell(str(item))
               current_row += 1
               if current_row >= len(guest_list):
                  print(f"\t  End of guest list reached at {current_row=}.")
                  break
         current_row += table_def.number_of_rows_on_a_page # skip to next set of rows
            
   except Exception as e:
      status_string = f"Failure: while making table for {pdf_report_path} exception: {e}"
      return status_string
      
   try:
      pdf.output(pdf_report_path)
      # status_string = f"{pdf_report_path} has {len(guest_list)} guests."
   except Exception as e:
      print(f"failed to generate {pdf_report_path} exception: {e}")
      return False

   return True
