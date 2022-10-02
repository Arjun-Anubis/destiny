import destiny
import destiny.homeworkbot as homeworkbot
import destiny.default_handlers as default_handlers
import destiny.runners

client = homeworkbot.Client(default_handlers.message_handler)
destiny.runners.auto_reload(client)
