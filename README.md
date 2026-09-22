# Arbor to iCal
A python script that automatically logs into your Arbor account and converts all entries from your Calendar into iCal (.ics) format.

## Why?
For the last couple of years, I have used my Apple Watch to track all of my school periods so that I can quickly glance at where I need to be. Then the service that our school used that let us export that information shut down, and we migrated to Arbor.
To remedy this, we simply got our calendar data from Google Calendar instead, which let you export the same way...<br>
... and then Google Calendar got blocked on our accounts for some reason

Since the only way to digitally track which periods I have is now through Arbor, I needed a way to export my Calendar data to iCal so that it can be imported on other devices. Arbor's own help center states that "You can only export Staff Calendars. This feature is not available for Student Calendars. To export Staff Calendars with this feature, you must use a Live Feed" meaning if I want to get an iCal output from Arbor, I'd have to do it myself.

Then I made this script, whatever whatever it works it generates an ics file okay job done go have fun and don't violate the [license](LICENSE) cuz that's illegal or something

# Usage
- Install [Python 3](https://www.python.org/downloads/), and make sure pip is included. Otherwise, install that separetly
- Clone this repository either by clicking `Code > Download ZIP` or using the command `git clone https://github.com/gingerphoenix10/Arbor-to-iCal.git` if you have git installed. GitHub Desktop also probably lets you do that too
- In the root of this project, install dependencies using either `pip install -r requirements.txt` or `python3 -m pip install requirements.txt`
- Run the script with `python3 main.py`
- Enter your login details, and if valid, arbor.ics should be generated in the current folder