#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime, timedelta
import math
import requests
from dateutil.tz import tzlocal

DEBUG=True
JCALAPI_URL="http://localhost:7042/events"
MAX_HOURS_BY_DAY=10
MY_SFDC_ID="0052H00000BxQ9GQAV"

class Attendee:
    def __init__(self, name, email, optional):
        """
        Initializes an Attendee object.

        Args:
            name (str): The name of the attendee.
            email (str): The email address of the attendee.
            optional (bool): Whether the attendee is optional or not.
        """
        self.name = name
        self.email = email
        self.optional = optional

class EventEntry:

    SUBJECT_LIST = [
        "BACK OFFICE TASKS",
        "COMPANY/TEAM MEETINGS",
        "HighspotActivity",
        "LEARNING ACTIVITY",
        "OTHER PRE SALES (OPPORTUNITY RELATED)",
        "PARTNER ENGAGEMENT",
        "PIPELINE GENERATION ACTIVITY",
        "POST SALES ASSISTANCE",
        "PRE SALES ONSITE",
        "SME SUPPORT",
        "TRAVEL",
        "VACATION"
    ]

    def __init__(self, uid, backend, calendar, organizer, attendees, summary, description, body, location, start, end, whole_day, is_recurring, status, categories, extra, conference_url):
        """
        Initializes an instance of the Event class.

        Args:
            uid (str): The unique identifier of the event.
            backend (str): The backend used for the event.
            calendar (str): The calendar associated with the event.
            organizer (str): The organizer of the event.
            attendees (list): A list of attendees for the event.
            summary (str): The summary or title of the event.
            description (str): The description of the event.
            body (str): The body or content of the event.
            location (str): The location of the event.
            start (str): The start date and time of the event in ISO format.
            end (str): The end date and time of the event in ISO format.
            whole_day (bool): Indicates if the event is a whole day event.
            is_recurring (bool): Indicates if the event is recurring.
            status (str): The status of the event.
            categories (list): A list of categories associated with the event.
            extra (str): Extra information about the event.
            conference_url (str): The URL for the conference associated with the event.
        """
        self.uid = uid
        self.backend = backend
        self.calendar = calendar
        self.organizer = organizer
        self.attendees = [Attendee(**attendee) for attendee in attendees]
        self.summary = summary
        self.description = description
        self.body = body
        self.location = location
        self.start = datetime.fromisoformat(start)
        self.end = datetime.fromisoformat(end)
        self.whole_day = whole_day
        self.is_recurring = is_recurring
        self.status = status
        self.categories = categories
        self.extra = extra
        self.conference_url = conference_url
        self.duration_hours = self.calculate_duration_hours()
        self.subject = self.category_matches_subject_list()
        self.companies = self.category_matches_company()

    def calculate_duration_hours(self):
        """
        Calculates the duration in hours between the start and end time.

        Returns:
            int: The rounded duration in hours, or None if either the start or end time is missing.
        """
        if self.start is not None and self.end is not None:
            duration = self.end - self.start
            duration_hours = duration.total_seconds() / 3600
            rounded_hours = math.ceil(duration_hours)
            return rounded_hours if rounded_hours <= MAX_HOURS_BY_DAY else MAX_HOURS_BY_DAY
        else:
            return None

    def category_matches_subject_list(self):
        """
        Checks if any category in the list matches the subject list.
        
        Returns:
            str: The matched category if found, None otherwise.
        """
        for category in self.categories if self.categories is not None else []:
            if category.startswith("SU::"):
                stripped_category = category.replace("SU::", "")
                if stripped_category in self.SUBJECT_LIST:
                    return stripped_category
        return None

    def category_matches_company(self):
        """
        Returns a list of companies that match the category.

        Returns:
            list: A list of dictionaries containing the id and name of the matching companies.
        """
        companies = []
        for category in self.categories if self.categories is not None else []:
            if category.startswith("CU::"):
                parts = category.split("::")
                if len(parts) >= 3:
                    company = {"id": parts[2], "name": parts[1]}
                    companies.append(company)
        return companies

