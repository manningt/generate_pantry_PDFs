# make_reports.py
import os
from fpdf import FPDF, table
from PyPDF2 import PdfMerger # pyrefly: ignore [missing-import]
from defines import GUEST_LIST_IDX_E, FRIDAY_IDX, SATURDAY_IDX, Table_def_deliveries_by_route
import csv
import xlsxwriter # pyrefly: ignore [missing-import]

def normalize_phone_number(number):
   import re
   clean_number = re.sub("[^0-9]", "", str(number))
   if len(clean_number) != 10:
      print(f"bad phone number: {clean_number}")
   return f'{clean_number[:3]}.{clean_number[3:6]}.{clean_number[6:]}'

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

   #72 points = 1 inch;  612 points across page
   pdf.set_margins(40, 24, 2) #left, top, right in points - 40 pix = .5"
   widths = table_def.column_widths
   if table_def.number_of_columns == 1:
      widths = table_def.column_widths
   elif table_def.number_of_columns == 2:
      if len(guest_list) > table_def.number_of_rows_on_a_page:
         widths = table_def.column_widths + [table_def.center_spacer_width] + table_def.column_widths
   else:
      print(f"Unsupported number of columns: {table_def.number_of_columns}; either 1 or 2")
      return
   
   # print(f"{sum(widths)=} {widths=}")
   # print(f"Generating {pdf_report_filename} {report_title=}: ", end="")
   current_row = 0
   guest_list_page_number = 0

   if table_def.number_of_columns == 2:
      page_count = (len(guest_list) // (table_def.number_of_rows_on_a_page * 2)) + 1
   else:
      page_count = (len(guest_list) // table_def.number_of_rows_on_a_page) + 1

   skipped_second_column = 0
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
            # make dual data columns
            for _ in range(table_def.number_of_rows_on_a_page):
               pdf_table_row = table.row()
               this_guest = guest_list[current_row].copy()
               del this_guest[0] # delete client_id
               # print(f"{this_guest}", end="")
               for idx, item in enumerate(this_guest):
                  pdf.set_font("Helvetica",  size=int(table_def.column_font[idx]))
                  pdf_table_row.cell(str(item))

               second_column_guest_index = current_row + table_def.number_of_rows_on_a_page
               # print(f"{second_column_guest_index=} {len(guest_list)}")
               if table_def.number_of_columns == 2:
                  if second_column_guest_index < len(guest_list):
                     pdf_table_row.cell("", border=0) # center row
                     this_guest = guest_list[second_column_guest_index].copy()
                     del this_guest[0] # delete client_id
                     # print(f"{this_guest} ", end="")
                     for idx, item in enumerate(this_guest):
                        pdf.set_font("Helvetica",  size=int(table_def.column_font[idx]))
                        pdf_table_row.cell(str(item))
                  else:
                     skipped_second_column += 1
               current_row += 1
               if current_row >= len(guest_list):
                  # print(f"\t  End of guest list reached at {current_row=}.")
                  break
         if table_def.number_of_columns == 2:
            current_row += table_def.number_of_rows_on_a_page # skip to next set of rows
            
   except Exception as e:
      status_string = f"Failure: while making table for {pdf_report_path} exception: {e}"
      return status_string
   
   if table_def.number_of_columns == 2:
      if current_row % table_def.number_of_rows_on_a_page:
         guest_count = current_row - table_def.number_of_rows_on_a_page
      else:
         guest_count = current_row - skipped_second_column
   else:
      guest_count = current_row

   try:
      pdf.output(pdf_report_path)
      # status_string = f"{pdf_report_path} has {len(guest_list)} guests."
   except Exception as e:
      print(f"failed to generate {pdf_report_path} exception: {e}")
      return False

   print(f"{pdf_report_filename} has {guest_count} guests on {guest_list_page_number} pages")
   return True


def write_counts_csv(guest_list, output_directory, csv_filename):
   #              visit_with_bags = [visit_tuple[0], "", bags, pickup_time, first_name, last_name, item_count, phone]
   # delivery_with_bags_list.append([visit_tuple[0], "", bags, route, first_name, last_name, item_count, phone])
   I_BAGS = 2
   I_TIME_ROUTE = 3
   I_FIRST = 4
   I_LAST = 5
   I_ITEMS = 6

   visit_array   = [['Bags', 'Labels', 'Items', 'First', 'Last', 'Time/Route']]
   for tuple in guest_list:
      visit_array.append(["",tuple[I_BAGS], tuple[I_ITEMS], tuple[I_FIRST], tuple[I_LAST], tuple[I_TIME_ROUTE]])

   csv_path = os.path.join(output_directory, csv_filename)
   with open(csv_path, 'w', newline='') as csvfile:
      writer = csv.writer(csvfile)
      writer.writerows(visit_array)

   print(f'{csv_filename} has {len(visit_array)-1} guests')


def write_delivery_routes_pdf(deliveries_list, output_directory, pdf_filename, client_info, this_weeks_date, routes_to_print):
   if len(deliveries_list) == 0:
      print("Failure: no guest lists in request to generate PDF report on tag files.")
      return False

   # delivery_with_bags_list.append([visit_tuple[0], "", bags, route, first_name, last_name, item_count, phone])
   I_CLIENT_ID = 0
   I_ROUTE = 3
   I_FIRST = 4
   I_LAST = 5
   I_PHONE = 7

   guests_on_route_list = []
   pdf_filename_list = []

   for route_to_print_number in routes_to_print:
      guests_on_route_list = []
      for visit_tuple in deliveries_list:
         this_guests_route_number = visit_tuple[I_ROUTE].split(":")[0]
         if this_guests_route_number == route_to_print_number:
            client_id = visit_tuple[I_CLIENT_ID]
            street = client_info[client_id][4]             
            unit = client_info[client_id][5]
            guest_info = [client_id, "", visit_tuple[I_FIRST], visit_tuple[I_LAST], street, unit, visit_tuple[I_PHONE]]         
            guests_on_route_list.append(guest_info)
            full_route_name = visit_tuple[I_ROUTE] #need to save this for page title

      if len(guests_on_route_list):
         report_header = f"Deliveries for   {full_route_name}    for {this_weeks_date[0][-5:]}     "
         route_pdf_filename = f"route_{route_to_print_number}.pdf"
         write_report_pdf(guests_on_route_list, report_header, "/tmp", route_pdf_filename, Table_def_deliveries_by_route())
         pdf_filename_list.append(route_pdf_filename)

   # merge the PDFs per route
   merger = PdfMerger()
   for pdf in pdf_filename_list:
      merger.append(os.path.join("/tmp", pdf))
   merger.write(os.path.join(output_directory, pdf_filename))
   merger.close()

   # for pdf in pdf_filename_list:
   #    try:
   #       os.remove(os.path.join("/tmp", pdf))
   #    except OSError:
   #       pass

def write_driver_timing_schedule(guest_list, output_directory, output_filename):
   routes_dict = {}  # just the route number before the colon
   route_name_dict = {}
   total_deliveries_count = 0

   # delivery_with_bags_list.append([visit_tuple[0], "", bags, route, first_name, last_name, item_count, phone])
   for visit_tuple in guest_list:
      visit_route = visit_tuple[3].split(': ')[0]
      if visit_route not in routes_dict:
         routes_dict[visit_route] = 1
         route_name_dict[visit_route] = visit_tuple[3].split(': ')[1]
      else:
         routes_dict[visit_route] += 1
      total_deliveries_count += 1

   routes_list = list(routes_dict.items())
   routes_list.sort()
   route_with_name_list = []
   for route_set in routes_list:
      route_with_name_list.append([route_set[0], route_name_dict[route_set[0]], route_set[1]])
   # print(f"{route_with_name_list}")

   # insert header:
   header = ['Route', 'Route Name', 'Orders', \
      'Minutes to complete','Completion Time','First Order Out', \
      'Orders Complete','Vehicle/Driver','Driver arrival']
   route_with_name_list.insert(0, header)
   route_with_name_list.append(["",'Total', total_deliveries_count])

   filename_path = os.path.join(output_directory, output_filename)
   workbook = xlsxwriter.Workbook(filename_path) 

   header_format = workbook.add_format({'bold': True})
   header_format.set_font_name('Arial')
   header_format.set_font_size(12)
   header_format.set_text_wrap()
   # print(f"{header_format}")

   text_format = workbook.add_format()
   text_format.set_font_name('Arial')
   text_format.set_font_size(12)

   worksheet = workbook.add_worksheet()
   for row_number, content in enumerate(route_with_name_list):
      if row_number == 0:
         worksheet.write_row(row_number, 0, content, header_format)
      else:
         worksheet.write_row(row_number, 0, content, text_format)

   column_widths = [6,18,7,10,11,10,10,10,10]
   for column_number, column_width in enumerate(column_widths):
      worksheet.set_column(column_number, column_number, column_width) #, text_format)

   workbook.close()
   print(f'{output_filename} has {total_deliveries_count} guests on {len(route_name_dict)} routes')



#previous implementation which has embedded formatting and data lookup
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
