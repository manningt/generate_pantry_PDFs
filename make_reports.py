# make_reports.py
import os
from fpdf import FPDF, table
from PyPDF2 import PdfMerger # pyrefly: ignore [missing-import]
from defines import FRIDAY_IDX, SATURDAY_IDX, Table_def_deliveries_by_route, Table_def_saturday_staging
import csv
import xlsxwriter # pyrefly: ignore [missing-import]
import math

#              visit_with_bags = [visit_tuple[0], "", "", bags, pickup_time, first_name, last_name, item_count, phone]
# delivery_with_bags_list.append([visit_tuple[0], "", "", bags, route, first_name, last_name, item_count, phone])
I_CLIENT_ID = 0
I_ESTIMATED_BAGS = 3
I_TIME_ROUTE = 4
I_FIRST = 5
I_LAST = 6
I_ITEMS = 7
I_PHONE = 8

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

   #72 points = 1 inch;  612 points across page;  previous reports in excel had a font of 14 and a line height of 42 pixels
   pdf.set_margins(40, 24, 2) #left, top, right in points - 40 pix = .5"

   cell_padding = (table_def.vertical_padding,2)
   line_spacing = int(max(table_def.column_font) * 1.1)
   cell_height = int(line_spacing + (table_def.vertical_padding * 2)) # add 1 for the cell border?
   # the followning works, but it's not all that precise:
   number_of_rows_on_a_page = int(72*9/cell_height) # 9 inches is 1/2 top/bottom margins, plus header

   if len(table_def.column_widths) != len(table_def.column_font):
      exit(f"{len(table_def.column_widths)=} does not equal {len(table_def.column_font)=}")

   widths = table_def.column_widths
   if table_def.number_of_columns == 1:
      widths = table_def.column_widths
   elif table_def.number_of_columns == 2:
      if len(guest_list) > number_of_rows_on_a_page:
         widths = table_def.column_widths + [table_def.center_spacer_width] + table_def.column_widths
   else:
      print(f"Unsupported number of columns: {table_def.number_of_columns}; either 1 or 2")
      return

   # print(f"Generating {pdf_report_filename} {report_title=}: ", end="")
   current_row = 0
   guest_list_page_number = 0

   row_divisor = number_of_rows_on_a_page * table_def.number_of_columns
   page_count = math.ceil((len(guest_list) / row_divisor))
   # print(f"\t\t\t{report_title} {cell_height=}   {number_of_rows_on_a_page=} {page_count=}   {sum(widths)=} {widths=}")

   skipped_second_column = 0
   try:
      while current_row < len(guest_list):
         pdf.add_page()
         guest_list_page_number += 1
         pdf.set_font("Helvetica", "B", size=14)
         pdf.cell(0,0, f'{report_title}             {len(guest_list)} guests            Page {guest_list_page_number} of {page_count}', align="L")
         pdf.ln(pdf.font_size+4)
         pdf.set_font("Helvetica", "B", size=12)
         with pdf.table(align="L", line_height=line_spacing, padding=cell_padding, width=sum(widths), col_widths=widths) as table:
            pdf_table_row = table.row()
            for column_title in table_def.header:
               pdf_table_row.cell(column_title)
            if table_def.number_of_columns == 2 and len(guest_list) > number_of_rows_on_a_page:
               # print("Adding 2nd column")
               pdf_table_row.cell("", border=0) # spacer
               for column_title in table_def.header:
                  pdf_table_row.cell(column_title)
            # make dual data columns
            for _ in range(number_of_rows_on_a_page):
               pdf_table_row = table.row()
               this_guest = guest_list[current_row].copy()
               del this_guest[0] # delete client_id
               # print(f"{this_guest}")
               for idx, item in enumerate(this_guest):
                  pdf.set_font("Helvetica",  size=int(table_def.column_font[idx]))
                  pdf_table_row.cell(str(item))

               second_column_guest_index = current_row + number_of_rows_on_a_page
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
            current_row += number_of_rows_on_a_page # skip to next set of rows
            
   except Exception as e:
      status_string = f"Failure: while making table for {pdf_report_path} exception: {e}"
      return status_string
   
   if table_def.number_of_columns == 2:
      if current_row % number_of_rows_on_a_page:
         guest_count = current_row - number_of_rows_on_a_page
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


