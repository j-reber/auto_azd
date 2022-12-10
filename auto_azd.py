import calendar
from datetime import datetime, timedelta
import random
from dateutil.rrule import DAILY, rrule, MO, TU, WE, TH, FR
from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import holidays

PDF = "azd_vorlage_kit.pdf"

months = {1: "Januar", 2: "Februar", 3: "März", 4: "April", 5: "Mai", 6: "Juni", 7: "Juli", 8: "August",
          9: "September", 10: "Oktober", 11: "November", 12: "Dezember"}


def generate_working_days(cur_month, cur_year, amount=6):
    """
    https://pypi.org/project/holidays/
    :param cur_month: Give month as int [1, 12]
    :param cur_year: Give year as four digit int e.g 2022
    :param amount: amount of days that are supposed to be chosen
    :return:
    """
    last_day = calendar.monthrange(cur_year, cur_month)[1]
    start_date = datetime(cur_year, cur_month, 1)
    end_date = datetime(cur_year, cur_month, last_day)
    if weekly_meeting:
        days_it = rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO, TU, WE, TH))
        days_meet = rrule(DAILY, dtstart=start_date, until=end_date, byweekday=FR)
    else:
        days_it = rrule(DAILY, dtstart=start_date, until=end_date, byweekday=(MO, TU, WE, TH, FR))

    # ger_holidays = holidays.country_holidays("DE", subdiv="BW")  # Other states can be selected here
    ger_holidays = holidays.CountryHoliday(country='DE', years=int(year), state='BW')
    print(ger_holidays)
    working_days = []
    for day in days_it:
        if day not in ger_holidays:
            working_days.append(day.strftime("%d.%m.%y"))

    if weekly_meeting:
        meeting_days = []
        for day in days_meet:
            if day not in ger_holidays:
                meeting_days.append(day.strftime("%d.%m.%y"))

    random.seed(42)
    selected_days = random.sample(working_days, amount)
    selected_days.sort()
    if weekly_meeting:
        selected_days = meeting_days + selected_days
        selected_days.sort()
        return meeting_days, selected_days
    return selected_days


def generate_hours(amount, num_meetings=None):
    starts, ends, durations = [], [], []
    if num_meetings:
        full_minutes = (int(monthly_hours) - num_meetings - 2.5) * 60
        hours = (int(monthly_hours) - num_meetings - 2.5) / amount
        timeslot = round(hours * 2) / 2 * 60
        session = []
        while full_minutes > 0:
            if full_minutes - timeslot > 0 and len(session) + 1 < amount:
                session.append(int(timeslot))
                full_minutes = full_minutes - timeslot
            else:
                session.append(full_minutes)
                full_minutes = 0
        # 3 for 3 hours of vacation
    else:
        session = [int(monthly_hours) * 60 // amount]*amount
    for i in range(amount):
        start = datetime.strptime("10:00", "%H:%M")
        starts.append(start.strftime("%H:%M"))
        duration = timedelta(minutes=session[i])
        end = start + duration
        ends.append(end.strftime("%H:%M"))
        durations.append(str(duration)[:4])
    return starts, ends, durations


def generate_meeting_hours():
    # starts, ends, durations = [], [], []
    time = 60
    start = datetime.strptime("15:00", "%H:%M")
    # starts.append(start.strftime("%H:%M"))
    duration = timedelta(minutes=time)
    end = start + duration
    # ends.append(end.strftime("%H:%M"))
    # durations.append(str(duration)[:4])
    return start.strftime("%H:%M"), end.strftime("%H:%M"), str(duration)[:4]


def get_keyword():
    keyword = random.sample(keywords, 1)[0]
    return keyword


def create_azd():
    splits = int(sessions)
    cur_month = int(month)
    cur_year = int(year)
    last_day_month = calendar.monthrange(cur_year, cur_month)[1]
    if weekly_meeting:
        meeting_days, days = generate_working_days(cur_month, cur_year, splits)
        starts, ends, durations = generate_hours(splits, len(meeting_days))
        meet_start, meet_end, meet_duration = generate_meeting_hours()
    else:
        days = generate_working_days(cur_month, cur_year, splits)
        starts, ends, durations = generate_hours(splits)
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.drawString(410, 740, months[cur_month])
    can.drawString(480, 740, year)
    can.drawString(300, 720, name)
    can.drawString(497, 702, "X")
    can.drawString(300, 685, institute)
    can.drawString(280, 668, monthly_hours)
    can.drawString(475, 668, hourly_wage)
    can.drawString(475, 285, monthly_hours)

    # for i in range(splits):
    #     height = 618 - 14.5 * i
    #     keyword = get_keyword()
    #     can.drawString(70, height, keyword)
    #     can.drawString(210, height, days[i])
    #     can.drawString(270, height, starts[i])
    #     can.drawString(340, height, ends[i])
    #     can.drawString(480, height, durations[i])

    num_meetings = 0
    for i, day in enumerate(days):
        height = 618 - 14.5 * i
        if weekly_meeting and day in meeting_days:
            keyword = "Meeting"
            can.drawString(70, height, keyword)
            can.drawString(210, height, day)
            can.drawString(270, height, meet_start)
            can.drawString(340, height, meet_end)
            can.drawString(480, height, meet_duration)
            num_meetings += 1
        else:
            keyword = get_keyword()
            can.drawString(70, height, keyword)
            can.drawString(210, height, day)
            can.drawString(270, height, starts[i-num_meetings])
            can.drawString(340, height, ends[i-num_meetings])
            can.drawString(480, height, durations[i-num_meetings])

    # Create Signature
    can.drawString(65, 190, f"{str(last_day_month)}.{cur_month}.{str(cur_year)[-2:]}")
    can.drawImage("signature/signature_transparent.png", 110, 170, width=160, height=60, mask="auto")

    can.save()

    # move to the beginning of the StringIO buffer
    packet.seek(0)

    # create a new PDF with Reportlab
    new_pdf = PdfFileReader(packet)
    # read your existing PDF
    existing_pdf = PdfFileReader(open(PDF, "rb"))
    output = PdfFileWriter()
    # add the "watermark" (which is the new pdf) on the existing page
    page = existing_pdf.getPage(0)
    page.mergePage(new_pdf.getPage(0))
    output.addPage(page)
    # finally, write "output" to a real file
    with open("outputs/result.pdf", "wb") as outputStream:
        output.write(outputStream)


if __name__ == "__main__":
    month = "11"  # Int form 1-12
    year = "2022"  # Int > 1990
    institute = "Institut für abgewandte Informatik"
    monthly_hours = "36"  # Int > 0
    hourly_wage = "12,52"
    name = "Max Mustermann"
    keywords = ["Model trainieren", "Model evaluieren", "Präsentation"]
    sessions = "6"  # Int > 0
    weekly_meeting = FR
    create_azd()
