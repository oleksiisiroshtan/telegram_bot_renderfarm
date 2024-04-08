#coding=utf-8

# import urllib
import json
import traceback

import cherrypy
from cherrypy import log
import telebot

from config import *
from shelve_data import SaveData
from keyboards import KeyBoarder

from threading import Timer
import time

# таймер отслеживающий пакеты с сервера файлманагера.
# если пакеты не приходят более 2-х - сервер сломан и необходимо сообщить админам
class RepeatTimer(Timer):
	def run(self):
		while not self.finished.wait(self.interval):
			self.function(*self.args,**self.kwargs)

# Наш вебхук-сервер
class WebhookServer(object):
	bot=None
	SD=None
	KB=None
	# farm_status_update=None,
	# farm_renders_update=None,

	LAST_SCREEN={}
	LAST_RENDERS={}
	DICT_GRP_RENDERS={}

	TIMEOUT=None

	def __init__(self, bot, BC):
		self.bot=bot
		self.SD=None
		# self.SD=SD

		self.BC=BC

		# self.farm_status_update=farm_status_update
		# self.farm_renders_update=farm_renders_update

		self.KB = KeyBoarder()

		cherrypy.engine.subscribe('start', self.start)
		cherrypy.engine.subscribe('stop', self.stop)

		self.set_webhook()

		self.timer = RepeatTimer(1*60,self.check_timeout)

		self.timer.start()
		self.running=True

		return


	def log_info(self, msg):
		log(str(msg), "SERVER INFO")

	def log_error(self, msg):
		log(str(msg), "SERVER ERROR")

	def start(self):
		self.log_info("start")
		self.running = True

	def stop(self):
		# правильное выключение потока с таймером
		self.log_info("stop")
		self.running = False
		if self.timer.isAlive():
			self.timer.cancel()
			self.timer.join()

	def check_timeout(self):
		if self.running:
			if not self.TIMEOUT is None:
				#если последний запрос был более чем 20 минут назад
				if time.time() > (self.TIMEOUT+(20*60.0)):
					self.BC.set_err_server()
					self.TIMEOUT=None
		else:
			self.stop()


	def set_webhook(self):
		# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
		self.bot.remove_webhook()
		# Ставим заново вебхук
		self.bot.set_webhook(
			url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
			certificate=open(WEBHOOK_SSL_CERT, 'r')
		)


	@cherrypy.expose
	def index(self):
		self.log_info("cherrypy.request.headers")
		self.log_info(cherrypy.request.headers)
		if 'content-length' in cherrypy.request.headers and \
				'content-type' in cherrypy.request.headers and \
				cherrypy.request.headers['content-type'] == 'application/json':

			length = int(cherrypy.request.headers['content-length'])
			json_string = cherrypy.request.body.read(length).decode("utf-8")

			# self.log_info("json_string")
			# self.log_info(json_string)

			# if json_string.startswith('{"update_id":'):
			try:
				update = telebot.types.Update.de_json(json_string)
				if update:
					self.log_info("update")
					self.log_info(update)
					# Эта функция обеспечивает проверку входящего сообщения
					self.bot.process_new_updates([update])
				return "OK"
			except:
				data = json.loads(json_string)
				if isinstance(data, dict):
					self.log_info("FARM DATA KEYS")
					self.log_info(["%s:%d"%(i, len(data[i])) for i in data.keys()])
					if [i for i in ["LAST_ACTION_ON", "LAST_ACTION_OFF", "LIST_NOT_RESPONDING"] if i in data.keys()]:
						self.TIMEOUT=time.time()
						if data.get("LAST_ACTION_ON"):
							self.BC.set_on_render_node(data["LAST_ACTION_ON"])
						if data.get("LAST_ACTION_OFF"):
							self.BC.set_off_render_node(data["LAST_ACTION_OFF"])
						if data.get("LIST_NOT_RESPONDING"):
							self.BC.set_err_render_node(data["LIST_NOT_RESPONDING"])
						return "OK"
					else:
						if data.get("list_msgs"):
							self.log_info(data.get("list_msgs"))
							for i_msg in data.get("list_msgs"):
								self.BC.send_admins("\U0001f7e5 %s\n%s" % (i_msg["msg_type"].capitalize(), i_msg["msg_txt"]))
						if data.get("list_jobs"):
							self.BC.farm_status_update(data.get("list_jobs"))
						if data.get("list_renders"):
							self.BC.farm_renders_update(data.get("list_renders", []))
						# if data.get("list_broken_renders"):
						self.BC.BROKEN_NODES=data.get("list_broken_renders", [])

						if self.BC.MANAGED_NODES == [] and self.BC.ON_NODES == [] and self.BC.PROHIBITED_NODES == []:
							self.BC.MANAGED_NODES = data.get("MANAGED_NODES", [])
							self.BC.ON_NODES = data.get("ON_NODES", [])
							self.BC.PROHIBITED_NODES = data.get("PROHIBITED_NODES", [])

						if data.get("LIST_NODE_SET_ON"):
							self.BC.set_on_render_node(data["LIST_NODE_SET_ON"],force=True)
						if data.get("LIST_NODE_SET_OFF"):
							self.BC.set_off_render_node(data["LIST_NODE_SET_OFF"],force=True)
						if data.get("LIST_NODE_SET_RESTART"):
							self.BC.set_restart_render_node(data["LIST_NODE_SET_RESTART"],force=True)


						r={
							"MANAGED_NODES":sorted(self.BC.MANAGED_NODES),
							"ON_NODES":sorted(self.BC.ON_NODES),
							"PROHIBITED_NODES":sorted(self.BC.PROHIBITED_NODES),
						}

						if self.BC.LIST_NODE_SET_ON:
							r.update({"LIST_NODE_SET_ON":self.BC.LIST_NODE_SET_ON})
						if self.BC.LIST_NODE_SET_OFF:
							r.update({"LIST_NODE_SET_OFF":self.BC.LIST_NODE_SET_OFF})
						if self.BC.LIST_NODE_SET_RESTART:
							r.update({"LIST_NODE_SET_RESTART":self.BC.LIST_NODE_SET_RESTART})
						self.BC.clear_list_node_command()

						return json.dumps(r)

				elif isinstance(data, (list, tuple)):
					self.BC.farm_status_update(data)
					return "OK!"
				else:
					self.log_error("WRONG CHERRYPY DATA!")
					self.log_error(json_string)
					return "OK!"

		else:
			self.log_info("WRONG cherrypy.request.headers")
			raise cherrypy.HTTPError(403)



def start_server(
		bot,
		BC,
		# farm_status_update,
		# farm_renders_update,
):
	print("Start cherry server")



	# Указываем настройки сервера CherryPy
	cherrypy.config.update({
		'server.socket_host': WEBHOOK_LISTEN,
		'server.socket_port': WEBHOOK_PORT,
		'server.ssl_module': 'builtin',
		'server.ssl_certificate': WEBHOOK_SSL_CERT,
		'server.ssl_private_key': WEBHOOK_SSL_PRIV,

		'log.access_file': "{0}/cherrypy-access.log".format(LOGGER_FOLDER),
		'log.error_file': "{0}/cherrypy-error.log".format(LOGGER_FOLDER),
		#"server.thread_pool" : 10
	})
	WS = WebhookServer(
		bot,
		BC,
		# farm_status_update,
		# farm_renders_update,
	)
	# Собственно, запуск!
	cherrypy.quickstart(
		WS,
		WEBHOOK_URL_PATH,
		{'/': {}}
	)