def fetch_data():
    """
    Fetches data from JCALAPI_URL and returns it as JSON.

    Returns:
        dict: The fetched data as a JSON dictionary.
        None: If the request fails or the response status code is not 200.
    """
    response = requests.get(JCALAPI_URL, timeout=15, verify=False)
    if response.status_code == 200:
        json_data = response.json()
        return json_data
    else:
        print(f"Failed to retrieve JSON from {JCALAPI_URL}. Status code: {response.status_code}")
        return None

def validate_events_timing(events, start_date, end_date):
    """
    Validates the timing of events based on the given start and end dates.

    Args:
        events (list): A list of events to be validated.
        start_date (datetime): The start date of the date range.
        end_date (datetime): The end date of the date range.

    Returns:
        list: A list of valid events that fall within the specified date range.
    """
    valid_events = []
    for event in events:
        event_start = datetime.fromisoformat(event['start'])
        event_end = datetime.fromisoformat(event['end'])
        if start_date <= event_start <= end_date and start_date <= event_end <= end_date:
            valid_events.append(event)
            if DEBUG:
                print(f"INCLUDED - Event {event['summary']} at {event['start']} is within the date range")
        else:
            if DEBUG:
                print(f"EXCLUDED - Event {event['summary']} at {event['start']} is NOT within the date range")
    return valid_events

def main():
    def last_week():
        today = datetime.now(tz=tzlocal()).replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=today.weekday(), weeks=1)
        end = start + timedelta(days=6)
        return start, end.replace(hour=23, minute=59, second=59, microsecond=0)

    def last_month():
        today = datetime.now(tz=tzlocal()).replace(hour=0, minute=0, second=0, microsecond=0)
        start = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end = today.replace(day=1) - timedelta(days=1)
        return start, end.replace(hour=23, minute=59, second=59, microsecond=0)

    def current_week():
        today = datetime.now(tz=tzlocal()).replace(hour=0, minute=0, second=0, microsecond=0)
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        return start, end.replace(hour=23, minute=59, second=59, microsecond=0)

    def validate_date(date_text):
        try:
            datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    parser = argparse.ArgumentParser(
        prog="export_event_exchange_sfdc",
        description="Export events from Exchange to CSV file able to be imported to Salesforce.",
        epilog="Without parameters, the script will export events from current week."
    )
    parser.add_argument(
        '--last-week',
        action='store_true',
        help="Export events from last week. Take precendence over --start and --end."
        )
    parser.add_argument(
        '--last-month',
        action='store_true',
        help="Export events from last month. Take precendence over --start and --end."
        )
    parser.add_argument('--start', type=str, help="Start date in format YYYY-MM-DD.")
    parser.add_argument('--end', type=str, help="End date in format YYYY-MM-DD.")
    parser.add_argument('-a', '--export-all', action='store_true', help="Export all events from Exchange including events without SFDC Task subject.")

    args = parser.parse_args()

    if args.last_week:
        start_date, end_date = last_week()
    elif args.last_month:
        start_date, end_date = last_month()
    elif args.start and args.end:
        if validate_date(args.start) and validate_date(args.end):
            start_date = datetime.strptime(args.start, '%Y-%m-%d').replace(tzinfo=tzlocal())
            end_date = datetime.strptime(args.end, '%Y-%m-%d').replace(hour=23, minute=59, second=59, microsecond=0, tzinfo=tzlocal())
            if start_date > end_date:
                parser.error("Start date must be before end date")
        else:
            parser.error("Invalid date format for --start or --end, should be YYYY-MM-DD")
    elif args.start or args.end:
        parser.error("--start and --end should be used together")
    else:
        start_date, end_date = current_week()

    print(f"Start date: {start_date}, End date: {end_date}")
    events = fetch_data()
    if events is not None:
        valid_events = validate_events_timing(events, start_date, end_date)
        if valid_events:
            print(f"{len(valid_events)} events are within the date range")
            matching_events = [EventEntry(**event) for event in valid_events]
            for event in matching_events:
                print(f"{event.start} - {event.end} - {event.summary} - {event.duration_hours} hours - {event.subject} - {event.companies}")
        else:
            print("No events are within the date range")

if __name__ == "__main__":
    main()
