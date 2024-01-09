#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module to export events from Exchange to CSV file able to be imported to Salesforce.

Author: GUYARD Marc - mguyard@fortinet.com
Version: 0.1
"""

import argparse
import logging
from datetime import datetime, timedelta
import math
import csv
import requests
from dateutil.tz import tzlocal

JCALAPI_URL="http://localhost:7042/events"
MAX_HOURS_BY_DAY=10
MY_SFDC_ID="0052H00000BxQ9GQAV"
MORNING_HOUR=8
EVENING_HOUR=22

class Attendee:
    """Class representing a Attendee"""

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
    """Class representing an event entry"""

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
        self.opportunities = self.category_matches_opportunities()

        logging.debug("%s - %s - %s - %s hours - %s - %d companies (%s) and %d opportunities",
                      self.start,self.end, self.summary,
                      self.duration_hours, self.subject, len(self.companies),
                      '; '.join([str(company['name']) for company in self.companies]),
                      len(self.opportunities))

    def calculate_duration_hours(self):
        """
        Calculates the duration in hours between the start and end time.

        Returns:
            int: The rounded duration in hours, or None if either the start or end time is missing.
        """
        if self.start is not None and self.end is not None:
            start = max(self.start, self.start.replace(hour=MORNING_HOUR, minute=0))
            end = min(self.end, self.end.replace(hour=EVENING_HOUR, minute=0))

            if start >= end:
                return 0

            total_hours = 0
            while start.date() <= end.date():
                day_end = min(end, start.replace(hour=EVENING_HOUR, minute=0))
                hours_this_day = (day_end - start).seconds / 3600
                total_hours += min(hours_this_day, MAX_HOURS_BY_DAY)
                start = (start + timedelta(days=1)).replace(hour=MORNING_HOUR, minute=0)
            return math.ceil(total_hours)
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

    def category_matches_opportunities(self):
        """
        Returns a list of opportunities that match the categories.
        
        Returns:
            list: A list of dictionaries representing the opportunities. Each dictionary
            contains the 'id' and 'name' of the opportunity.
        """
        opportunities = []
        for category in self.categories if self.categories is not None else []:
            if category.startswith("OP::"):
                parts = category.split("::")
                if len(parts) >= 3:
                    opportunity = {"id": parts[2], "name": parts[1]}
                    opportunities.append(opportunity)
        return opportunities

def fetch_data():
    """
    Fetches data from JCALAPI_URL and returns it as JSON.

    Returns:
        dict: The fetched data as a JSON dictionary.
        None: If the request fails or the response status code is not 200.
    """
    try:
        response = requests.get(JCALAPI_URL, timeout=15, verify=False)
        response.raise_for_status()  # Raise an exception for non-200 status codes
        json_data = response.json()
        return json_data
    except requests.exceptions.RequestException as e:
        logging.error("Failed to retrieve JSON from %s: %s", JCALAPI_URL, str(e))
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
    logging.info("Validating if events are within the date range %s - %s", start_date, end_date)
    valid_events = []
    for event in events:
        event_start = datetime.fromisoformat(event['start'])
        event_end = datetime.fromisoformat(event['end'])
        if start_date <= event_start <= end_date and start_date <= event_end <= end_date:
            valid_events.append(event)
            logging.debug("INCLUDED - Event %s at %s is within the date range",
                          event['summary'], event['start'])
        else:
            logging.debug("EXCLUDED - Event %s at %s is NOT within the date range",
                          event['summary'], event['start'])
    return valid_events

def filter_events(events):
    """
    Filters a list of events based on certain criteria.

    Args:
        events (list): The list of events to be filtered.

    Returns:
        list: The filtered list of events.
    """
    filtered_events = []
    logging.info("Filtering events based on duration > 0 and subject is defined")
    for event in events:
        if event.duration_hours > 0 and event.subject:
            logging.debug("INCLUDED - Event %s at %s match the criteria",event.summary, event.start)
            filtered_events.append(event)
        else:
            logging.debug("EXCLUDED - Event %s at %s does not match the criteria",
                          event.summary, event.start)
    logging.info("%d events are valid (matching duration > 0 and subject is defined) on %d events",
                 len(filtered_events), len(events))
    return filtered_events

def write_events_to_csv(events, filename):
    """
    Write events to a CSV file.

    Args:
        events (list): List of events to write.
        filename (str): Name of the CSV file.

    Returns:
        None
    """
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([
            'OwnerId',
            'ActivityDate',
            'WhatId',
            'Status',
            'Subject',
            'Time_Spent_hrs__c',
            'Comments'])
        for event in events:
            companies = '; '.join([str(company['id']) for company in event.companies])
            opportunities = '; '.join([str(opportunity['id']) for opportunity in event.opportunities])
            comments = []
            comments.append(f'Event Summary: {event.summary}')
            if not companies and not opportunities:
                comments.append('No companies or opportunities are defined. Please verify if it is needed for this subject.')
                task_related_to = ''
            else:
                task_related_to = opportunities if opportunities else companies
            if len(event.companies) > 1:
                comments.append('Multiple companies are defined. You need to choose one manually.')
            if len(event.opportunities) > 1:
                comments.append('Multiple opportunities are defined. You need to choose one manually.')
            writer.writerow([
                MY_SFDC_ID,
                event.start.date(),
                task_related_to,
                'Completed',
                event.subject,
                event.duration_hours,
                ' // '.join(comments)])

def main():
    """
    Main function that exports events from Exchange to a CSV file
    that can be imported to Salesforce.

    The function accepts command line arguments to specify the date range
    of events to export. If no arguments are provided, it exports events
    from the current week.

    Command line arguments:
    --last-week: Export events from last week.
    --last-month: Export events from last month.
    --start: Start date in format YYYY-MM-DD.
    --end: End date in format YYYY-MM-DD.
    -a, --export-all: Export all events from Exchange including events without SFDC Task subject.
    -o, --output: Output CSV file name and path.
    --verbose, -v: Verbose mode.

    Returns:
    None
    """

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
    parser.add_argument('-a', '--export-all',action='store_true',
                        help="Export all events from Exchange including events without SFDC Task subject.")
    parser.add_argument('-o', '--output', type=str, default='sfdc_task.csv',
                        help="Output CSV file name and path.")
    parser.add_argument('--verbose', '-v', action='store_true', default=False, help="Verbose mode")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG, style='{', format='{levelname:8} {message}')
    else:
        logging.basicConfig(level=logging.INFO, style='{', format='{levelname:8} {message}')

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

    logging.info("Start date: %s, End date: %s", start_date, end_date)
    events = fetch_data()
    if events is not None:
        valid_events = validate_events_timing(events, start_date, end_date)
        if valid_events:
            logging.info("%d events are within the date range on %d events collected",
                         len(valid_events), len(events))
            matching_events = [EventEntry(**event) for event in valid_events]
            filtered_events = filter_events(matching_events) if not args.export_all else matching_events
            write_events_to_csv(filtered_events, args.output)
        else:
            logging.info("No events are within the date range")

if __name__ == "__main__":
    main()
