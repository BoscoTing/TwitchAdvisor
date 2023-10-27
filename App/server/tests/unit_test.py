from datetime import datetime
import pytest

from ..services.history_stats import ViewersReactionAnalyser, Overview

def test_get_livestream_schedule():
    overview = Overview()
    week = 40
    year = 2023
    
    processed_data = overview.get_livestream_schedule(week, year)
    for doc in processed_data:
        assert isinstance(doc, dict)  # Check if each item is a dictionary
        assert 'avgSentimentScore' in doc and isinstance(doc['avgSentimentScore'], (float, type(None)))
        assert 'maxMessageCount' in doc and isinstance(doc['maxMessageCount'], int)
        assert 'avgMessageCount' in doc and isinstance(doc['avgMessageCount'], float)
        assert 'avgViewerCount' in doc and isinstance(doc['avgViewerCount'], (float, type(None)))
        assert 'maxViewerCount' in doc and isinstance(doc['maxViewerCount'], (float, type(None)))
        assert 'totCheerCount' in doc and isinstance(doc['totCheerCount'], int)
        assert 'channel' in doc and isinstance(doc['channel'], str)
        assert 'year' in doc and isinstance(doc['year'], int)
        assert 'month' in doc and isinstance(doc['month'], int)
        assert 'dayOfMonth' in doc and isinstance(doc['dayOfMonth'], int)
        assert 'weekDay' in doc and isinstance(doc['weekDay'], int)
        assert 'weekOfMonth' in doc and isinstance(doc['weekOfMonth'], int)
        assert 'weekOfYear' in doc and isinstance(doc['weekOfYear'], int)
        assert 'weekDayName' in doc and isinstance(doc['weekDayName'], str)

        assert 'startedAtUnixTimestamp' in doc and isinstance(doc['startedAtUnixTimestamp'], float)
        assert 'startedAt' in doc and isinstance(doc['startedAt'], str)
        expected_format = '%Y-%m-%dT%H:%M:%S+08:00'
        try:
            datetime.strptime(doc['startedAt'], expected_format)
        except ValueError:
            assert False, f"Invalid 'startedAt' format: {doc['startedAt']}"

def test_get_schedule_week_range():
    overview = Overview()
    schedule_range_list = overview.get_schedule_week_range()

    assert len(schedule_range_list) == 2
    for year_week in schedule_range_list:
        assert year_week.startswith('2023-W')
        week_number = int(year_week.split('-W')[1])
        assert 1 <= week_number <= 53

def test_query_historical_stats_with_started_at():
    analyser = ViewersReactionAnalyser('sneakylol')
    started_at = '2023-10-16T13:05:13+08:00'
    result = analyser.query_historical_stats(started_at)

    assert isinstance(result, list)
    assert isinstance(result[0], dict)  # Check if it's a dictionary

    doc = result[0]
    assert 'timestamp' in doc and isinstance(doc['timestamp'], datetime)
    assert '_id' in doc and isinstance(doc['_id'], datetime)
    assert 'cheers' in doc and isinstance(doc['cheers'], list)
    assert 'averageViewerCount' in doc and isinstance(doc['averageViewerCount'], (float, type(None)))
    assert 'messages' in doc and isinstance(doc['messages'], list)
    assert 'startedAt' in doc and isinstance(doc['startedAt'], str)
    assert 'chatterCount' in doc and isinstance(doc['chatterCount'], int)
    assert 'channel' in doc and isinstance(doc['channel'], str)
    assert 'messageCount' in doc and isinstance(doc['messageCount'], int)

    expected_started_at_format = '%Y-%m-%dT%H:%M:%S+08:00'
    assert datetime.strptime(doc['startedAt'], expected_started_at_format)  # Check if startedAt matches the expected format


def test_query_historical_stats_without_started_at():
    analyser = ViewersReactionAnalyser('sneakylol')
    result = analyser.query_historical_stats(None)

    assert isinstance(result, list)  # Check if the result is a list
    assert isinstance(result[0], dict)  # Check if it's a dictionary

    doc = result[0]
    assert 'timestamp' in doc and isinstance(doc['timestamp'], datetime)
    assert '_id' in doc and isinstance(doc['_id'], datetime)
    assert 'cheers' in doc and isinstance(doc['cheers'], list)
    assert 'averageViewerCount' in doc and isinstance(doc['averageViewerCount'], (float, type(None)))
    assert 'messages' in doc and isinstance(doc['messages'], list)
    assert 'startedAt' in doc and isinstance(doc['startedAt'], str)
    assert 'chatterCount' in doc and isinstance(doc['chatterCount'], int)
    assert 'channel' in doc and isinstance(doc['channel'], str)
    assert 'messageCount' in doc and isinstance(doc['messageCount'], int)

    expected_started_at_format = '%Y-%m-%dT%H:%M:%S+08:00'
    assert datetime.strptime(doc['startedAt'], expected_started_at_format)  # Check if startedAt matches the expected format