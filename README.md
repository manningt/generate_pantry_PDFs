# Introduction
At the close of accepting orders from guests, currently at 12:15 on Thursdays, the following reports need to be generated:
- Pickup expeditor: a table with columns: Bags, Pickup Time, First & Last Names, and phone numbers:
    - The bags column is blank, it is used to in the fulfillment process to check that orders have been taken by a shopper, completed and something else.
    - The rows are sorted by Pickup time, last name, first name
    - the guest's phone number is included in case they do not show up at the pickup time.
    - The file naming convention is: Pickups_by_time_MM-DD where DD is the Friday of the week.  These reports are maintain in a folder indicating the year.
    - Saturday pickups are on a seperate page.
- Pickups sorted by name
    - same columns the Pickup expeditor, but sorted by last name, first name.
    - The file naming convention is: Pickups_by_name_MM-DD
- Delivery expeditor: a table with columns: Bags, Delivery Route, First & Last Names & phone:
    - Like the Pickup Expeditor, the bags column is blank
    - The rows are sorted by Delivery Route, last name, first name
    - Some orders on a delivery-route can be picked up instead of delivered.  Currently orders on the Quaker delivery route are picked up at 3:45.  These orders are moved from the delivery expeditor files to the pickup expeditor flags - but not the bag tag printing files.  When moved to the Pickup list, the delivery route is used instead of their first name.
    - A few guests have priority - their orders are shopped first for that delivery route.  This is indicated by an asterick preceeding their last name, so they get sorted to be before the other guests.
- Pickup & Delivery CSV files used for tracking bags per guest.  The columns are Bags[used], Bags[calculated], Labels, Items, First, Last, Route/Pickup Time.
    - After orders have been filled, the first column is edited with the actual number of bags used.  Analysis of these files is done at a later time to refine the number of bags required per number of items.
    - The Labels column contains the number of bags required for the number of items in the order.  The item to bag calculation is done by the program.
    - The items column is included in order to have all the data necessary to analyze the items to bag calculation.
- Tag/Label PDFs
    - 4 PDFs are generated: 1 Delivery and 3 Pickups (Friday_before_3, Friday_after_3, and Saturday).
    - The delivery labels have the route at the top, followed by the guest's first and last name, and a page count, e.g. 3 of 6.  The labels are printed in order of delivery route, last name.
    - The pickup labels on have the first, last names and the page count, and are ordered by Last name, First name, rather than pickup time.
    - The pickup labels are printed in the order of Last Name, First Name
    - A thermal printer is used to print the 2x4 labels - this printing is done manually after downloading the 4 PDFs from the food pantry's Google Team drive.
- list-of-guests-in-tag-pdf-files
    - A single file with a table of first and last names, pickup time or route, and number of items.  There are separate pages for Delivery, before 3, after 3 and Saturday.

# Implementation
A program written in Python retrieves a list of guests and a list of this week's orders using the PantrySoft API.  For ease of deployment, it runs on a [small computer](https://en.wikipedia.org/wiki/Raspberry_Pi), located inside the food pantry (on the shelf with the router). The computer uses the pantry's WiFi network to access to the internet. The computer does not have a keyboard or display and is accessed using a VPN service and [Tailscale](tailscale.com).

The program uses a token to authorize authorize access to the PantrySoft interface. The token is provided by PantrySoft upon request.  The token is stored on the small computer system which can only be reached using the VPN service.

Once the program has retrieve the data from PantrySoft, it generates the PDFs and CSV files described above.  It stores the files in a directory named output_files, and then uploads them to the Pantry's Google Team Drive.  The folder the reports are uploaded to is: [Newbury Food Pantry/PANTRYSOFT ORDER DOCUMENTS/YYYY/MONTH/MON-DD](https://drive.google.com/drive/folders/1fe1J4Un0bw3vqtge0tvBu9Nx4JcXT4nu) where YYYY is 2027, MONTH is the full month name.  A Google token is required be able to upload the files without interaction, where the interaction is a webpage pop-up window asking for permission. Like the PantrySoft token, Google token is stored locally on the small computer. *The token expires in 7 days, so currently a new token is generated on a separate computer   *A work-item for the developer is how to generate that token - the Google UI for doing this is not easy.*

After uploading the documents, the program queues the expeditor PDFs and the list-of-tags to the PDF to the local letter-sized printer.  Currently this is a Brother model MFC-L8900CDW, which is available on the Pantry's WiFi network. How to set this up is documented in a separate section.

The program is launched by the unix 'cron' utility at 12:16 on Thursdays.  It writes a log of operations to /tmp/make_tags.log

