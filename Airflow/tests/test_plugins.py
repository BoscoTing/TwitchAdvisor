import pytest
from unittest.mock import Mock, patch
from plugins.viewers_reaction import ViewersReactionAnalyser

analyser = ViewersReactionAnalyser('test_channel')

def test_recognize_cheers():

    line = "2023-10-16_12:34:56 — 2023-10-16T12:34:56+08:00 — 1000 —:sammie_leigh!sammie_leigh@sammie_leigh.tmi.twitch.tv PRIVMSG #sacriel :Have a great night chat and Sac! sacLOVE See you all tomorrow!TestCheer100 TestCheer200"
    result = analyser.recognize_cheers(line)
    assert result == {"TestCheer": 300}

def test_parse_chat_logs():

    line = "2023-10-16_12:34:56 — 2023-10-16T12:34:56+08:00 — 1000 —:sammie_leigh!sammie_leigh@sammie_leigh.tmi.twitch.tv PRIVMSG #sacriel :Have a great night chat and Sac! sacLOVE See you all tomorrow!"
    result = analyser.parse_chat_logs(line)

    assert "message" in result and result["message"] == "Have a great night chat and Sac! sacLOVE See you all tomorrow!"
    assert "cheer" in result and result["cheer"] == {}
    assert "viewerCount" in result and result["viewerCount"] == 1000
    assert "userName" in result and result["userName"] == "sammie_leigh"


@patch('your_module.ChatLogsManager.parse_chat_logs')
@patch('your_module.ChatLogsManager.db.connect_collection')
@patch('os.path.exists')
@patch('builtins.open', create=True)
def test_insert_chat_logs(
    mock_open, mock_exists, mock_connect_collection, mock_parse_chat_logs, chat_logs_manager
):
    # Mock your database connection and method
    db = Mock()
    mock_connect_collection.return_value = db

    # Mock the 'os.path.exists' function to return True (you can change this for different test cases)
    mock_exists.return_value = True

    # Mock the 'open' function to return a sample log content
    mock_open.return_value.__enter__.return_value.read.return_value = "Sample chat log content"

    # Mock the 'parse_chat_logs' method to return a sample document
    mock_parse_chat_logs.return_value = {"field1": "value1", "field2": "value2"}

    # Call the function to test
    chat_logs_manager.insert_chat_logs()

    # Assert that the expected methods were called
    mock_connect_collection.assert_called_once_with("taskRecords")
    db.insertmany_into_collection.assert_called_once()
    db.insertone_into_collection.assert_called_once()
