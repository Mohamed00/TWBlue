# -*- coding: utf-8 -*-
import wx
import logging
import mastodon
import output
from mastodon import MastodonError
from pubsub import pub
from mysc import restart
from mysc.thread_utils import call_threaded
from wxUI.dialogs.mastodon import search as search_dialogs
from wxUI.dialogs.mastodon import dialogs
from wxUI.dialogs import userAliasDialogs
from wxUI import commonMessageDialogs
from wxUI.dialogs.mastodon import updateProfile as update_profile_dialogs
from wxUI.dialogs.mastodon import showUserProfile, communityTimeline
from sessions.mastodon.utils import html_filter
from . import userActions, settings

log = logging.getLogger("controller.mastodon.handler")

class Handler(object):

    def __init__(self):
        super(Handler, self).__init__()
        # Structure to hold names for menu bar items.
        # empty names mean the item will be Disabled.
        self.menus = dict(
            # In application menu.
            updateProfile=_("Update Profile"),
            menuitem_search=_("&Search"),
            lists=None,
            manageAliases=_("Manage user aliases"),
            # In item menu.
            compose=_("&Post"),
            reply=_("Re&ply"),
            share=_("&Boost"),
            fav=_("&Add to favorites"),
            unfav=_("Remove from favorites"),
            view=_("&Show post"),
            view_conversation=_("View conversa&tion"),
            ocr=_("Read text in picture"),
            delete=_("&Delete"),
            # In user menu.
            follow=_("&Actions..."),
            timeline=_("&View timeline..."),
            dm=_("Direct me&ssage"),
            addAlias=_("Add a&lias"),
            addToList=None,
            removeFromList=None,
            details=_("Show user profile"),
            favs=None,
            # In buffer Menu.
            community_timeline =_("Create community timeline"),
            filter=None,
            manage_filters=None
        )
        # Name for the "tweet" menu in the menu bar.
        self.item_menu = _("&Post")

    def create_buffers(self, session, createAccounts=True, controller=None):
        session.get_user_info()
        name = session.get_name()
        controller.accounts.append(name)
        if createAccounts == True:
            pub.sendMessage("core.create_account", name=name, session_id=session.session_id, logged=True)
        root_position =controller.view.search(name, name)
        for i in session.settings['general']['buffer_order']:
            if i == 'home':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Home"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="timeline_home", name="home_timeline", sessionObject=session, account=name, sound="tweet_received.ogg"))
            elif i == 'local':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Local"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="timeline_local", name="local_timeline", sessionObject=session, account=name, sound="tweet_received.ogg"))
            elif i == 'federated':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Federated"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="timeline_public", name="federated_timeline", sessionObject=session, account=name, sound="tweet_received.ogg"))
            elif i == 'mentions':
                pub.sendMessage("createBuffer", buffer_type="MentionsBuffer", session_type=session.type, buffer_title=_("Mentions"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="notifications", name="mentions", sessionObject=session, account=name, sound="mention_received.ogg"))
            elif i == 'direct_messages':
                pub.sendMessage("createBuffer", buffer_type="ConversationListBuffer", session_type=session.type, buffer_title=_("Direct messages"), parent_tab=root_position, start=False, kwargs=dict(compose_func="compose_conversation", parent=controller.view.nb, function="conversations", name="direct_messages", sessionObject=session, account=name, sound="dm_received.ogg"))
            elif i == 'sent':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Sent"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="account_statuses", name="sent", sessionObject=session, account=name, sound="tweet_received.ogg", id=session.db["user_id"]))
            elif i == 'favorites':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Favorites"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="favourites", name="favorites", sessionObject=session, account=name, sound="favourite.ogg"))
            elif i == 'bookmarks':
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Bookmarks"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, function="bookmarks", name="bookmarks", sessionObject=session, account=name, sound="favourite.ogg"))
            elif i == 'followers':
                pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Followers"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_followers", name="followers", sessionObject=session, account=name, sound="update_followers.ogg", id=session.db["user_id"]))
            elif i == 'following':
                pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Following"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_following", name="following", sessionObject=session, account=name, sound="update_followers.ogg", id=session.db["user_id"]))
            elif i == 'muted':
                pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Muted users"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="mutes", name="muted", sessionObject=session, account=name))
            elif i == 'blocked':
                pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Blocked users"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="blocks", name="blocked", sessionObject=session, account=name))
            elif i == 'notifications':
                pub.sendMessage("createBuffer", buffer_type="NotificationsBuffer", session_type=session.type, buffer_title=_("Notifications"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_notification", function="notifications", name="notifications", sessionObject=session, account=name))
        pub.sendMessage("createBuffer", buffer_type="EmptyBuffer", session_type="base", buffer_title=_("Timelines"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, name="timelines", account=name))
        timelines_position =controller.view.search("timelines", name)
        for i in session.settings["other_buffers"]["timelines"]:
                pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=session.type, buffer_title=_("Timeline for {}").format(i), parent_tab=timelines_position, start=False, kwargs=dict(parent=controller.view.nb, function="account_statuses", name="{}-timeline".format(i), sessionObject=session, account=name, sound="tweet_timeline.ogg", id=i))
        for i in session.settings["other_buffers"]["followers_timelines"]:
            pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Followers for {}").format(i), parent_tab=timelines_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_followers", name="{}-followers".format(i,), sessionObject=session, account=name, sound="new_event.ogg", id=i))
        for i in session.settings["other_buffers"]["following_timelines"]:
            pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Following for {}").format(i), parent_tab=timelines_position, start=False, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_following", name="{}-following".format(i,), sessionObject=session, account=name, sound="new_event.ogg", id=i))
