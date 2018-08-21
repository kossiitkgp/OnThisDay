import os
import time
import datetime

import slackclient as slck

CH_NAME = 0
CH_ID = 1
MSG_CONTENT = 0
MSG_CH = 1
MSG_CREATOR = 2
MSG_REACTS = 3


class OnThisDay:

    def __init__(self):

        self.now = datetime.datetime.now()
        self.client = slck.SlackClient(os.getenv('SLACK_BOT_TOKEN'))
        self.channel_list = self.list_channels()
        self.messages_ch_list = self.list_messages()
        self.message = self.messages_ch_list[self.max_emoji_msg()]
        self.post_msg()

    def list_channels(self):
        """
        lists all the channels of the workspace

        :return:
        ch_list
        type: list of tuple (channel name, channel id)

        """
        ch_list = []
        ch_dict = self.client.api_call(method="https://slack.com/api/channels.list")
        for ch in ch_dict["channels"]:
            ch_list.append((ch["name"], ch["id"]))

        return ch_list

    def list_messages(self):
        """
        lists all the messages for the day of all channels

        :return:
        msg_list
        type: list of tuple (msg, msg_channel, msg_creator, msg_reacts)

        """
        list_msgs = []
        for ch in self.channel_list:
            ch_hist = self.client.api_call(method="https://slack.com/api/channels.history",
                                           channel=ch[CH_ID],
                                           count=1000,
                                           latest=self.time("start"),
                                           oldest=self.time("end")
                                           )
            for msg in ch_hist["messages"]:
                if msg["type"] == "message":
                    content = msg["text"]
                    user = msg["user"]
                    reacts = msg.get("reactions", 0)

                    list_msgs.append((content, ch[CH_NAME], user, reacts))

        return list_msgs

    def max_emoji_msg(self):
        """
        finds the index of the message with the highest number of reactions

        :return:
        msg_index
        type: int

        """
        max_reacts = 0
        msg_index = 0
        for index, msg in enumerate(self.messages_ch_list):
            if msg[MSG_REACTS] > max_reacts:
                msg_index = index
                max_reacts = msg[MSG_REACTS]

        return msg_index

    def post_msg(self):
        """
        sends the selected message to the 'random' slack channel

        :return:
        NONE

        """
        for ch in self.channel_list:
            if ch[CH_ID] == self.message[MSG_CH]:
                channel_name = ch[CH_NAME]
                break
        msg = "Here's what was trending OnThisDay!\n\n>"\
              + self.message[MSG_CONTENT]+"\n\n-- by " + \
              self.message[MSG_CREATOR] + " in #"+channel_name
        response = self.client.api_call(method="https://slack.com/api/chat.postMessage",
                                        channel=msg[MSG_CH],
                                        text=msg
                                        )
        if response["ok"]:
            print("nostalgia spread!")
        else:
            print("failed to invoke memories!")

    def time(self, type_of):
        """
        converts current date, last year, 23:59 (or 00:01) to timestamp recognised by slack.

        :param type_of: whether the start time or end time is required
        :return:
        start_time
        type: string (slack timestamp)

        """
        year = str(self.now.year - 1)
        month = self._convert(self.now.month)
        day = self._convert(self.now.day)
        time_str = day+"/"+month+"/"+year

        if type_of == "start":
            time_str = time_str+" 00:00"
        else:
            time_str = time_str+" 23:59"

        start_time = time.mktime(datetime.datetime.strptime(time_str, "%d/%m/%Y %H:%M").timetuple())
        return start_time

    @staticmethod
    def _convert(num):
        """
        converts "9" to "09"

        :param num: integer to be converted
        :return:
        str_num: string with modified integer

        """
        if num < 10:
            str_num = "0"+str(num)
        else:
            str_num = str(num)

        return str_num

if __name__ == "__main__":
    OnThisDay()