import logging
import sys
from datetime import datetime, timedelta

import plotly.graph_objects as go
import yaml
from plotly.subplots import make_subplots

from git import get_git_log, list_git_tags_per_repository, setup_git
from metrics import Metrics, ReportingPeriod

logger = logging.getLogger()
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

if __name__ == '__main__':
    with open('repos.yml', 'r') as f:
        config = yaml.load(f.read(), Loader=yaml.FullLoader)

    if not config:
        logging.error("Error loading config.yaml!")
        exit(1)

    git_config = setup_git(config)

    # repos = [(r['name'], r['path']) for r in config['repositories']]
    repos = [(name, path) for name, path in git_config['repositories'].items()]
    reporting_period = config['config']['reporting_period']
    reporting_period_days = ReportingPeriod.parse_reporting_period(reporting_period)
    plot = config['config']['plot']
    tags_by_repository = {}

    metrics = Metrics()
    # Global metrics
    commits_per_repository = {}
    commits_per_iso_week = {}
    average_tag_time_per_repository = {}
    average_tag_time = 0
    # Reporting period metrics
    commits_per_repository_last_reporting_period = {}
    commits_per_repository_per_day = {}
    commits_per_day = 0

    for repo_name, repo_path in repos:
        logger.info("Processing repository: %s", repo_name)
        git_commits = get_git_log(repo_path)

        commits_per_iso_week = metrics.calculate_commits_per_iso_week(git_commits)
        commits_per_repository[repo_name] = commits_per_repository.get(repo_name, 0) \
                                            + metrics.calculate_commits_per_repository(git_commits)

        # reporting window calculations
        commits_per_repository_last_reporting_period[repo_name] = metrics.calculate_commits_per_repository(
            git_commits, reporting_window=ReportingPeriod(short=reporting_period))
        total_commits_in_reporting_window = 0
        for repo, commit_count in commits_per_repository_last_reporting_period.items():
            commits_per_repository_per_day[repo] = commit_count / reporting_period_days
            total_commits_in_reporting_window += commit_count
        commits_per_day = total_commits_in_reporting_window / reporting_period_days

        # tag metrics
        tags_by_repository[repo_name] = list_git_tags_per_repository(repo_path)

    logger.debug("Total commits in date range: %s", commits_per_repository_last_reporting_period)
    logger.debug("Commits by week of year: %s", commits_per_iso_week)
    logger.debug("Commits by repository: %s", commits_per_repository)
    logger.debug("Commits by repository per day: %s", commits_per_repository_per_day)
    logger.debug("Commits per day: {:.2f}".format(commits_per_day))

    # Calculate average tag time.
    average_tag_time_per_repository = metrics.calculate_average_tag_time_per_repository(tags_by_repository)

    # Plots
    if plot:
        logger.info("Generating plots...")
        fig = make_subplots(2, 2)
        fig.add_trace(
            go.Bar(
                y=list(commits_per_repository_last_reporting_period.keys()),
                x=list(commits_per_repository_last_reporting_period.values()),
                orientation='h', showlegend=False,
                text=list(commits_per_repository_last_reporting_period.values()), textposition='auto',
            ),
            row=1, col=1)
        fig['layout']['xaxis']['title'] = 'Commits'

        fig.add_trace(
            go.Bar(
                y=list(commits_per_repository_per_day.keys()),
                x=list(commits_per_repository_per_day.values()),
                orientation='h', showlegend=False,
                text=[round(v, 2) for v in commits_per_repository_per_day.values()], textposition='auto',
            ),
            row=1, col=2)
        fig['layout']['xaxis2']['title'] = 'Average commits per day'

        fig.add_trace(
            go.Bar(
                x=[datetime.strftime(datetime.fromisocalendar(datetime.now().year, w, 1),
                                     '%D') for w in commits_per_iso_week.keys()],
                y=list(commits_per_iso_week.values()),
                text=list(commits_per_iso_week.values()), textposition='auto',
                showlegend=False,
            ),
            row=2, col=1)
        fig['layout']['xaxis3']['title'] = 'Week'
        fig['layout']['yaxis3']['title'] = 'Commits'

        fig.add_trace(
            go.Bar(
                x=[x for x, y in average_tag_time_per_repository.items() if y],
                y=[y for y in average_tag_time_per_repository.values() if y],
                text=[round(v, 2) for v in average_tag_time_per_repository.values() if v],
                textposition='auto',
                showlegend=False,
            ),
            row=2, col=2)
        fig['layout']['yaxis4']['title'] = 'Average tag time (days)'
        title = 'Reporting period: {} - {}'.format(datetime.now().strftime('%D'),
                                                   (datetime.now() - timedelta(days=reporting_period_days)).strftime(
                                                       '%D'))
        fig.update_layout(title_text=title)
        # fig.update_layout(height=600, width=800, title_text="Repository metrics")
        fig.show()
