from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone


class ReportingPeriod:
    def __init__(self, start_datetime=None, end_datetime=None, short=''):
        if short.startswith('last') and short.endswith('days'):
            period = self.parse_reporting_period(short)
            self.start_datetime = period.start_datetime
            self.end_datetime = period.end_datetime
        elif start_datetime and end_datetime:
            self.start_datetime = start_datetime
            self.end_datetime = end_datetime
        else:
            raise AssertionError('Must specify start_datetime and end_datetime, or short string. Got: {}'.format(short))

    @staticmethod
    def parse_reporting_period(p: str) -> ReportingPeriod:
        logger = logging.getLogger('ReportingPeriod')
        if p.startswith('last') and p.endswith('days'):
            period = ReportingPeriod(
                start_datetime=datetime.now(tz=timezone.utc) -
                               timedelta(days=int(p.replace('last', '').replace('days', ''))),
                end_datetime=datetime.now(tz=timezone.utc))
        elif re.match('\\d{4}-\\d{2}-\\d{2}[+-]\\d{4}:\\d{4}-\\d{2}-\\d{2}[+-]\\d{4}', p):
            start_date = p.split(':')[0]
            end_date = p.split(':')[1]
            period = ReportingPeriod(
                start_datetime=datetime.strptime(start_date, '%Y-%m-%d%z'),
                end_datetime=datetime.strptime(end_date, '%Y-%m-%d%z'))
        else:
            raise AssertionError('Invalid reporting period. Got: {}'.format(p))

        logger.info("Reporting period start={} end={}".format(period.start_datetime, period.end_datetime))
        reporting_period_days = (period.end_datetime - period.start_datetime).days
        if reporting_period_days <= 0:
            raise ValueError(
                'Invalid reporting period duration. Reporting period days={}'.format(reporting_period_days))
        return period


class Metrics:
    logger = logging.getLogger('metrics')

    def calculate_commits_per_iso_week(self, commits) -> dict:
        ending_week = datetime.now().isocalendar()[1] + 1
        commits_per_iso_week = dict(zip(range(1, ending_week), [0] * ending_week))
        for commit in commits:
            week_of_year = commit.committer.date.isocalendar().week
            commits_per_iso_week[week_of_year] += 1
        return commits_per_iso_week

    def calculate_commits_per_repository(self, commits, reporting_window: ReportingPeriod = None) -> int:
        if reporting_window:
            filtered_commits = filter(
                lambda c: (reporting_window.start_datetime < c.committer.date <= reporting_window.end_datetime),
                commits)
            return len(list(filtered_commits))
        return len(list(commits))

    """
    Calculates average days between tags in each repository. If there is only one tag, None will be returned.
    :param tags_by_repository: Tag information by repository.
    """

    def calculate_average_tag_time_per_repository(self, tags_by_repository: dict) -> dict:
        average_tag_days_per_repository = {}
        # Calculate average tag time.
        for repo_name, tags in tags_by_repository.items():
            last_tag_date = None
            average_days_since_last_tag = None
            for tag_name in tags.keys():
                current_tag_date = tags[tag_name]['date']
                if last_tag_date:
                    days_since_last_tag = (current_tag_date - last_tag_date).days
                    self.logger.debug("Repo: {}, tag: {}, date: {}, since_last: {} days".format(
                        repo_name, tag_name, tags[tag_name]['date'], days_since_last_tag))
                    average_days_since_last_tag = days_since_last_tag \
                        if not average_days_since_last_tag else average_days_since_last_tag + days_since_last_tag / 2
                else:
                    self.logger.debug("Repo: {}, tag: {}, date: {}, since_last: {} days".format(
                        repo_name, tag_name, current_tag_date, 0))
                last_tag_date = current_tag_date
            average_tag_days_per_repository[repo_name] = average_days_since_last_tag

        return average_tag_days_per_repository
