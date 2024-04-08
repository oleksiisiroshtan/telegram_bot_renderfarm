#coding=utf-8

import json
import traceback

import cherrypy
from cherrypy import log
import telebot

from config import *
from keyboards import KeyBoarder, DICT_BUTTONS



# Наш вебхук-сервер
class BotFunc:#(object):
	bot=None
	SD=None
	KB=None

	LAST_SCREEN=None
	LAST_RENDERS={}
	DICT_GRP_RENDERS={}


	MANAGED_NODES=[]
	BROKEN_NODES=[]
	ON_NODES=[]
	PROHIBITED_NODES=[]

	LIST_NODE_SET_ON=[]
	LIST_NODE_SET_OFF=[]
	LIST_NODE_SET_RESTART=[]


	def __init__(self, bot, SD):
		self.bot=bot
		self.SD=SD

		self.KB = KeyBoarder()
		self.DICT_BUTTONS = dict(DICT_BUTTONS)
		self.LIST_ALLOWED_USER_IDS=self.SD.get_allowed_user_ids()
		self.LIST_ADMIN_ID = LIST_ADMIN_ID
		self.LIST_ADMIN_ID.extend(self.SD.get_admins())
		self.LIST_ADMIN_ID = list(set(self.LIST_ADMIN_ID))
		return


	def log_info(self, msg):
		log(str(msg), "CLASS INFO")

	def log_error(self, msg):
		log(str(msg), "CLASS ERROR")

	def clear_list_node_command(self):
		self.LIST_NODE_SET_ON=[]
		self.LIST_NODE_SET_OFF=[]
		self.LIST_NODE_SET_RESTART=[]

	def is_new(self, new_job, old_job):
		return not new_job.get("time_creation") == old_job.get("time_creation")

	def is_restart(self, new_job, old_job):
		n = new_job.get("time_started")
		if n is None:
			n=0
		o = old_job.get("time_started")
		if o is None:
			o=0
		return int(n) != int(o)

	def is_run(self, new_job, old_job=None):
		if old_job and "RUN" in new_job.get("state") and not "RUN" in old_job.get("state"):
			return True
		elif not old_job and "RUN" in new_job.get("state"):
			return True
		else:
			return False

	def is_don(self, new_job, old_job=None):
		if old_job and "DON" in new_job.get("state") and not "DON" in old_job.get("state"):
			return True
		elif not old_job and "DON" in new_job.get("state"):
			return True
		else:
			return False

	def is_err(self, new_job, old_job=None):
		if old_job and "ERR" in new_job.get("state") and not "ERR" in old_job.get("state"):
			return True
		elif not old_job and "ERR" in new_job.get("state"):
			return True
		else:
			return False

	def get_emoji_from_state(self, state):
		if "DELETE" in state:
			return "\U0000274C " # красный крест
		elif "OFF" in state:
			return "\U000025FB " # серый
		elif "ERR" in state:
			# return "\U0001f7e5 \U0001f7e6 \U0001f7e7 \U0001f7e8 \U0001f7e9 \U0001f7ea \U0001f7eb \U0001f7ec \U0001f7ed \U0001f7ee \U0001f7ef"
			return "\U0001f7e5 " # красный
		# return "\U000025FB"
		elif "DON" in state:
			return '\U0001f7e9 ' # зеленый
		elif "WDP" in state:
			return '\U0001f7ea ' # фиолетовый
		elif "RUN" in state:
			return '\U0001f7e8 ' # желтый
		elif "RDY" in state:
			return "\U000025FB " # серый
		elif "WTM" in state:
			return '\U0001f7e6 ' # синий
		# return "\U0001f7e0"!!!
		# return ":red_circle:"
		# return "\U0001F609" !!!!!!!!!!!!!!!!!
		# return emoji.emojize(':white_check_mark:')
		else:
			return ''
	# return '\U0001f7ea'

	def get_node_color_from_state(self, state):
		r_state=""
		if "OFF" in state:
			r_state+="\U000025FB" #Grey
		elif "NBY" in state:
			r_state+= "\U0001f7e6" #Blue
		elif "NbY" in state:
			r_state+= "\U0001f7e6" #Blue
		elif "ONL" in state:
			r_state+= "\U0001f7e9" #Green
		elif "RUN" in state:
			r_state+= "\U0001f7e8" #Yelow
		return r_state


	def get_node_name(self, node_name):
		return node_name.split(".")[0]

	def get_group_from_render_node(self, node_name):
		grp_name = self.get_node_name(node_name)
		for i in range(1, len(grp_name)):
			if not grp_name[-1*i].isdigit():
				if -1*i+1 != 0:
					grp_name = grp_name[:-1*i+1]
				break
		return grp_name


	def send_text_format(self, id, text, reply_markup=None):
		try:
			if any([ i in text for i in ["<b>", ]]):
				text = (text.replace("<b>", "{0}").replace("</b>", "{1}").replace(">","").replace("<","")).format("<b>", "</b>")
				self.bot.send_message(
					id,
					text,
					reply_markup=reply_markup,
					parse_mode="HTML",)
			else:
				self.bot.send_message(
					id,
					text,
					reply_markup=reply_markup,)
		except:
			str_text_err = str(traceback.format_exc())
			if "bot was blocked by the user" in str_text_err:
				pass
			else:
				raise Exception()

	def send_user(self, id, text, reply_markup=None, parse_mode="HTML"):
		self.log_info("send_user")
		self.send_text_format(id, text, reply_markup)

	def send_channel(self, text):
		self.log_info("send_channel")
		self.send_text_format(CHANNAL_ID, text)

	def send_admins(self, text, kb=None):
		self.log_info("send_admins")
		for iID in self.LIST_ADMIN_ID:
			self.send_text_format(iID, text, kb)

	def msg_bot_reboot(self):
		# self.send_channel(MSG_REBOOT_TEMPLATE)
		self.send_admins(MSG_REBOOT_TEMPLATE)

	def get_id_user_from_af_name(self, af_user):
		d_user = self.SD.DICT_AF_USER.get(af_user)
		if d_user:
			return list(d_user.keys())
		else:
			return []

	def get_username(self, af_user):
		# TODO дописать проверку через БД

		d_user = self.SD.DICT_AF_USER.get(af_user)
		if d_user:
			l_user = str([ i for i in d_user.values() ])
			return "%s == %s"%(af_user, l_user)
		else:
			return af_user


	def add_admin(self, message, *args, **kwargs):
		self.log_info("add_admin")
		markup = self.KB.start_cmds(admin=message.from_user.id in self.LIST_ADMIN_ID)
		try:
			if message.from_user.id in self.LIST_ADMIN_ID:
				if kwargs.get("id_new_admin") in self.LIST_ALLOWED_USER_IDS:
					if message.text == "Confirm":
						self.log_info("id_new_admin: %s" % kwargs.get("id_new_admin"))
						self.log_info("LIST_ALLOWED_USER_IDS: %s" % self.LIST_ALLOWED_USER_IDS)
						if kwargs.get("id_new_admin") not in self.LIST_ADMIN_ID:
							self.LIST_ADMIN_ID = self.SD.save_admin_ids(self.LIST_ADMIN_ID+[kwargs.get("id_new_admin"),] )
							self.send_user(int(kwargs.get("id_new_admin")), "You have been granted administrator rights", reply_markup=None)
							self.send_user(message.from_user.id, "User set as administrator", reply_markup=markup)
						else:
							self.send_user(message.from_user.id, "The user is already an administrator", reply_markup=markup)
					else:
						self.send_user(message.from_user.id, "Choose another action", reply_markup=markup)
				else:
					self.send_user(message.from_user.id, "This user is not registered", reply_markup=markup)
			else:
				self.send_user(message.from_user.id, "You can't do it", reply_markup=markup)
		except Exception:
			self.send_admins("ERROR \"add_admin\":\n%s"%str(traceback.format_exc()))

	def delete_user(self, message, *args, **kwargs):
		self.log_info("delete_user")
		markup = self.KB.start_cmds(admin=message.from_user.id in LIST_ADMIN_ID)
		try:
			if message.text == "Confirm":
				if kwargs.get("delete_id") in self.LIST_ALLOWED_USER_IDS:
					del(self.LIST_ALLOWED_USER_IDS[self.LIST_ALLOWED_USER_IDS.index(kwargs.get("delete_id"))])
					self.SD.save_allowed_user_ids(self.LIST_ALLOWED_USER_IDS)
				if kwargs.get("delete_id") in LIST_ADMIN_ID:
					del(LIST_ADMIN_ID[LIST_ADMIN_ID.index(kwargs.get("delete_id"))])
				self.send_user(int(kwargs.get("delete_id")), "Access blocked", reply_markup=None)
				self.send_user(message.from_user.id, "User delete. Choose another action", reply_markup=markup)
			else:
				self.send_user(message.from_user.id, "Choose another action", reply_markup=markup)

		except Exception as e:
			self.send_admins("ERROR \"delete_user\":\n%s"%str(traceback.format_exc()))

	def print_node_info(self, message, node_name, node_data):

		def get_template_1(data, template):
			if data.get("address",{}).get("ip"):
				template += "\n"+MSG_NODE_TEMPLATE["ip"]%data["address"]["ip"]
			if data.get("state"):
				template += "\n" + MSG_NODE_TEMPLATE["state"]%( " ".join([
					self.get_node_color_from_state(data["state"]),
					data["state"]
				]))
			if data.get("host",{}).get("os"):
				template += "\n"+MSG_NODE_TEMPLATE["os"]%data["host"]["os"]
			return template

		def get_template_M(data, template):
			d_template={
				"state":[],
				"color_state":[],
				"os":[],
			}
			for iD in data:
				if iD.get("state"):
					color_state = self.get_node_color_from_state(iD["state"])
					if not color_state in d_template["color_state"]:
						d_template["color_state"].append(color_state)
					if not iD["state"] in d_template["state"]:
						d_template["state"].append(iD["state"])
				if iD.get("host",{}).get("os"):
					if not iD["host"]["os"] in d_template["os"]:
						d_template["os"].append(iD["host"]["os"])
			if d_template["state"]:
				template += "\n" + MSG_NODE_TEMPLATE["state"]%(" ".join([
					"".join(d_template["color_state"]),
					" ".join(d_template["state"]),
				]))
			if d_template["os"]:
				template += "\n" + MSG_NODE_TEMPLATE["os"]%(" ".join(d_template["os"]))
			return template

		keyboard=None
		if isinstance(node_data, dict):
			template = MSG_NODE_TEMPLATE["name_node"]%node_name
			template = get_template_1(node_data, template)
			keyboard = self.KB.nodes_inline({
				"id":message.chat.id,
				"node_name":node_name,
			})
		elif isinstance(node_data, (list, tuple)):
			if len(node_data)==1:
				template = MSG_NODE_TEMPLATE["name_node"]%node_name
				template = get_template_1(node_data[0], template)
				keyboard = self.KB.nodes_inline({
					"id":message.chat.id,
					"node_name":node_name,
				})
			else:
				template = MSG_NODE_TEMPLATE["name_grp"]%node_name
				template = get_template_M(node_data, template)

				keyboard = self.KB.grp_nodes_inline({
					"id":message.chat.id,
					"node_name":node_name,
				})
		else:
			template = MSG_NODE_TEMPLATE["name_node"]%node_name
		self.log_info(template)
		self.send_user(
			message.chat.id,
			template,
			reply_markup=keyboard,
			parse_mode="HTML",
		)
		return


	def msg_check_state(self, job_name, job_data, old_job_data=None, check_time=None, set_time=None, set_state=None, state_only=None):
		self.log_info("msg_check_state")
		try:
			if (state_only and state_only in job_data.get("state")) or not state_only:
				if check_time:
					if set_time:
						template = MSG_TIMESTATE_TEMPLATE
						time_state = set_time
					elif old_job_data and self.is_new(job_data, old_job_data):
						template = MSG_TIMESTATE_TEMPLATE
						time_state = "NEW"
					elif old_job_data and self.is_restart(job_data, old_job_data):
						template = MSG_TIMESTATE_TEMPLATE
						time_state = "RESTART"
					else:
						template = MSG_STATE_TEMPLATE
						time_state=None
				else:
					template = MSG_STATE_TEMPLATE
					time_state=None

				if set_state:
					state = set_state
					af_state = " %s %s"%(state, job_data.get("state"))
				else:
					if self.is_err(job_data, old_job_data):
						state = "ERROR"
					elif self.is_don(job_data, old_job_data):
						state = "DONE"
					elif self.is_run(job_data, old_job_data):
						state = "RUN"
					else:
						return
					af_state = job_data.get("state")

				color_state=self.get_emoji_from_state(af_state)
				af_name = self.get_username(job_data.get("user_name"))
				self.log_info(template)
				if not state in ["DELETE"]:
					self.send_channel(template%locals())

				if state in ["RUN", "DONE", "DELETE"] or time_state in ["NEW"]:
					l_id = self.get_id_user_from_af_name(job_data.get("user_name"))
					if l_id:
						for id in l_id:
							self.send_user(id, template%locals())
				if state == "ERROR":
					l_id = self.get_id_user_from_af_name(job_data.get("user_name"))
					if l_id:
						for id in l_id:
							if id not in self.LIST_ADMIN_ID:
								self.send_user(id, template%locals())
					self.send_admins(template%locals())
		except Exception as e:
			self.send_admins("<b>ERROR \"msg_check_state\":</b>\n%s"%str(traceback.format_exc()))

	def set_webhook(self):
		# Снимаем вебхук перед повторной установкой (избавляет от некоторых проблем)
		self.bot.remove_webhook()
		# Ставим заново вебхук
		self.bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
		                     certificate=open(WEBHOOK_SSL_CERT, 'r'))

	def farm_renders_update(self, data):
		try:
			self.log_info("farm_renders_update")
			self.LAST_RENDERS = {self.get_node_name(i["name"]): i for i in data}
			self.DICT_GRP_RENDERS = {}
			for iNodeName, iNodeData in self.LAST_RENDERS.items():
				n = self.get_group_from_render_node(iNodeName)
				if n not in self.DICT_GRP_RENDERS:
					self.DICT_GRP_RENDERS[n] = []
				self.DICT_GRP_RENDERS[n].append(iNodeName)
		except Exception:
			self.send_admins("<b>ERROR \"farm_renders_update\":</b>\n%s"%str(traceback.format_exc()))

	def farm_status_update(self, data):
		try:
			self.log_info("farm_status_update")
			if data:
				self.log_info("LIST JOBS NAME")
				self.log_info([i["name"] for i in data])
				self.log_info("JOB KEYS")
				self.log_info(data[0].keys())

				d_job_name = {}
				for i in data:
					if (
							all([i.get(j) for j in [
								"name", "user_name", "time_creation",
								"state"
							]])
							and i["user_name"] != "afadmin"
					):
						d_job_name[i["name"]] = {
							"user_name": i["user_name"],
							'time_creation': i['time_creation'],
							'time_started': i.get('time_started'),
							'state': i['state'],
						}
				if  self.LAST_SCREEN is None:
					self.msg_bot_reboot()

				for iNewJob, iNewJobINFO in d_job_name.items():
					if self.LAST_SCREEN and isinstance(self.LAST_SCREEN, dict):
						if iNewJob in self.LAST_SCREEN:
							iOldJobINFO = self.LAST_SCREEN[iNewJob]
							self.msg_check_state(iNewJob, iNewJobINFO, iOldJobINFO, check_time=True)
							del(self.LAST_SCREEN[iNewJob])
						else:
							self.msg_check_state(iNewJob, iNewJobINFO, check_time=True, set_time="NEW")
					else:
						self.msg_check_state(iNewJob, iNewJobINFO, state_only="RUN")
				if self.LAST_SCREEN and isinstance(self.LAST_SCREEN, dict):
					for iOldJob in self.LAST_SCREEN:
						self.msg_check_state(iOldJob, self.LAST_SCREEN[iOldJob], set_state="DELETE")
				if d_job_name:
					self.LAST_SCREEN = dict(d_job_name)
				else:
					self.LAST_SCREEN = False
		except Exception:
			self.send_admins("<b>ERROR \"farm_status_update\":</b>\n%s"%str(traceback.format_exc()))

	def get_msg_set_render_node(self, node_name, data):
		msg = "<b>%s:</b>"%node_name
		if data.get("outs"):
			msg+="\n    %s"%data["outs"]
		if data.get("errs"):
			msg+="\n    <b>Error</b>: %s"%data["errs"]
		return msg

	def set_on_render_node(self, data, force=None):
		self.log_info("set_on_render_node")
		self.log_info(data)
		# \U0001F7E2  green_circle
		# \U0001f7e9  green_square
		if force:
			self.send_admins("\U0001F7E2 Forced running nodes on a farm:\n%s"%"\n".join(
				[ self.get_msg_set_render_node(k,v) for k,v in data.items()]
			))
		else:
			self.send_admins("\U0001F7E2 Running nodes on a farm:\n%s"%"\n".join(data))

	def set_off_render_node(self, data, force=None):
		self.log_info("set_off_render_node")
		self.log_info(data)
		# \U000025FB  white_medium_square
		# \U000026AA  white_circle
		if force:
			self.send_admins("\U000026AA Forced shutting down nodes on the farm:\n%s"%"\n".join(
				[ self.get_msg_set_render_node(k,v) for k,v in data.items()]
			))
		else:
			self.send_admins("\U000026AA Started shutting down nodes on the farm:\n%s"%"\n".join(data))

	def set_restart_render_node(self, data, force=None):
		self.log_info("set_restart_render_node")
		self.log_info(data)
		if force:
			self.send_admins("\U0001F7E2 Forced restart nodes on the farm:\n%s"%"\n".join(
				[ self.get_msg_set_render_node(k,v) for k,v in data.items()]
			))
		else:
			self.send_admins("\U0001F7E2 Restart shutting down nodes on the farm:\n%s"%"\n".join(data))

	def set_err_render_node(self,data):
		self.log_info("set_err_render_node")
		self.log_info(data)
		# \U0001f7e5  red_square
		# \U0001F534  red_circle
		# \U00002757  red_exclamation_mark
		self.send_admins("\U00002757 Nodes not responding or returning an error:\n%s"%"\n".join(data))

	def set_err_server(self):
		self.send_admins("\U00002757\U00002757\U00002757 No signal from server!")

	def start_message(self, message):
		self.log_info("start_message")
		if message.from_user.id in self.LIST_ALLOWED_USER_IDS:
			self.bot.reply_to(
				message,
				"You are already registered",
				reply_markup=self.KB.start_cmds(admin=message.from_user.id in LIST_ADMIN_ID)
			)
		else:
			self.SD.add_user({
				"first_name":message.from_user.first_name,
				"last_name":message.from_user.last_name,
				"username":message.from_user.username,
				"id":int(message.from_user.id),
			})
			keyboard = telebot.types.InlineKeyboardMarkup()
			button = telebot.types.InlineKeyboardButton(
				text="Invite to chat",
				callback_data="invite %s" % json.dumps({
					"id":message.from_user.id,
					"username": message.json["from"].get(
						"username",
						" ".join([
							message.json["from"].get("first_name", ""),
							message.json["from"].get("last_name", ""),
						])
					),
				}

				),
			)
			keyboard.add(button)
			self.send_admins(
				"New user wants to join:\n%s" % json.dumps(message.json["from"], indent=4),
				kb=keyboard
			)
			self.send_user(message.from_user.id, "Message sent to manager")

	def info_message(self, message):
		self.log_info("info_mesaage")
		if message.from_user.id in self.LIST_ALLOWED_USER_IDS:
			if message.from_user.id in self.LIST_ADMIN_ID:
				txt = "\n".join(i for i in INFO["user"]+INFO["admin"])
			else:
				txt = "\n".join(i for i in INFO["user"])
			self.send_user(message.from_user.id, txt)
		else:
			self.send_user(message.from_user.id, "You are not registred")

	def callback_inline(self, call, *args, **kwargs):
		self.log_info("callback_inline")
		# Если сообщение из чата с ботом
		if call.message:
			if call.message.chat.id in LIST_ADMIN_ID:
				if call.data.startswith("invite "):
					self.callback_inline_invite(call)
				elif call.data.startswith("delete_user "):
					self.callback_inline_delete_user(call)
				elif call.data.startswith("set_admin "):
					self.callback_inline_set_admin(call)
				elif call.data.startswith("show_each_node "):
					self.callback_inline_show_each_node(call)
				elif call.data.startswith("off_unmng_each_node "):
					self.callback_inline_off_unmng_each_node(call)
				elif call.data.startswith("mng_each_node "):
					self.callback_inline_mng_each_node(call)
				elif call.data.startswith("set_up_node "):
					self.callback_inline_set_up_node(call)

	def callback_inline_invite(self, call):
		try:
			self.log_info("callback_inline_invite")
			self.send_admins("New user added:\n%s"%call.data)
			id = int(json.loads(call.data.split("invite ")[1]).get("id", 0))
			self.send_user(id, "You have been added to the list of allowed users")
			if id and not id in self.LIST_ALLOWED_USER_IDS:
				self.LIST_ALLOWED_USER_IDS.append(id)
				self.SD.save_allowed_user_ids(self.LIST_ALLOWED_USER_IDS)
				self.log_info(self.SD.get_allowed_user_ids())
		except Exception:
			self.send_admins("ERROR \"callback_inline_invite\":\n%s"%str(traceback.format_exc()))

	def callback_inline_delete_user(self,call):
		try:
			self.log_info("delete_user")
			info = json.loads(call.data.split("delete_user ")[1])
			delete_id = int(info.get("id_delete", 0))
			if delete_id in self.LIST_ALLOWED_USER_IDS:
				self.send_user(
					call.message.chat.id,
					"Are you sure you want to delete this user?\n%s"%json.dumps(self.SD.get_user(delete_id), indent=4),
					reply_markup=self.KB.confirm()
				)
				self.bot.register_next_step_handler(call.message, self.delete_user, **{"delete_id":delete_id})
			else:
				self.send_user(call.message.chat.id, "User not found", reply_markup=self.KB.start_cmds(admin=id in LIST_ADMIN_ID))
		except Exception:
			self.send_admins("ERROR \"callback_inline_delete_user\":\n%s"%str(traceback.format_exc()))

	def callback_inline_set_admin(self,call):
		try:
			self.log_info("set_admin")
			info = json.loads(call.data.split("set_admin ")[1])
			# id = int(info.get("id", 0))
			# log_info(id)
			id_new_admin = int(info.get("id_new_admin", 0))
			if id_new_admin in self.LIST_ALLOWED_USER_IDS:
				self.send_user(
					call.message.chat.id,
					"Are you sure you want to make the user an administrator?\n%s"%json.dumps(self.SD.get_user(id_new_admin), indent=4),
					reply_markup=self.KB.confirm()
				)
				self.bot.register_next_step_handler(call.message, self.add_admin, **{"id_new_admin":id_new_admin})
			else:
				self.send_user(
					call.message.chat.id,
					"User not found",
					reply_markup=self.KB.start_cmds(admin=call.message.chat.id in LIST_ADMIN_ID))
		except Exception:
			self.send_admins("ERROR \"callback_inline:set_admin\":\n%s"%str(traceback.format_exc()))

	def callback_inline_show_each_node(self,call):
		try:
			self.log_info("show_each_node")
			info = json.loads(call.data.split("show_each_node ")[1])
			self.send_user(call.message.chat.id, "Information about nodes from the \"%s.*\" group"%info["node_name"])
			for iName in sorted(self.LAST_RENDERS):
				if iName.startswith(info["node_name"]):
					self.print_node_info(call.message, iName, self.LAST_RENDERS[iName])
		except Exception:
			self.send_admins("ERROR \"callback_inline:show_each_node\":\n%s"%str(traceback.format_exc()))

	def callback_inline_off_unmng_each_node(self,call):
		try:
			self.log_info("off_unmng_each_node")
			info = json.loads(call.data.split("off_unmng_each_node ")[1])
			self.send_user(call.message.chat.id, "Node group disabled and placed in unmanaged mode: \"%s.*\""%info["node_name"])
			for iNode in [iName for iName in self.LAST_RENDERS if iName.startswith(info["node_name"])]:
				if iNode not in self.LIST_NODE_SET_OFF:
					self.LIST_NODE_SET_OFF.append(iNode)
				if iNode in self.MANAGED_NODES:
					self.MANAGED_NODES.pop(self.MANAGED_NODES.index(iNode))
		except Exception:
			self.send_admins("ERROR \"callback_inline:off_unmng_each_node\":\n%s"%str(traceback.format_exc()))

	def callback_inline_mng_each_node(self,call):
		try:
			self.log_info("mng_each_node")
			info = json.loads(call.data.split("mng_each_node ")[1])
			self.send_user(call.message.chat.id, "Node group moved to managed mode: \"%s.*\""%info["node_name"])
			for iNode in [iName for iName in self.LAST_RENDERS if iName.startswith(info["node_name"])]:
				if iNode not in self.MANAGED_NODES:
					self.MANAGED_NODES.append(iNode)
		except Exception:
			self.send_admins("ERROR \"callback_inline:mng_each_node\":\n%s"%str(traceback.format_exc()))

	def callback_inline_set_up_node(self, call):
		try:
			self.log_info("set_up_node")
			info = json.loads(call.data.split("set_up_node ")[1])
			self.send_user(
				call.message.chat.id,
				"Choose the next command",
				reply_markup=self.KB.set_up_node(
					admin=call.message.chat.id in self.LIST_ADMIN_ID,
					managed= True if info.get("node_name") in self.MANAGED_NODES else False,
					always_on= True if info.get("node_name") in self.ON_NODES else False,
					prohibited=True if info.get("node_name") in self.PROHIBITED_NODES else False,
				)
			)
			self.bot.register_next_step_handler(
				call.message,
				self.set_up_node,
				**{"node_name":info.get("node_name")}
			)
		except Exception:
			self.send_admins("ERROR \"callback_inline:set_up_node\":\n%s"%str(traceback.format_exc()))

	def save_render_user_name(self, message):
		self.log_info("save_render_user_name")
		if message.from_user.id in self.LIST_ALLOWED_USER_IDS:
			user_data = self.SD.get_user(message.from_user.id)
			user_data.update({"render_user_name": message.text})
			self.SD.add_user(user_data)
			self.bot.reply_to(
				message,
				"New name is save",
				reply_markup=self.KB.start_cmds(admin=message.from_user.id in self.LIST_ADMIN_ID)
			)


	def get_func_from_button(self, text, message):
		self.log_info(text)
		try:
			if message.from_user.id in self.LIST_ALLOWED_USER_IDS:
				if text.capitalize() in self.DICT_BUTTONS:
					func = text.lower().replace(" ", "_").replace("-", "_")
					self.log_info("Func:\n%s"%func)
					if func in dir(self):
						if self.DICT_BUTTONS[text] == "user":
							getattr(self, func)(message)
						elif self.DICT_BUTTONS[text] == "admin" and  message.chat.id in self.LIST_ADMIN_ID:
							getattr(self, func)(message)
					else:
						self.send_user(message.chat.id, "Function not found to process command")
				else:
					self.send_user(message.chat.id, "Command not recognized, please try again")
			else:
				self.send_user(message.chat.id, "You are not registered")
		except Exception:
			txt = "\"get_func_from_button\":\n%s"%str(traceback.format_exc())
			self.send_admins("ERROR %s"%txt)
			self.log_error(txt)

	def set_render_user_name(self, message):
		try:
			self.send_user(message.from_user.id, "Enter the account name on the render farm")
			self.bot.register_next_step_handler(message, self.save_render_user_name)
		except Exception:
			self.send_admins("ERROR Button \"Jobs\":\n%s"%str(traceback.format_exc()))
			self.send_user(
				message.chat.id,
				"An error has occurred. The message has been sent to the administrator.",
				reply_markup=self.KB.start_cmds(admin=message.chat.id in self.LIST_ADMIN_ID))

	def jobs(self, message):
		try:
			self.log_info("jobs")
			user_data = self.SD.get_user(message.from_user.id)
			if user_data.get("render_user_name"):
				if self.LAST_SCREEN:
					ch=None
					for iJobName, iJobInfo in self.LAST_SCREEN.items():
						self.log_info(iJobName)
						self.log_info(iJobInfo.get("user_name"))
						self.log_info(iJobInfo.get("state"))
						if user_data.get("render_user_name") == iJobInfo.get("user_name"):
							self.send_user(
								message.from_user.id,
								"<b>%sJob:</b> %s\n<b>State:</b> %s"%(
									self.get_emoji_from_state(iJobInfo.get("state")),
									iJobName,
									iJobInfo.get("state"),
								),
								parse_mode="HTML",
							)
							ch=True
					if ch is None:
						self.send_user(message.from_user.id, 'Jobs for user \"%s\" not found'%user_data.get("render_user_name"))
				else:
					self.send_user(message.from_user.id, 'An update is currently in progress')
			else:
				self.send_user(message.from_user.id, "\"Render User Name\" not set")
		except Exception as e:
			self.send_admins("ERROR Button \"Jobs\":\n%s"%str(traceback.format_exc()))
			self.send_user(
				message.chat.id,
				"An error has occurred. The message has been sent to the administrator.",
				reply_markup=self.KB.start_cmds(admin=message.chat.id in self.LIST_ADMIN_ID))

	def users(self, message):
		try:
			self.log_info(self.LIST_ALLOWED_USER_IDS)
			for iUserId in self.LIST_ALLOWED_USER_IDS:
				user_data = self.SD.get_user(iUserId)
				if user_data and isinstance(user_data, dict):
					if user_data.get("username"):
						user_name=user_data.get("username")
					else:
						user_name=" ".join([
							user_data.get("first_name") if user_data.get("first_name") else "",
							user_data.get("last_name") if user_data.get("last_name") else "",
						])
					keyboard = telebot.types.InlineKeyboardMarkup()
					if not user_data.get("id") in self.LIST_ADMIN_ID:
						button = telebot.types.InlineKeyboardButton(
							text="Set admin \"%s\""%user_name,
							callback_data="set_admin %s" % json.dumps({
								"id_new_admin":user_data.get("id"),
								"id":message.from_user.id,
							}),
						)
						keyboard.add(button)
					button = telebot.types.InlineKeyboardButton(
						text="Delete user \"%s\""%user_name,
						callback_data="delete_user %s" % json.dumps({
							"id_delete":user_data.get("id"),
							#"username": user_name,
							"id":message.from_user.id,
						}),
					)
					keyboard.add(button)
					self.send_user(
						message.from_user.id,
						json.dumps(user_data, indent=4),
						reply_markup=keyboard,
					)
		except Exception:
			self.send_admins("ERROR Button \"User\":\n%s"%str(traceback.format_exc()))
			self.send_user(
				message.chat.id,
				"An error has occurred. The message has been sent to the administrator.",
				reply_markup=self.KB.start_cmds(admin=True))

	def jobs_run(self, message):
		self.log_info("Jobs run")
		self.get_state_jobs(message, "RUN")

	def jobs_err(self, message):
		self.log_info("Jobs err")
		self.get_state_jobs(message, "ERR")

	def renders(self, message):
		self.log_info("Renders")
		self.send_user(
			message.from_user.id,
			"Choose the next command",
			reply_markup=self.KB.renders_cmds(admin=True),
		)

	def to_main(self, message):
		self.send_user(
			message.from_user.id,
			"Choose the next command",
			reply_markup=self.KB.start_cmds(admin=message.from_user.id in self.LIST_ADMIN_ID))

	def list_of_nodes_by_group(self, message):
		if self.LAST_RENDERS:
			list_grp = sorted([ k for k,v in self.DICT_GRP_RENDERS.items() if len(v)>1])
			list_node = sorted(list(set(self.DICT_GRP_RENDERS).difference(set(list_grp))))
			if list_grp:
				self.send_user(
					message.from_user.id,
					"List of node groups",
				)
				for iGrp in sorted(list_grp):
					self.print_node_info(message, iGrp, [iV for iName, iV in self.LAST_RENDERS.items() if iName.startswith(iGrp)])
			if list_node:
				self.send_user(
					message.from_user.id,
					"List of individual nodes",
				)
				for iNode in sorted(list_node):
					self.print_node_info(message, iNode, [iV for iName, iV in self.LAST_RENDERS.items() if iName.startswith(iNode)])

		else:
			self.send_user(
				message.from_user.id,
				"No information to display",
			)

	def list_of_unmanaged_nodes(self, message):
		try:
			self.log_info("list_of_unmanaged_nodes")
			if self.MANAGED_NODES:
				self.send_user(message.from_user.id, "List of unmanaged nodes")
				for iName in sorted(list(self.LAST_RENDERS.keys())):
					if iName not in self.MANAGED_NODES:
						self.print_node_info(message, iName, self.LAST_RENDERS[iName])
			else:
				self.send_user(message.from_user.id, "Nothing found")
		except:
			txt = "Button \"list_of_unmanaged_nodes\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def list_of_managed_nodes(self, message):
		try:
			self.log_info("list_of_managed_nodes")
			if self.MANAGED_NODES:
				self.send_user(message.from_user.id, "List of managed nodes")
				for iNode in sorted(self.MANAGED_NODES):
					self.print_node_info(message, iNode, [iV for iName, iV in self.LAST_RENDERS.items() if iName == iNode])
			else:
				self.send_user(message.from_user.id, "Nothing found")
		except:
			txt = "Button \"list_of_managed_nodes\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def list_of_broken_nodes(self, message):
		try:
			self.log_info("list_of_broken_nodes")
			if self.BROKEN_NODES:
				self.send_user(message.from_user.id, "List of broken nodes")
				for iNode in sorted(self.BROKEN_NODES):
					self.print_node_info(message, iNode, [iV for iName, iV in self.LAST_RENDERS.items() if iName == iNode])
			else:
				self.send_user(message.from_user.id, "Nothing found")
		except:
			txt = "Button \"list_of_broken_nodes\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def list_of_always_on_nodes(self, message):
		try:
			self.log_info("list_of_always_on_nodes")
			if self.ON_NODES:
				self.send_user(message.from_user.id, "List of always-on nodes")
				for iNode in sorted(self.ON_NODES):
					self.print_node_info(message, iNode, [iV for iName, iV in self.LAST_RENDERS.items() if iName == iNode])
			else:
				self.send_user(message.from_user.id, "Nothing found")
		except:
			txt = "Button \"list_of_always_on_nodes\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def list_of_nodes_prohibited_for_use(self, message):
		try:
			self.log_info("list_of_nodes_prohibited_for_use")
			if self.PROHIBITED_NODES:
				self.send_user(message.from_user.id, "List of nodes prohibited for use")
				for iNode in sorted(self.PROHIBITED_NODES):
					self.print_node_info(message, iNode, [iV for iName, iV in self.LAST_RENDERS.items() if iName == iNode])
			else:
				self.send_user(message.from_user.id, "Nothing found")
		except:
			txt = "Button \"list_ofnodes_prohibited_for_use\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def set_up_node(self, message, *args, **kwargs):
		try:
			self.log_info("set_up_node")
			self.log_info(message)
			self.log_info(args)
			self.log_info(kwargs)
			node_name = kwargs.get("node_name")
			if message.text.startswith("Managed "):
				if node_name in self.MANAGED_NODES:
					del(self.MANAGED_NODES[self.MANAGED_NODES.index(node_name)])
				else:
					self.MANAGED_NODES.append(node_name)
				self.log_info("MANAGED_NODES")
				self.log_info(self.MANAGED_NODES)
			elif message.text.startswith("Always-on "):
				if node_name in self.ON_NODES:
					del(self.ON_NODES[self.ON_NODES.index(node_name)])
				else:
					self.ON_NODES.append(node_name)
				self.log_info("ON_NODES")
				self.log_info(self.ON_NODES)
			elif message.text.startswith("Prohibited "):
				if node_name in self.PROHIBITED_NODES:
					del(self.PROHIBITED_NODES[self.PROHIBITED_NODES.index(node_name)])
				else:
					self.PROHIBITED_NODES.append(node_name)
				self.log_info("PROHIBITED_NODES")
				self.log_info(self.PROHIBITED_NODES)
			elif message.text == ("On"):
				self.LIST_NODE_SET_ON.append(node_name)
			elif message.text == ("Off"):
				self.LIST_NODE_SET_OFF.append(node_name)
			elif message.text == ("Restart"):
				self.LIST_NODE_SET_RESTART.append(node_name)
			else:
				self.send_user(
					message.from_user.id,
					"Choose the next command",
					reply_markup=self.KB.start_cmds(admin=message.from_user.id in self.LIST_ADMIN_ID)
				)
				return

			self.send_user(
				message.from_user.id,
				"Choose the next command",

				reply_markup=self.KB.set_up_node(
					admin=message.chat.id in self.LIST_ADMIN_ID,
					managed= True if node_name in self.MANAGED_NODES else False,
					always_on= True if node_name in self.ON_NODES else False,
					prohibited=True if node_name in self.PROHIBITED_NODES else False,
				)
			)
		except:
			txt = "Button \"set_up_node\":\n%s"%str(traceback.format_exc())
			self.log_error(txt)
			self.send_admins("ERROR %s"%txt)

	def get_state_jobs(self, message, state):
		try:
			if self.LAST_SCREEN:
				ch=None
				for iJobName, iJobInfo in self.LAST_SCREEN.items():
					if state in iJobInfo.get("state"):
						d_user = self.SD.DICT_AF_USER.get(iJobInfo.get("user_name"))
						if d_user:
							l_user = str([ i for i in d_user.values() ])
						else:
							l_user = "None"
						emj= self.get_emoji_from_state(iJobInfo.get("state"))
						self.send_user(
							message.from_user.id,
							"<b>%sJob:</b> %s\n<b>User name:</b> %s == %s\n<b>State:</b> %s"%(
								emj,
								iJobName,
								iJobInfo.get("user_name"),
								l_user,
								iJobInfo.get("state"),
							),
							parse_mode="HTML",
							)
						ch=True
				if ch is None:
					self.send_user(message.from_user.id, 'No jobs found with %s status'%state)
			else:
				self.send_user(message.from_user.id, 'An update is currently in progress')
		except Exception as e:
			self.send_admins("ERROR Button \"Jobs %s\":\n%s"%(state,str(traceback.format_exc())))
			self.send_user(
				message.chat.id,
				"An error has occurred. The message has been sent to the administrator.",
				reply_markup=self.KB.start_cmds(admin=message.chat.id in self.LIST_ADMIN_ID))
