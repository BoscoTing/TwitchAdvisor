from chatroom_sentiment import ChatroomSentiment
from viewers_reaction import ViewersReactionAnalyser

def organize_data(channel):
    ChatroomSentiment.analyse_new_messages()
    ViewersReactionAnalyser(channel).query_chat_logs()
    