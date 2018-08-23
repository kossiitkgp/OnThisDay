import os
import sys
import time
import datetime

import slackclient as slck

CH_NAME = 0
CH_ID = 1
MSG_CONTENT = 0
MSG_CH = 1
MSG_CREATOR = 2
MSG_REACTS = 3
MSG_LINK = 3


class OnThisDay:

    def __init__(self):

        self.now = datetime.datetime.now()
        # print(self.now)
        self.client = slck.SlackClient(os.getenv('SLACK_BOT_TOKEN'))
        print("Slack bot authenticated!\nrequesting channel list...")
        self.channel_list = self.list_channels()
        print("{num} channels received!\nQuerying channels...".format(
            num=len(self.channel_list)
        ))
        # print(self.channel_list)
        self.messages_ch_list = self.list_messages("year")
        if len(self.messages_ch_list) == 0:
            self.messages_ch_list = self.list_messages("month")

        if len(self.messages_ch_list) > 0:
            self.message = self.messages_ch_list[self.max_emoji_msg()]
            self.decorated_message = self.decorate_msg()
            self.post_msg()
        else:
            msg = "DAMN! You guys should be talking more..."
            channel_id = 'random'
            for ch in self.channel_list:
                if ch[CH_NAME] == 'random':
                    channel_id = ch[CH_ID]
                    break
            self.client.api_call(method="chat.postMessage",
                                 channel=channel_id,
                                 text=msg,
                                 username="Mnemosyne"
                                 )

    def list_channels(self):
        """
        lists all the channels of the workspace

        :return:
        ch_list
        type: list of tuple (channel name, channel id)

        """
        ch_list = []
        ch_dict = self.client.api_call(method="channels.list")
        try:
            for ch in ch_dict["channels"]:
                ch_list.append((ch["name"], ch["id"]))
        except KeyError:
            print("Authentication failed!\nPlease check your OAuth environment variable.")
            sys.exit(1)

        return ch_list

    def list_messages(self, time_frame):
        """
        lists all the messages for the day of all channels

        :param time_frame: (str) specifies if the data is to be collected for past year or past month

        :return:
        msg_list
        type: list of tuple (msg, msg_channel, msg_creator, msg_reacts)

        """
        list_msgs = []
        for ch in self.channel_list:
            for x in range(6):
                ch_hist = self.client.api_call(method="channels.history",
                                               channel=ch[CH_ID],
                                               count=1000,
                                               inclusive=True,
                                               latest=self.time("end", time_frame, x),
                                               oldest=self.time("start", time_frame, x)
                                               )
                print("Data for {ch} fetched under {frame} (interation: {iter}) time-frame with {num} messages".format(
                    ch=ch[CH_NAME],
                    frame=time_frame,
                    iter=x,
                    num=len(ch_hist.get("messages", []))
                ))
                if ch_hist is not None:
                    for msg in ch_hist["messages"]:
                        if msg["type"] == "message":
                            content = msg.get("text", "false")
                            user = msg.get("user", "user detection failed")
                            reacts = msg.get("reactions", [])
                            reacts_count = 0
                            for reaction in reacts:
                                reacts_count += reaction.get('count', 0)

                            list_msgs.append((content, ch[CH_NAME], user, reacts_count))

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
            # print(msg)
            if msg[MSG_REACTS] > max_reacts:
                msg_index = index
                max_reacts = msg[MSG_REACTS]

        return msg_index

    def decorate_msg(self):
        """
        Using search method of Slack API, returns a better metadata for the message

        :return:
        decorated_msg
        type: (content, channel, creator, link)
        """
        msg_metadata = self.client.api_call('search.messages',
                                            query=self.message[MSG_CONTENT],
                                            )
        print(msg_metadata)
        if msg_metadata["ok"]:
            msg_metadata = msg_metadata["messages"]['matches'][0]
            decorated_msg = (
                msg_metadata["text"],
                msg_metadata["channel"]["name"],
                msg_metadata["username"],
                msg_metadata["permalink"]
            )
        else:
            print("message decoration failed!")
            sys.exit(1)

        return decorated_msg

    def post_msg(self):
        """
        sends the selected message to the 'random' slack channel

        :return:
        NONE

        """
        channel_id = 'random'
        for ch in self.channel_list:
            if ch[CH_NAME] == 'random':
                channel_id = ch[CH_ID]
                break
        msg = "Here's what was trending OnThisDay!\n\n>"\
              + self.decorated_message[MSG_CONTENT]+"\n\n-- by @" + \
              self.decorated_message[MSG_CREATOR] + " in #" + \
              self.decorated_message[MSG_CH] + "\n\n" + \
              self.decorated_message[MSG_LINK]
        response = self.client.api_call(method="chat.postMessage",
                                        channel=channel_id,
                                        text=msg,
                                        link_names=True,
                                        username="Mnemosyne"
                                        )
        if response["ok"]:
            print("Yay, nostalgia spread!")
        else:
            print("failed to invoke memories!")

    def time(self, type_of, time_frame, iter_value):
        """
        converts current date, last year, 23:59 (or 00:01) to timestamp recognised by slack.

        :param type_of: whether the start time or end time is required
        :param time_frame: specified if year is to be decreased or month
        :param iter_value: specifies the amount by which year/month is to be decreased

        :return:
        start_time
        type: string (slack timestamp)

        """
        if time_frame == "year":
            year = str(self.now.year - 1 - iter_value)
            month = self._convert(self.now.month)
        else:
            year = str(self.now.year)
            month = self._convert(self.now.month - 1 - iter_value)
        day = self._convert(self.now.day)
        time_str = day+"/"+month+"/"+year

        if type_of == "start":
            time_str = time_str+" 00:01"
        else:
            time_str = time_str+" 23:59"
        # print(time_str)

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
