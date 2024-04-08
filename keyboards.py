#coding=utf-8
from cherrypy import log
from telebot import types
import json

START={
	"user":["Set render user name", "Jobs"],
	"admin":["Users", "Jobs run", "Jobs err", "Renders",],
}

USERS={
	"admin":[
		"list users",
		"add user",
	]
}

CONFIRM={
	"user":["Confirm","Reject"]
}

RENDERS={
	"admin":[
		"List of nodes by group",
		"List of unmanaged nodes",
		"List of managed nodes",
		"List of broken nodes",
		"List of always-on nodes",
		"List of nodes prohibited for use",
	],
	# "user":["To main",],
}

NODES={
	"admin":[
		"To main",
		"Managed",
		"Always-on",
		"Prohibited",
		["On", "Off", "Restart"],

	]
}

DICT_BUTTONS={}
for iDictButton in [START, CONFIRM, RENDERS, NODES]:
	for iType, iListButton in iDictButton.items():
		for iButton in iListButton:
			if isinstance(iButton, str):
				DICT_BUTTONS[iButton]=iType
			elif isinstance(iButton, (list,tuple)):
				for iiButton in iButton:
					DICT_BUTTONS[iiButton]=iType



class KeyBoarder():

	def __init__(self):
		pass

	def log_info(self, msg):
		log(str(msg), "KEYBOARD INFO")

	def log_err(self, msg):
		log(str(msg), "KEYBOARD ERROR")


	def get_buttons(self, dict_buttons , manager=None, admin=None):
		l_buttons=[]
		l_buttons.extend(dict_buttons.get("user", []))
		if manager:
			l_buttons.extend(dict_buttons.get("manager", []))
		if admin:
			l_buttons.extend(dict_buttons.get("admin", []))
		return l_buttons

	def start_cmds(self, manager=None, admin=None):
		markup = types.ReplyKeyboardMarkup(
			one_time_keyboard=True,
			resize_keyboard=True,
		)
		l_buttons=self.get_buttons(START, manager, admin)
		colum_count = 3
		for i in range(0, len(l_buttons), colum_count):
			row=[]
			for j in range(0,colum_count,1):
				if i+j < len(l_buttons):
					row.append(types.KeyboardButton(l_buttons[i+j]))
			markup.row(*row)
		return markup

	def confirm(self):
		markup = types.ReplyKeyboardMarkup(
			one_time_keyboard=True,
			resize_keyboard=True,
		)
		l_buttons=self.get_buttons(CONFIRM)
		colum_count = 2
		for i in range(0, len(l_buttons), colum_count):
			row=[]
			for j in range(0,colum_count,1):
				if i+j < len(l_buttons):
					row.append(types.KeyboardButton(l_buttons[i+j]))
			markup.row(*row)
		return markup

	def renders_cmds(self, manager=None, admin=None):
		markup = types.ReplyKeyboardMarkup(
			one_time_keyboard=True,
			resize_keyboard=True,
		)
		l_buttons=self.get_buttons(RENDERS, manager, admin)
		for iB in l_buttons:
			markup.row(types.KeyboardButton(iB))
		# colum_count = 1
		# for i in range(0, len(l_buttons), colum_count):
		# 	row=[]
		# 	for j in range(0,colum_count,1):
		# 		if i+j < len(l_buttons):
		# 			row.append(types.KeyboardButton(l_buttons[i+j]))
		# 	markup.row(*row)
		return markup

	def set_up_node(self, manager=None, admin=None, managed=None,always_on=None,prohibited=None):
		markup = types.ReplyKeyboardMarkup(
			one_time_keyboard=True,
			resize_keyboard=True,
		)
		l_buttons=self.get_buttons(NODES, manager, admin)
		icon={
			True:"\U00002611 ON",
			False:"\U00002610 OFF",
		}
		d_icon={
			"Managed":managed,
			"Always-on":always_on,
			"Prohibited":prohibited,
		}
		colum_count = 2
		row=[]
		for iB in l_buttons:
			if isinstance(iB, str):
				row.append(types.KeyboardButton("%s %s"%(iB, icon.get(d_icon.get(iB), "") )))
				# markup.row()
				if len(row) >= colum_count:
					markup.row(*row)
					row=[]
			elif isinstance(iB, list):
				if row:
					markup.row(*row)
					row=[]
				if managed:
					self.log_info(["%s %s"%(jB, icon.get(d_icon.get(jB), "") ) for jB in iB])
					markup.row(*[
						types.KeyboardButton("%s %s"%(jB, icon.get(d_icon.get(jB), "") )) for jB in iB
					])

		return markup

	def grp_nodes_inline(self, callback_data):
		keyboard = types.InlineKeyboardMarkup()

		button = types.InlineKeyboardButton(
			text="Show for each node",
			callback_data="show_each_node %s" % json.dumps(callback_data))
		keyboard.add(button)

		button = types.InlineKeyboardButton(
			text="Off & Unmanaged for each node",
			callback_data="off_unmng_each_node %s" % json.dumps(callback_data))
		keyboard.add(button)

		button = types.InlineKeyboardButton(
			text="Managed for each node",
			callback_data="mng_each_node %s" % json.dumps(callback_data))
		keyboard.add(button)

		return  keyboard

	def nodes_inline(self, callback_data):
		self.log_info(callback_data)
		keyboard = types.InlineKeyboardMarkup()
		button = types.InlineKeyboardButton(
			text="Set up node \"%s\""%callback_data["node_name"],
			callback_data="set_up_node %s" % json.dumps(callback_data))
		keyboard.add(button)
		return  keyboard
		# if dict_callback_data:
		# 	keyboard = types.InlineKeyboardMarkup()
		# 	for iText in sorted(list(dict_callback_data.keys())):
		# 		button = types.InlineKeyboardButton(
		# 			text=iText,
		# 			callback_data=dict_callback_data[iText],
		# 		)
		# 		keyboard.add(button)
		# 	return  keyboard
		# else:
		# 	return None