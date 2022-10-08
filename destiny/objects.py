from destiny.header import *
from destiny.exceptions import *
import destiny.structs as structs
import destiny.events as events

import json
import jsons
import uuid

class User( events.recv_event ):
    _lookup = {
            "id" : "id",
            "username" : "username",
            "discriminator" : "discriminator",
            "avatar" : "avatar",
            "bot" : "is_bot",
            "system" : "is_system",
            "mfa_enabled" : "is_mfa_enabled",
            "banner" : "banner",
            "accent_color" :"accent_color",
            "locale" : "locale",
            "verified" : "is_verified",
            "email" : "email",
            "flags": "flags",
            "premium_type" : "premium_type",
            "public_flags" : "public_flags",


            "avatar_decoration" : "avatar_decoration"
            }

class Message( events.recv_event ):
    _lookup = {
            "id" : "id", #string
            "channel_id": "channel_id", #string
            "author": "author", #object _author_
            "content" : "content", #string
            "timestamp" : "time",
            "edited_timestamp" : "edited_time",
            "tts" : "tts", #bool
            "mention_everyone" : "mention_everyone",
            "mentions" : "mentions",
            "mention_roles" :"mention_roles",
            "mention_channels" : "mention_channels",
            "attachments" : "attachments", #list object
            "embeds" : "embeds",
            "reactions" : "reactions",
            "nonce" : "nonce",
            "pinned" : "pinned",
            "webhook_id" : "webhook_id",
            "type" : "type",
            "activity" : "activity",
            "application": "app",
            "application_id" : "app_id",
            "message_reference" : "message_reference",
            "flags" : "flags",
            "referenced_message": "referenced_message",
            "interaction" : "interaction",
            "thread" : "thread",
            "components" : "components",
            "sticker_items" : "sticker_items",
            "stickers" : "stickers",
            "position" : "position",


            "guild_id" : "guild_id",
            "member" : "member",
            }

class Channel( structs.unimplimented_structure ):
    def __str__( self ):
        return self.name
    def __repr__( self ):
        return self.name

class Guild( structs.unimplimented_structure ):
    def __str__( self ):
        return self.name
    def __repr__( self ):
        return self.name