#        pub.sendMessage("createBuffer", buffer_type="EmptyBuffer", session_type="base", buffer_title=_("Lists"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, name="lists", name))
#        lists_position =controller.view.search("lists", session.db["user_name"])
#        for i in session.settings["other_buffers"]["lists"]:
#            pub.sendMessage("createBuffer", buffer_type="ListBuffer", session_type=session.type, buffer_title=_(u"List for {}").format(i), parent_tab=lists_position, start=False, kwargs=dict(parent=controller.view.nb, function="list_timeline", name="%s-list" % (i,), sessionObject=session, name, bufferType=None, sound="list_tweet.ogg", list_id=utils.find_list(i, session.db["lists"]), include_ext_alt_text=True, tweet_mode="extended"))
        pub.sendMessage("createBuffer", buffer_type="EmptyBuffer", session_type="base", buffer_title=_("Searches"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, name="searches", account=name))
        searches_position =controller.view.search("searches", name)
        for term in session.settings["other_buffers"]["post_searches"]:
            pub.sendMessage("createBuffer", buffer_type="SearchBuffer", session_type=session.type, buffer_title=_("Search for {}").format(term), parent_tab=searches_position, start=True, kwargs=dict(parent=controller.view.nb, compose_func="compose_post", function="search", name="%s-searchterm" % (term,), sessionObject=session, account=session.get_name(), sound="search_updated.ogg", q=term, result_type="statuses"))
        pub.sendMessage("createBuffer", buffer_type="EmptyBuffer", session_type="base", buffer_title=_("Communities"), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, name="communities", account=name))
        communities_position =controller.view.search("communities", name)
        for community in session.settings["other_buffers"]["communities"]:
            pub.sendMessage("createBuffer", buffer_type="CommunityBuffer", session_type=session.type, buffer_title=_("Community for {}").format(community.split("@")[1].replace("https://", "")), parent_tab=communities_position, start=True, kwargs=dict(parent=controller.view.nb, function="timeline", compose_func="compose_post", name=community, sessionObject=session, community_url=community.split("@")[1], account=session.get_name(), sound="search_updated.ogg", timeline=community.split("@")[0]))

