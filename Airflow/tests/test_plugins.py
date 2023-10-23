import datetime
import pytest
from unittest.mock import Mock
from ..plugins.viewers_reaction import ViewersReactionAnalyser

@pytest.fixture
def analyser():
    channel = "test_channel"
    return ViewersReactionAnalyser(channel)

analyser = ViewersReactionAnalyser('test_channel')

def test_recognize_cheers(analyser):
    line = "TestCheer100 TestCheer200"

    analyser.listener = Mock()
    analyser.listener.recognize_cheers.return_value = {"TestCheer": 300}

    # Test the function
    result = analyser.recognize_cheers(line)
    assert result == {"TestCheer": 300}

def test_parse_chat_logs(analyser):
    line = "2023-10-16_12:34:56—2023-10-16T12:34:56+08:00—1000—TestUser : Test message"
    result = analyser.parse_chat_logs(line)

    assert "message" in result and result["message"] == "Test message"
    assert "cheer" in result and result["cheer"] == {}
    assert "viewerCount" in result and result["viewerCount"] == 1000
    assert "userName" in result and result["userName"] == "TestUser"

def test_insert_chat_logs(analyser):
    analyser.db = Mock()
    analyser.db.connect_collection.return_value = Mock()
    analyser.db.insertmany_into_collection.return_value = True
    analyser.insert_chat_logs()

    analyser.db.connect_collection.assert_called_once()
    analyser.db.insertmany_into_collection.assert_called_once()

def test_historical_stats(analyser):
    started_at = "2023-10-16T12:34:56+08:00"
    analyser.db = Mock()
    analyser.db.connect_collection.return_value = Mock()
    analyser.db.connect_collection().aggregate.return_value = [{"_id": datetime.datetime(2023, 10, 16, 12, 30), "messages": ["Test message"]}]

    result = analyser.historical_stats(started_at)

    assert isinstance(result, list) and len(result) == 1
    assert "messages" in result[0] and result[0]["messages"] == ["Test message"]

def test_insert_historical_stats(analyser):
    analyser.db = Mock()
    analyser.db.connect_collection.return_value = Mock()
    analyser.db.connect_collection().aggregate.return_value = [{"_id": datetime.datetime(2023, 10, 16, 12, 30), "messages": ["Test message"]}

    analyser.historical_stats = Mock()
    analyser.historical_stats.return_value = [{"_id": datetime.datetime(2023, 10, 16, 12, 30), "messages": ["Test message"]}

    analyser.db.insertmany_into_collection.return_value = True

    analyser.insert_historical_stats()

    analyser.db.connect_collection.assert_called()
    analyser.historical_stats.assert_called()
    analyser.db.insertmany_into_collection.assert_called()