The program is maintained in a [github](https://en.wikipedia.org/wiki/GitHub) repository: https://github.com/manningt/generate_pantry_PDFs

The small computer does not have a monitor or keyboard.  It is accessed using [ssh](https://en.wikipedia.org/wiki/Secure_Shell).  From the pantry's computers using ```ssh username@192.168.1.215```.  The username and password can be obtained from the developer.  It can also be accessed from the internet using [Tailscale](https://en.wikipedia.org/wiki/Tailscale) which provides VPN services.  *Need to set up a Food Pantry account for Tailscale*

# Program Overview
The program does the following:
1. generate the list of clients (guests), where each client has some data (delivery_route, phone, address, etc)
    - it uses the [PantrySoft REST API](https://app.pantrysoft.com/api/doc) to get all the clients.
    - the client API limits each GET request to 100 entries, so it has to do a loop to get all the entries
    - a function parses the returned list of client data to extract the client information
2. generate a list of visits during the current week (Friday, Saturday).
    - If the script is not run on a Thursday, then it runs in 'test-mode' and uses hardcoded dates.
3. generate 4 bag tag PDFs for the visits (delivery, Friday, Saturday) as well as a report PDF listing the guests in alphabetical order.
4. generate 2 expeditor PDFs: pickup and delivery
5. generate Pickups_by_name PDF to help with shopping preperation.
6. generate 2 CSV files to be used for tracking bag counts per item count
7. upload the generated files to Google Drive: /Newbury Food Pantry/PANTRYSOFT ORDER DOCUMENTS/20xx/Tags where 20xx is the year, starting with 2026
8. Print the letter sized PDFs on the Pantry printer.

# make_this_fridays_folder program
This program is run every Monday to create the folder YYYY/MONTH/MON-DD, if it doesn't exist.  MONTH is the full name.  MON is the 3 letter abbreviation, except for September, which is 4 characters.  The folder needs to be created before Tuesday, because the caller supervisor uploads a spreadsheet named *Master List for Calling  Month Day Year*.  On Thursdays, the *generate.py* script uploads to this Friday's folder.

The program is launched as a cron job; it's output is written to /tmp/make_fridays_folder.log
The line in crontab -e is:
```
02 5 * * 1 cd /home/pantry/repos/generate_pantry_PDFs && /home/pantry/.local/bin/uv run make_this_fridays_folder.py >> /tmp/make_fridays_folder.log 2>&1
```

# Details
## Handling registrations
There are [registration questions](https://app.pantrysoft.com/registrationquestion/) that effect the expeditor reports.  Specifically there is the required 'registration_cell' which can be Yes or No, and the optional 'Is Priority' which can True or False.

Registrations are not required for clients - it was found that 5 clients did not have registrations.

A client can be registered multiple times; the PantrySoft API allows getting a list of registrations sorted by decreasing datetime for a client.  The API also allows getting all the registrations sorted by client or by datetime.  Since there are more than 6000 registrations, doing a query to determine the state of cell phone and priority would take time. Similarly, doing a get for every client would require more than 800 GETs - this was measured at a little under 6 mimutes.

In order to avoid extensive queries, the program will use a file, 'my_priority.json' to save which the client ID's that have priority.
The script '''get_registration_data''' can be run periodically to update the my-priority.json file.

It was decided that indicating whether a phone number is a cell or landline was not necessary.  One of the reasons for the decision is the data in the registration could be wrong - either due to a guest porting a number, a data entry error, or a registration not being performed for a guest.  Because the data may not be reliable, and when trying to contact the guest it could be determined cell/landline, then the registration cell data is no longer used. Although the get_registration_data obtains the cell phone state, it currently does not do anything with the data.

## Documentation for how to use the Pantry's printer.
### To print a PDF:
[Common UNIX Printing System (CUPS) documentation](https://www.cups.org/doc/admin.html#PRINTERS)
```
lp <filename>
lp -n num-copies -o collate=true filename
```

### Installing linux printer support packages:
[how-to-install-wifi-printer-on-debian-trixie-step-by-step](https://tutorialforlinux.com/2025/05/20/how-to-install-wifi-printer-on-debian-trixie-step-by-step/2/)

[how-to-find-network-printers](https://www.baeldung.com/linux/printer-ip-address):  Avahi is 'bonjour' or zero-conf

```
sudo apt install cups cups-client cups-filters cups-ipp-utils
sudo service cups start
sudo systemctl enable --now cups
sudo nano /etc/cups/cupsd.conf -> Browsing On
sudo usermod -aG lpadmin $USER

sudo apt install avahi-daemon
sudo service avahi start
sudo systemctl enable avahi-daemon
sudo apt-get install avahi-utils
```
### Finding wifi printers:
[how-to-find-network-printers](https://www.cups.org/doc/network.html)
```
lpinfo --include-schemes dnssd -v
  response at pantry: network dnssd://Brother%20MFC-L8900CDW%20series._ipp._tcp.local/?uuid=e3248000-80ce-11db-8000-b42200adc8a6
# the following command shows all the printer types per IP, e.g. Unix, PDL, Internet.  Use it to get the IP address of the unix printer
avahi-browse --all -t -r
```
### Add Printer after finding it's IP address:
ipp stands for internet printing protocol:
```
lpadmin -p pantry_printer -E -v ipp://192.168.1.239/ipp/print -m everywhere
# make the printer the default:
lpadmin -d pantry_printer
# show total state of printing system
lpstat -t
#To add a coverpage (not used - using custom coverpages)
lpoptions -p pantry_printer -o job-sheets=standard
```

### Installing a printer driver

[how-to-install-wifi-printer-on-debian-trixie-step-by-step](https://tutorialforlinux.com/2025/05/20/how-to-install-wifi-printer-on-debian-trixie-step-by-step/#google_vignette)

[Brother MFC-L8900CDW driver](https://packages.debian.org/en/stable/text/printer-driver-brlaser)
```
sudo apt install printer-driver-brlaser
#list printer drivers:
lpinfo -m | grep -i 'brother MFC-L'
```


# Notes:
- https://app.pantrysoft.com/api/v1/client/?limit=N returns 'count' after 'data', where the count equal to the number of active clients.
- Similarly https://app.pantrysoft.com/api/v1/registration/?client_id=N returns 'count' after 'data', with the count equal to the number of registrations.