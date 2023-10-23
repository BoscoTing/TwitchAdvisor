import pytest

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