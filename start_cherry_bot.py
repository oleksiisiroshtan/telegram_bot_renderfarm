#coding=utf-8
import os
from inspect import getsourcefile
import telebot
from cherrypy import log
import json
import traceback


from config import *
from shelve_data import SaveData
from keyboards import KeyBoarder
from bot_class import BotFunc
from cherry_webhook_server import start_server

print("START")

START_SCRIPT_FOLDER=os.path.split(os.path.abspath(getsourcefile(lambda:0)))[0]

LAST_SCREEN={}
LAST_RENDERS={}
DICT_GRP_RENDERS={}

SD = SaveData(START_SCRIPT_FOLDER)
KB = KeyBoarder()

WS =None

bot = telebot.TeleBot(token)

BF = BotFunc(bot, SD)

def log_info(msg):
	log(str(msg), "START INFO")

@bot.message_handler(commands=['info'])
def start_message(message):
	BF.info_message(message)


@bot.message_handler(commands=['start'])
def start_message(message):
	BF.start_message(message)


# Хэндлер на все текстовые сообщения в окне Бота
@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
	BF.get_func_from_button(message.text, message)


# Хэндлер на все текстовые сообщения в окне Канала
@bot.channel_post_handler(func=lambda channel_post: True, content_types=['text'])
def echo_chat(channel_post):
	log_info("chat id")
	log_info(channel_post.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
	BF.callback_inline(call)


try:
	WS = start_server(
		bot,
		BF,
	)
except Exception:
	log("%s:\n%s"%(
		"ERROR",
		str(traceback.format_exc()),
	))

print("END")