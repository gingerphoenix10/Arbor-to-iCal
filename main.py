# This is a script that logs into your Arbor account, requests all Calendar data, and converts it into ical (.ics) format.
# There are a LOT of comments, simply because Arbor reaaaally sucks to work with. Not a fun experience making this.
# Maybe the sheer amount of comments could help another poor soul dealing with Arbor's API in the future
# also this code probably sucks because I don't use python very often and just wanted this done with already

import requests
import json
import xml.etree.ElementTree as ET
from icalendar import *
import datetime as dt
import zoneinfo
from pathlib import Path
from time import sleep

#︃ Default values for pre-authenticated since we don't lookup the school
schoolName = None
schoolLocation = None
schoolUrl = None


# Disabled because it's objectively worse
#preAuthenticated = not input("Use Email & Password instead of a pre-generated token? (Y/n)").strip().lower().startswith("n")
preAuthenticated = False

# PreAuth on - If pre-authenticated, use existing token. Lasts about an hour or two I believe
if preAuthenticated:
    school_prefix = input("Enter your school's URK prefix ({this}.uk.arbor.sc): ")
    schoolName = school_prefix
    schoolUrl = f"https://{school_prefix}.uk.arbor.sc"
    token = input("Enter your token: ")

# PreAuth off - Use a username (email) and password to automatically login to your Arbor account and get its own token
else:
    username = input("Enter Username (Email): ")
    password = input("Enter Password: ")


# Get token from login details
if not preAuthenticated:
    # Find which school is bound to this account
    searchUrl = "https://login.arbor.sc/applications/search-by-email"
    searchBody = {"email": username, "password": password}
    searchReq = requests.post(searchUrl, json=searchBody)
    searchResp = json.loads(searchReq.text)

    if searchResp["status"] != 200:
        print(f"ERROR: {searchResp["status"]}")
        exit()
    if len(searchResp["payload"]) == 0:
        print("Authentication failed! Check your login details")
        exit()

    schoolName = searchResp["payload"][0]["name"]
    schoolLocation = searchResp["payload"][0]["location"]
    schoolUrl = searchResp["payload"][0]["sisUrl"]

    # Login to the found school's Arbor server with the provided details
    authUrl = f"{schoolUrl}/auth/login"
    authBody = {"items":[{"username":username,"password":password}]}
    authReq = requests.post(authUrl, json=authBody)
    authResp = json.loads(authReq.text)
    if not authResp["success"]:
        print("Authentication failed! Check your login details")
        exit()
    token = authResp["items"][0]["session_id"]
    print(f"New token: {token}")
print()

# Arbor has 3 calander request modes - Day, 5 Days, and Month. These are all handled really weirdly:
# If we want the most entries with the least requests, you'd assume we'd use Month mode, however there's a caveat - Location is *only* provided on Day mode.
# To get the location on any other mode would require us to send an extra request for *every* event in the calendar, which would be significantly more than just 1 per day.
# Month is also formatted differently on the website, meaning the HTML returned is in a different format to Day and 5 Days, so whilst those both work with this script, Month does not.
# Strangely enough though, even though Day is the "single day" mode, it actually returns 5 days worth of calendar events - starting from 2 days before the requested date, and ending 2 after.
# This is likely to preload them for switching pages quicker, but still seems incredibly counter-intuitive.
# This is good for us however, since that means we only need to send 1 request for every 5 days we want.
dates = []
for i in range(int(365/5)): # 1 year worth of calendar events in 5-day intervals
    # Maybe instead of using datetime.now(), we could snap it to wednesday so it starts at monday, ends on final sunday
    date = dt.datetime.now() + dt.timedelta(days=5*i)
    arborDate = "{:04d}-{:02d}-{:02d}".format(date.year, date.month, date.day)
    dates.append(arborDate)