def write_counts_xlsx(guest_list, output_directory, filename):

   if len(guest_list[0][I_TIME_ROUTE]) == 5:
      generate_pickup_file = True
      header = ['Shop', 'Actual Bags', 'Est. Bags', 'Items', 'First', 'Last', 'Time', 'Phone']
   else:
      generate_pickup_file = False
      header = ['Shop', 'Actual Bags', 'Est. Bags', 'Items', 'First', 'Last', 'Route', 'Phone']

   # Phone is included so they can edit & print Expeditor report modifications
   visit_array   = []
   for tuple in guest_list:
      visit_array.append(["","",tuple[I_ESTIMATED_BAGS], tuple[I_ITEMS], tuple[I_FIRST], tuple[I_LAST], tuple[I_TIME_ROUTE], tuple[I_PHONE]])

   filename_path = os.path.join(output_directory, filename)
   workbook = xlsxwriter.Workbook(filename_path) 
   worksheet = workbook.add_worksheet()

   header_format = workbook.add_format({'bold': True})
   header_format.set_font_name('Arial')
   header_format.set_font_size(12)
   worksheet.write_row(0, 0, header, header_format)

   text_format = workbook.add_format()
   text_format.set_font_name('Arial')
   text_format.set_font_size(12)
   for row_number, content in enumerate(visit_array):
      worksheet.write_row(row_number+1, 0, content, text_format)

   if generate_pickup_file:
      time_route_width = 6
   else:
      time_route_width = 27
   column_widths = [6,6,6,6,12,17,time_route_width,15]
   for column_number, column_width in enumerate(column_widths):
      worksheet.set_column(column_number, column_number, column_width) #, text_format)

   workbook.close()

   print(f'{filename} has {len(visit_array)-1} guests')


def write_delivery_routes_pdf(deliveries_list, output_directory, pdf_filename, client_info, this_weeks_date, routes_to_print):
   if len(deliveries_list) == 0:
      print("Failure: no guest lists in request to generate PDF report on tag files.")
      return False

   guests_on_route_list = []
   pdf_filename_list = []

   for route_to_print_number in routes_to_print:
      guests_on_route_list = []
      route_name = None
      for visit_tuple in deliveries_list:
         this_guests_route_number = visit_tuple[I_TIME_ROUTE].split(":")[0]
         if this_guests_route_number == route_to_print_number:
            client_id = visit_tuple[I_CLIENT_ID]
            unit = client_info[client_id][5]
            guest_info = [client_id, "",visit_tuple[I_ESTIMATED_BAGS], visit_tuple[I_FIRST], visit_tuple[I_LAST], unit, visit_tuple[I_PHONE]]         
            guests_on_route_list.append(guest_info)
            if not route_name:
               street = client_info[client_id][4].split(" St")[0] #strip off Street         
               route_name = f"{visit_tuple[I_TIME_ROUTE][:14]} ({street})" #for page title

      if len(guests_on_route_list):
         report_header = f"Deliveries for {route_name} for {this_weeks_date[0][-5:]} "
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

   # delivery_with_bags_list.append([visit_tuple[0], "", "", bags, route, first_name, last_name, item_count, phone])
   for visit_tuple in guest_list:
      visit_route = visit_tuple[I_TIME_ROUTE].split(': ')[0]
      if visit_route not in routes_dict:
         routes_dict[visit_route] = 1
         try:
            route_name_dict[visit_route] = visit_tuple[I_TIME_ROUTE].split(': ')[1]
         except Exception:
            print(f"Route naming error for route '{visit_tuple[3]}' has no semicolon - client: {visit_tuple[I_CLIENT_ID]} last: {visit_tuple[I_LAST]} ")
            route_name_dict[visit_route] = visit_tuple[I_TIME_ROUTE]
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

def make_staging_list(pickup_list):
   # header = ["Freezer", "Fridge", "Shelf", "Total", "Est. Bags","Items", "First", "Last", "Time", "Phone"]
   staging_list = []
   for guest in pickup_list:
      if  int(guest[I_TIME_ROUTE].split(':')[0]) > 7:
         staging_list.append([guest[I_CLIENT_ID], "","","","", guest[I_ESTIMATED_BAGS], guest[I_ITEMS], \
            guest[I_FIRST], guest[I_LAST], guest[I_TIME_ROUTE], guest[I_PHONE]])
   return staging_list
