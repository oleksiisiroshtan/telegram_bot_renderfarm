#coding=utf-8
token="0000000000:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"

# WEBHOOK_HOST = 'IP-адрес сервера, на котором запущен бот'
WEBHOOK_HOST = '123.456.789.123'
# WEBHOOK_PORT = 443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
# WEBHOOK_PORT = 80  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_PORT = 8443  # 443, 80, 88 или 8443 (порт должен быть открыт!)
WEBHOOK_LISTEN = '0.0.0.0'  # На некоторых серверах придется указывать такой же IP, что и выше

# WEBHOOK_SSL_CERT = './webhook_cert.pem'  # Путь к сертификату
# WEBHOOK_SSL_PRIV = './webhook_pkey.pem'  # Путь к приватному ключу
WEBHOOK_SSL_CERT = '/home/siroshtan/webhook_cert.pem'  # Путь к сертификату
WEBHOOK_SSL_PRIV = '/home/siroshtan/webhook_pkey.pem'  # Путь к приватному ключу

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (token)

LOGGER_FOLDER = "/var/log/farm_bot_log"


LIST_ADMIN_ID=[
	123456789
]

CHANNAL_ID = -1234567891011

DICT_AF_USER={}


MSG_REBOOT_TEMPLATE="BOT RESTARTED"
# MSG_NEW_TEMPLATE="JOB NEW:\nuser: %s\njob: %s"
# MSG_RST_TEMPLATE="JOB RESTART:\nuser: %s\njob: %s"
MSG_TIMESTATE_TEMPLATE="<b>%(color_state)sJOB %(time_state)s %(state)s:</b>\n<b>User:</b> %(af_name)s\n<b>Job:</b> %(job_name)s\n<b>State:</b> %(af_state)s"
# MSG_STATE_TEMPLATE="JOB %(state)s:\nUser: %(af_name)s\nJob: %(job_name)s\nState: %(af_state)s"
MSG_STATE_TEMPLATE="<b>%(color_state)sJOB %(state)s:</b>\n<b>User:</b> %(af_name)s\n<b>Job:</b> %(job_name)s\n<b>State:</b> %(af_state)s"
MSG_NODE_TEMPLATE={
	"name_grp":"<b>Name</b>: %s.*",
	"name_node":"<b>Name</b>: %s",
	"ip":"<b>IP</b>: %s",
	"state":"<b>State</b>: %s",
	"os":"<b>OS</b>: %s",
}

INFO = {
	"user":[
		"""<b>/start</b> - Shows the basic set of commands for the user, depending on his rights""",
		"""<b>/info</b> - Description of all available commands for the user, depending on his rights""",
		"List of commands:",
		"<b>Set render user name</b> - Specify the name of your account on the render farm",
		"<b>Jobs</b> - List of farm jobs running under your account"
	],
	"admin":[
		"<b>Users</b> - List of registered users",
		"<b>Jobs run</b> - List of current farm jobs (with RUN status)",
		"<b>Jobs err</b> - List of failed farm jobs (with status ERR)",
		"<b>Renders</b> - List of commands for working with nodes",

		"<b>List of nodes by group</b> - List of nodes registered on the farm, their parameters and current state",
		"<b>List of unmanaged nodes</b> - List of unmanaged nodes. These nodes cannot be started/suspended remotely",
		"<b>List of managed nodes</b> - List of managed nodes. These nodes can be started/stopped remotely",
		"<b>List of broken nodes</b> - List of nodes that encountered an error or are not responding to commands",
		"<b>List of always-on nodes</b> - List of nodes active all the time",
		"<b>List of nodes prohibited for use</b> - List of nodes prohibited for use",
	]

}

