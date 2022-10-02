import destiny
import destiny.core as core
import destiny.default_handlers as default_handlers
import destiny.message_handler as message_handler
import destiny.runners

client = core.Client( message_handler.message_handler )
destiny.runners.auto_reload(client)