cal = Calendar.new(name=f"{schoolName} Calendar")
i = 1
try:
    for date in dates:
        print(f"{i} / {len(dates)} - {date}")

        # Request this date's calendar entries. This uses POST for some reason even though we're *getting* the data
        url = f"{schoolUrl}/calendar-entry/list-static/format/json/"
        body = {"action_params":{"view":"day","startDate":date,"endDate":date,"filters":[{"field_name":"object","value":{"_objectTypeId":1,"_objectId":3777}}]}}
        cookie = {"mis": token}

        calendarReq = requests.post(url, json=body, cookies=cookie)
        calendarResp = json.loads(calendarReq.text)

        if not calendarResp["success"]:
            print(f"ERROR: {calendarResp["message"]}")
            break

        for item in calendarResp["items"]:
            value = item["fields"]["response"]["value"]
            for page in value["pages"]:
                # Each page is a single day (I think) since we're still receiving multiple days 
                if "html" in page:
                    # We have data for this day
                    DateParts = page["start"].split("-")
                    DateYear = int(DateParts[0])
                    DateMonth = int(DateParts[1])
                    DateDay = int(DateParts[2])

                    htmlText = page["html"].replace("data - ot", "data-ot") # strange bug in arbor? Seems to send invalid xml/html

                    # Parse the day's HTML as XML so that we can navigate through elements
                    html = ET.fromstring(htmlText)
                    eventsElement = html.find("table").find("tbody").find("tr") # I think the first tr is for calendar event entries, and the rest of the tr elements are the hours that show on the left
                    for day in eventsElement.findall("td"): # Pretty sure these are used for each day in week mode. Would need to track the index of this and add it to DateDay to get the actual calendar day
                        events = day.findall("div") # Unused tds don't have any divs, so the list is empty and nothing happens during iteration
                        for event in events:
                            timeSection = event.find("div") # div contains the "hh:mm - hh:mm | Location: 000" information 
                            nameSection = event.find("span") # span contains the event name


                            timeLocText = timeSection.find("span").text
                            name = nameSection.find("b").find("b").text

                            # Doesn't handle month wraparound ffffUCK
                            TimeLocationSplit = timeLocText.split(" | Location: ")
                            time = TimeLocationSplit[0]

                            # Location isn't always included. Keep blank unless " | Location: " was found, in which case we use it
                            loc = ""
                            if len(TimeLocationSplit) > 1:
                                loc = TimeLocationSplit[1]

                            print(f"{DateDay}/{DateMonth}/{DateYear} at {time} - {name} in {loc}")

                            startEndSections = time.split(" - ") # Split "hh:mm" start and "hh:mm" end
                            startTime = startEndSections[0]
                            endTime = startEndSections[1]

                            startTimeHoursMinutes = startTime.split(":")
                            startHours = int(startTimeHoursMinutes[0])
                            startMinutes = int(startTimeHoursMinutes[1])
                            
                            endTimeHoursMinutes = endTime.split(":")
                            endHours = int(endTimeHoursMinutes[0])
                            endMinutes = int(endTimeHoursMinutes[1])

                            # Finally, add to the ical file
                            timezone = zoneinfo.ZoneInfo("Europe/London")
                            formattedLocation = None
                            if loc != "":
                                formattedLocation = f"{schoolName}: {loc}"
                                if schoolLocation != None:
                                    formattedLocation = f"{formattedLocation} - {schoolLocation}"
                            calEvent = Event.new(
                                start=dt.datetime(DateYear, DateMonth, DateDay, startHours, startMinutes, 00, tzinfo=timezone),
                                end=dt.datetime(DateYear, DateMonth, DateDay, endHours, endMinutes, 00, tzinfo=timezone),
                                summary=name,
                                location=formattedLocation,
                                description=name
                            )
                            cal.add_component(calEvent)
        i = i + 1

except KeyboardInterrupt:
    print()
    print("Ending early")

except Exception as e:
    print()
    print(e)
    print("An error occured during conversion. Outputting whatever we got so far")

print()
print(f"Finished at {i-1} / {len(dates)}")
out = Path("arbor.ics")
out.write_bytes(cal.to_ical())
print(f"Outputted to {out.absolute()}")