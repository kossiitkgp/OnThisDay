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
        self.message = self.max_emoji_msg()
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

        if type_of=="start":
            time_str=time_str+" 00:00"
        else:
            time_str=time_str+" 23:59"

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
        if num<10:
            str_num = "0"+str(num)
        else:
            str_num = str(num)

        return str_num
