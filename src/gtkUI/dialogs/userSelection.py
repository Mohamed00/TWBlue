# -*- coding: utf-8 -*-
import wx

class selectUserDialog(wx.Dialog):
 def __init__(self, users=[], default="tweets", *args, **kwargs):
  super(selectUserDialog, self).__init__(parent=None, *args, **kwargs)
  panel = wx.Panel(self)
  userSizer = wx.BoxSizer()
  self.SetTitle(_(u"Timeline for %s") % (users[0]))
  userLabel = wx.StaticText(panel, -1, _(u"User"))
  self.cb = wx.ComboBox(panel, -1, choices=users, value=users[0])
  self.cb.SetFocus()
  userSizer.Add(userLabel, 0, wx.ALL, 5)
  userSizer.Add(self.cb, 0, wx.ALL, 5)
  actionSizer = wx.BoxSizer(wx.VERTICAL)
  label2 = wx.StaticText(panel, -1, _(u"Buffer type"))
  self.tweets = wx.RadioButton(panel, -1, _(u"Tweets"), style=wx.RB_GROUP)
  self.favourites = wx.RadioButton(panel, -1, _(u"Favourites"))
  self.setup_default(default)
  hSizer = wx.BoxSizer(wx.HORIZONTAL)
  hSizer.Add(label2, 0, wx.ALL, 5)
  actionSizer.Add(self.tweets, 0, wx.ALL, 5)
  actionSizer.Add(self.favourites, 0, wx.ALL, 5)
  hSizer.Add(actionSizer, 0, wx.ALL, 5)
  sizer = wx.BoxSizer(wx.VERTICAL)
  ok = wx.Button(panel, wx.ID_OK, _(u"OK"))
  ok.SetDefault()
  cancel = wx.Button(panel, wx.ID_CANCEL, _(u"Close"))
  btnsizer = wx.BoxSizer()
  btnsizer.Add(ok)
  btnsizer.Add(cancel)
  sizer.Add(userSizer)
  sizer.Add(hSizer, 0, wx.ALL, 5)
  sizer.Add(btnsizer)
  panel.SetSizer(sizer)

 def get_action(self):
  if self.tweets.GetValue() == True: return "tweets"
  elif self.favourites.GetValue() == True: return "favourites"

 def setup_default(self, default):
  if default == "tweets":
   self.tweets.SetValue(True)
  elif default == "favourites":
   self.favourites.SetValue(True)

 def get_response(self):
  return self.ShowModal()

 def get_user(self):
  return self.cb.GetValue()