#        for i in session.settings["other_buffers"]["trending_topic_buffers"]:
#            pub.sendMessage("createBuffer", buffer_type="TrendsBuffer", session_type=session.type, buffer_title=_("Trending topics for %s") % (i), parent_tab=root_position, start=False, kwargs=dict(parent=controller.view.nb, name="%s_tt" % (i,), sessionObject=session, name, trendsFor=i, sound="trends_updated.ogg"))

    def start_buffer(self, controller, buffer):
        if hasattr(buffer, "finished_timeline") and buffer.finished_timeline == False:
            change_title = True
        else:
            change_title = False
        try:
            buffer.start_stream(play_sound=False)
        except Exception as err:
            log.exception("Error %s starting buffer %s on account %s, with args %r and kwargs %r." % (str(err), buffer.name, buffer.account, buffer.args, buffer.kwargs))
        if change_title:
            pub.sendMessage("buffer-title-changed", buffer=buffer)

    def open_conversation(self, controller, buffer):
        post = buffer.get_item()
        if post.reblog != None:
            post = post.reblog
        conversations_position =controller.view.search("direct_messages", buffer.session.get_name())
        pub.sendMessage("createBuffer", buffer_type="ConversationBuffer", session_type=buffer.session.type, buffer_title=_("Conversation with {0}").format(post.account.acct), parent_tab=conversations_position, start=True, kwargs=dict(parent=controller.view.nb, function="status_context", name="%s-conversation" % (post.id,), sessionObject=buffer.session, account=buffer.session.get_name(), sound="search_updated.ogg", post=post, id=post.id))

    def follow(self, buffer):
        if not hasattr(buffer, "get_item"):
            return
        item = buffer.get_item()
        if buffer.type == "user":
            users = [item.acct]
        elif buffer.type == "baseBuffer":
            if item.reblog != None:
                users = [user.acct for user in item.reblog.mentions if user.id != buffer.session.db["user_id"]]
                if item.reblog.account.acct not in users and item.account.id != buffer.session.db["user_id"]:
                    users.insert(0, item.reblog.account.acct)
            else:
                users = [user.acct for user in item.mentions if user.id != buffer.session.db["user_id"]]
            if item.account.acct not in users:
                users.insert(0, item.account.acct)
        elif buffer.type == "notificationsBuffer":
            if buffer.is_post():
                status = item.status
                if status.reblog != None:
                    users = [user.acct for user in status.reblog.mentions if user.id != buffer.session.db["user_id"]]
                    if status.reblog.account.acct not in users and status.account.id != buffer.session.db["user_id"]:
                        users.insert(0, status.reblog.account.acct)
                else:
                    users = [user.acct for user in status.mentions if user.id != buffer.session.db["user_id"]]
        if hasattr(item, "account"):
            acct = item.account.acct
        else:
            acct = item.acct
        if acct not in users:
            users.insert(0, item.account.acct)
        u = userActions.userActions(buffer.session, users)

    def search(self, controller, session, value):
        log.debug("Creating a new search...")
        dlg = search_dialogs.searchDialog(value)
        if dlg.ShowModal() == wx.ID_OK and dlg.term.GetValue() != "":
            term = dlg.term.GetValue()
            searches_position =controller.view.search("searches", session.get_name())
            if dlg.posts.GetValue() == True:
                if term not in session.settings["other_buffers"]["post_searches"]:
                    session.settings["other_buffers"]["post_searches"].append(term)
                    session.settings.write()
                    pub.sendMessage("createBuffer", buffer_type="SearchBuffer", session_type=session.type, buffer_title=_("Search for {}").format(term), parent_tab=searches_position, start=True, kwargs=dict(parent=controller.view.nb, compose_func="compose_post", function="search", name="%s-searchterm" % (term,), sessionObject=session, account=session.get_name(), sound="search_updated.ogg", q=term, result_type="statuses"))
                else:
                    log.error("A buffer for the %s search term is already created. You can't create a duplicate buffer." % (term,))
                    return
            elif dlg.users.GetValue() == True:
                pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=session.type, buffer_title=_("Search for {}").format(term), parent_tab=searches_position, start=True, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_search", name="%s-searchUser" % (term,), sessionObject=session, account=session.get_name(), sound="search_updated.ogg", q=term))
        dlg.Destroy()

    # ToDo: explore how to play sound & save config differently.
    # currently, TWBlue will play the sound and save the config for the timeline even if the buffer did not load or something else.
    def open_timeline(self, controller, buffer):
        if not hasattr(buffer, "get_item"):
            return
        item = buffer.get_item()
        if buffer.type == "user":
            users = [item.acct]
        elif buffer.type == "baseBuffer":
            if item.reblog != None:
                users = [user.acct for user in item.reblog.mentions if user.id != buffer.session.db["user_id"]]
                if item.reblog.account.acct not in users and item.account.id != buffer.session.db["user_id"]:
                    users.insert(0, item.reblog.account.acct)
            else:
                users = [user.acct for user in item.mentions if user.id != buffer.session.db["user_id"]]
            if item.account.acct not in users and item.account.id != buffer.session.db["user_id"]:
                users.insert(0, item.account.acct)
        u = userActions.UserTimeline(buffer.session, users)
        if u.dialog.ShowModal() == wx.ID_OK:
            action = u.process_action()
            if action == None:
                return
            user = u.user
            if action == "posts":
                self.openPostTimeline(controller, buffer, user)
            elif action == "followers":
                self.openFollowersTimeline(controller, buffer, user)
            elif action == "following":
                self.openFollowingTimeline(controller, buffer, user)

    def openPostTimeline(self, controller, buffer, user):
        """Opens post timeline for user"""
        if user.statuses_count == 0:
            dialogs.no_posts()
            return
        if user.id in buffer.session.settings["other_buffers"]["timelines"]:
            commonMessageDialogs.timeline_exist()
            return
        timelines_position =controller.view.search("timelines", buffer.session.get_name())
        pub.sendMessage("createBuffer", buffer_type="BaseBuffer", session_type=buffer.session.type, buffer_title=_("Timeline for {}").format(user.username,), parent_tab=timelines_position, start=True, kwargs=dict(parent=controller.view.nb, function="account_statuses", name="%s-timeline" % (user.id,), sessionObject=buffer.session, account=buffer.session.get_name(), sound="tweet_timeline.ogg", id=user.id))
        buffer.session.settings["other_buffers"]["timelines"].append(user.id)
        buffer.session.sound.play("create_timeline.ogg")
        buffer.session.settings.write()

    def openFollowersTimeline(self, controller, buffer, user):
        """Open followers timeline for user"""
        if user.followers_count == 0:
            dialogs.no_followers()
            return
        if user.id in buffer.session.settings["other_buffers"]["followers_timelines"]:
            commonMessageDialogs.timeline_exist()
            return
        timelines_position =controller.view.search("timelines", buffer.session.get_name())
        pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=buffer.session.type, buffer_title=_("Followers for {}").format(user.username,), parent_tab=timelines_position, start=True, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_followers", name="%s-followers" % (user.id,), sessionObject=buffer.session, account=buffer.session.get_name(), sound="new_event.ogg", id=user.id))
        buffer.session.settings["other_buffers"]["followers_timelines"].append(user.id)
        buffer.session.sound.play("create_timeline.ogg")
        buffer.session.settings.write()

    def openFollowingTimeline(self, controller, buffer, user):
        """Open following timeline for user"""
        if user.following_count == 0:
            dialogs.no_following()
            return
        if user.id in buffer.session.settings["other_buffers"]["following_timelines"]:
            commonMessageDialogs.timeline_exist()
            return
        timelines_position =controller.view.search("timelines", buffer.session.get_name())
        pub.sendMessage("createBuffer", buffer_type="UserBuffer", session_type=buffer.session.type, buffer_title=_("Following for {}").format(user.username,), parent_tab=timelines_position, start=True, kwargs=dict(parent=controller.view.nb, compose_func="compose_user", function="account_following", name="%s-followers" % (user.id,), sessionObject=buffer.session, account=buffer.session.get_name(), sound="new_event.ogg", id=user.id))
        buffer.session.settings["other_buffers"]["following_timelines"].append(user.id)
        buffer.session.sound.play("create_timeline.ogg")
        buffer.session.settings.write()

    def account_settings(self, buffer, controller):
        d = settings.accountSettingsController(buffer, controller)
        if d.response == wx.ID_OK:
            d.save_configuration()
            if d.needs_restart == True:
                commonMessageDialogs.needs_restart()
                buffer.session.settings.write()
                buffer.session.save_persistent_data()
                restart.restart_program()

    def add_alias(self, buffer):
        if not hasattr(buffer, "get_item"):
            return
        item = buffer.get_item()
        if buffer.type == "user":
            users = [item.acct]
        elif buffer.type == "baseBuffer":
            if item.reblog != None:
                users = [user.acct for user in item.reblog.mentions if user.id != buffer.session.db["user_id"]]
                if item.reblog.account.acct not in users and item.account.id != buffer.session.db["user_id"]:
                    users.insert(0, item.reblog.account.acct)
            else:
                users = [user.acct for user in item.mentions if user.id != buffer.session.db["user_id"]]
            if item.account.acct not in users:
                users.insert(0, item.account.acct)
        dlg = userAliasDialogs.addAliasDialog(_("Add an user alias"), users)
        if dlg.get_response() == wx.ID_OK:
            user, alias = dlg.get_user()
            if user == "" or alias == "":
                return
            try:
                full_user = buffer.session.api.account_lookup(user)
            except Exception as e:
                log.exception("Error adding alias to user {}.".format(user))
                return
            buffer.session.settings["user-aliases"][str(full_user.id)] = alias
            buffer.session.settings.write()
            output.speak(_("Alias has been set correctly for {}.").format(user))
            pub.sendMessage("alias-added")

    def update_profile(self, session):
        """Updates the users dialog"""
        profile = session.api.me()
        data = {
                'display_name': profile.display_name,
                'note': html_filter(profile.note),
                'header': profile.header,
                'avatar': profile.avatar,
                'fields': [(field.name, html_filter(field.value)) for field in profile.fields],
                'locked': profile.locked,
                'bot': profile.bot,
                # discoverable could be None, set it to False
                'discoverable': profile.discoverable if profile.discoverable else False,
                }
        log.debug(f"Received data_ {data['fields']}")
        dialog = update_profile_dialogs.UpdateProfileDialog(**data)
        if dialog.ShowModal() != wx.ID_OK:
            log.debug("User canceled dialog")
            return
        updated_data = dialog.data
        if updated_data == data:
            log.debug("No profile info was changed.")
            return
        # remove data that hasn't been updated
        for key in data:
            if data[key] == updated_data[key]:
                del updated_data[key]
        log.debug(f"Updating users profile with: {updated_data}")
        call_threaded(session.api_call, "account_update_credentials", _("Update profile"), report_success=True, **updated_data)

    def user_details(self, buffer):
        """Displays user profile in a dialog.
        This works as long as the focused item hass a 'account' key."""
        if not hasattr(buffer, 'get_item'):
            return  # Tell user?
        item = buffer.get_item()
        if not item:
            return  # empty buffer

        log.debug(f"Opening user profile. dictionary: {item}")
        mentionedUsers = list()
        holdUser = item.account if item.get('account') else None
        if hasattr(item, "type") and item.type in ["status", "mention", "reblog", "favourite", "update", "poll"]: # statuses in Notification buffers
            item = item.status
        if item.get('username'):  # account dict
            holdUser = item
        elif isinstance(item.get('mentions'), list):
            # mentions in statuses
            if item.reblog:
                item = item.reblog
            mentionedUsers = [(user.acct, user.id) for user in item.mentions]
            holdUser = item.account
        if not holdUser:
            dialogs.no_user()
            return

        if len(mentionedUsers) == 0:
            user = holdUser
        else:
            mentionedUsers.insert(0, (holdUser.display_name, holdUser.username, holdUser.id))
            mentionedUsers = list(set(mentionedUsers))
            selectedUser = showUserProfile.selectUserDialog(mentionedUsers)
            if not selectedUser:
                return  # Canceled selection
            elif selectedUser[-1] == holdUser.id:
                user = holdUser
            else:  # We don't have this user's dictionary, get it!
                user = buffer.session.api.account(selectedUser[-1])
        dlg = showUserProfile.ShowUserProfile(user)
        dlg.ShowModal()

    def community_timeline(self, controller, buffer):
        dlg = communityTimeline.CommunityTimeline()
        if dlg.ShowModal() != wx.ID_OK:
            return
        url = dlg.url.GetValue()
        bufftype = dlg.get_action()
        local_api = mastodon.Mastodon(api_base_url=url)
        try:
            instance = local_api.instance()
        except MastodonError:
            commonMessageDialogs.invalid_instance()
            return
        if bufftype == "local":
            title = _(f"Local timeline for {url.replace('https://', '')}")
        else:
            title = _(f"Federated timeline for {url}")
            bufftype = "public"
        dlg.Destroy()
        tl_info = f"{bufftype}@{url}"
        if tl_info in buffer.session.settings["other_buffers"]["communities"]:
            return # buffer already exists.
        buffer.session.settings["other_buffers"]["communities"].append(tl_info)
        buffer.session.settings.write()
        communities_position =controller.view.search("communities", buffer.session.get_name())
        pub.sendMessage("createBuffer", buffer_type="CommunityBuffer", session_type=buffer.session.type, buffer_title=title, parent_tab=communities_position, start=True, kwargs=dict(parent=controller.view.nb, function="timeline", name=tl_info, sessionObject=buffer.session, account=buffer.session.get_name(), sound="tweet_timeline.ogg", community_url=url, timeline=bufftype))
