#coding=utf-8
import os
import shelve
import json
from cherrypy import log

class SaveData():

	DICT_AF_USER={}

	def __init__(self, script_folder):

		self.ALLOWED_USER_IDS_FILE_PATH = os.path.normpath( os.path.join(script_folder, "BD", "allowed_user_ids.list"))
		self.ADMIN_FILE_PATH = os.path.normpath( os.path.join(script_folder, "BD", "admin.list"))
		# self.MANAGER_FILE_PATH = os.path.normpath( os.path.join(script_folder, "BD", "manager"))

		# self.PROJECT_FOLDER = os.path.normpath( os.path.join(script_folder, "BD", "projects"))
		self.USER_FOLDER = os.path.normpath( os.path.join(script_folder, "BD", "users"))

		#Создание списка имен пользователй на ферме
		list_ids = list(set(self.get_allowed_user_ids()+self.get_admins()))
		for iID in list_ids:
			self.get_user(iID)

	def log_info(self, msg):
		log(str(msg), "SHELVE INFO")

	def log_error(self, msg):
		log(str(msg), "SHELVE ERROR")


	# def save_users(self, d_data):
	# 	if not os.path.isdir(self.USER_FOLDER):
	# 		os.makedirs(self.USER_FOLDER)
	# 	if d_data:
	# 		for iUser_id, iData in d_data.items():
	# 			with shelve.open(os.path.join(self.USER_FOLDER, str(iUser_id)), "n") as states:
	# 				for k,v in iData.items():
	# 					states[k]=v

	def get_nice_name(self, user_data):
		if user_data.get("username"):
			user_name="@"+user_data.get("username")
		else:
			user_name=" ".join([ user_data.get(i) for i in ["first_name", "last_name" ] if user_data.get(i)] )
			# 	user_data.get("first_name") if user_data.get("first_name") else "",
			# 	user_data.get("last_name") if user_data.get("last_name") else "",
			# ])
		return user_name

	def add_user(self, user_data):
		if not os.path.isdir(self.USER_FOLDER):
			os.makedirs(self.USER_FOLDER)
		if user_data:
			with shelve.open(os.path.join(self.USER_FOLDER, str(user_data["id"])), "n") as states:
				for k, v in user_data.items():
					states[k] = v
					if k=="render_user_name":
						# if not v in self.DICT_AF_USER:
						# 	self.DICT_AF_USER[v]={}
						# self.DICT_AF_USER[v].update({
						# 	user_data["id"]:self.get_nice_name(user_data)
						# })
						self.DICT_AF_USER[v]={
							user_data["id"]:self.get_nice_name(user_data)
						}

	def get_user(self, id):
		self.log_info("get_user")
		with shelve.open(os.path.join(self.USER_FOLDER, str(id)), "r") as states:
			# for k, v in user_data.items():
			# 	states[k] = v
			user_data= dict(states)
			self.log_info(str(user_data))
			if user_data.get("render_user_name"):
				if  not user_data.get("render_user_name") in self.DICT_AF_USER:
					self.DICT_AF_USER[user_data.get("render_user_name")]={}
				self.DICT_AF_USER[user_data.get("render_user_name")].update({user_data["id"]:self.get_nice_name(user_data)})
			return user_data


	def save_allowed_user_ids(self, l_ids):
		if not os.path.isdir( os.path.split(self.ALLOWED_USER_IDS_FILE_PATH)[0]):
			os.makedirs(os.path.split(self.ALLOWED_USER_IDS_FILE_PATH)[0])
		with open(self.ALLOWED_USER_IDS_FILE_PATH, "w") as f:
			f.write(json.dumps(list(set(l_ids))))


	def get_allowed_user_ids(self):
		if os.path.isfile( self.ALLOWED_USER_IDS_FILE_PATH):
			with open(self.ALLOWED_USER_IDS_FILE_PATH, "r") as f:
				return json.loads(f.read())
		return []



	def save_admin_ids(self, l_ids):
		l = list(set(l_ids))
		if not os.path.isdir( os.path.split(self.ADMIN_FILE_PATH)[0]):
			os.makedirs(os.path.split(self.ADMIN_FILE_PATH)[0])
		with open(self.ADMIN_FILE_PATH, "w") as f:
			f.write(json.dumps(l))
		return l

	def get_admins(self):
		if os.path.isfile(self.ADMIN_FILE_PATH):
			with open(self.ADMIN_FILE_PATH, "r") as f:
				# return [int(i) for i in f.readlines() if i]
				return json.loads(f.read())
		return []



	# def get_managers(self):
	# 	if os.path.isfile(self.MANAGER_FILE_PATH):
	# 		with open(self.MANAGER_FILE_PATH, "r") as f:
	# 			return [int(i) for i in f.readlines() if i]
	# 	return []
	#
	#
	# def set_manager(self, id):
	# 	if os.path.isfile(self.MANAGER_FILE_PATH):
	# 		with open(self.MANAGER_FILE_PATH, "a") as f:
	# 			f.write(str(id))
	# 	else:
	# 		with open(self.MANAGER_FILE_PATH, "x") as f:
	# 			f.write(str(id))
	# 	return