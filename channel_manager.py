import wx
import json
import os

JSON_FILE = "tv_channel.json"

class ChannelDialog(wx.Dialog):
    def __init__(self, parent, title, name="", url=""):
        super().__init__(parent, title=title, size=(400, 250))
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Name
        sizer.Add(wx.StaticText(panel, label="Tên kênh:"), 0, wx.ALL, 5)
        self.tc_name = wx.TextCtrl(panel, value=name)
        sizer.Add(self.tc_name, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # URL
        sizer.Add(wx.StaticText(panel, label="Link luồng phát (URL):"), 0, wx.ALL, 5)
        self.tc_url = wx.TextCtrl(panel, value=url)
        sizer.Add(self.tc_url, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        btn_save = wx.Button(panel, id=wx.ID_OK, label="Lưu thay đổi")
        btn_cancel = wx.Button(panel, id=wx.ID_CANCEL, label="Hủy")
        
        btn_sizer.Add(btn_save, 0, wx.ALL, 5)
        btn_sizer.Add(btn_cancel, 0, wx.ALL, 5)
        
        sizer.AddStretchSpacer()
        sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)
        
        panel.SetSizer(sizer)
        self.Centre()
        
    def get_data(self):
        return self.tc_name.GetValue().strip(), self.tc_url.GetValue().strip()

class ManagerFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Công cụ Quản lý Kênh a11y tv", size=(500, 600))
        self.channels = []
        self.load_data()
        
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Layout components creation
        lbl_list = wx.StaticText(panel, label="Danh sách kênh đang có (Lưu ở máy cục bộ):")
        
        # Danh sách kênh
        self.list_box = wx.ListBox(panel, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)
        self.list_box.SetName("Danh sách kênh đang có")
        self.update_listbox()
        
        # Buttons
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_add = wx.Button(panel, label="Thêm kênh mới")
        self.btn_edit = wx.Button(panel, label="Sửa kênh")
        self.btn_delete = wx.Button(panel, label="Xóa kênh")
        self.btn_save_file = wx.Button(panel, label="Lưu thành File JSON")
        
        self.btn_add.Bind(wx.EVT_BUTTON, self.on_add)
        self.btn_edit.Bind(wx.EVT_BUTTON, self.on_edit)
        self.btn_delete.Bind(wx.EVT_BUTTON, self.on_delete)
        self.btn_save_file.Bind(wx.EVT_BUTTON, self.on_save_file)
        
        btn_sizer.Add(self.btn_add, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_edit, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_delete, 0, wx.ALL, 5)
        btn_sizer.Add(self.btn_save_file, 0, wx.ALL, 5)
        
        # Layout
        main_sizer.Add(lbl_list, 0, wx.ALL, 5)
        main_sizer.Add(self.list_box, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        main_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        self.Centre()
        
    def load_data(self):
        if os.path.exists(JSON_FILE):
            try:
                with open(JSON_FILE, "r", encoding="utf-8") as f:
                    self.channels = json.load(f)
            except Exception as e:
                wx.MessageBox(f"Lỗi đọc file: {e}", "Lỗi", wx.OK | wx.ICON_ERROR)
                self.channels = []
                
    def save_data(self):
        try:
            with open(JSON_FILE, "w", encoding="utf-8") as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=2)
            wx.MessageBox(f"Đã lưu thành công vào file '{JSON_FILE}'!\nBạn có thể tải file này lên máy chủ web của bạn.", "Thành công", wx.OK | wx.ICON_INFORMATION)
        except Exception as e:
            wx.MessageBox(f"Lỗi lưu file: {e}", "Lỗi", wx.OK | wx.ICON_ERROR)

    def update_listbox(self):
        self.list_box.Clear()
        for c in self.channels:
            self.list_box.Append(c.get('name', 'Unknown'))
        
        if self.list_box.GetCount() > 0:
            self.list_box.SetSelection(0)

    def on_add(self, event):
        dlg = ChannelDialog(self, "Thêm kênh mới")
        if dlg.ShowModal() == wx.ID_OK:
            name, url = dlg.get_data()
            if name and url:
                self.channels.append({"name": name, "url": url})
                self.update_listbox()
        dlg.Destroy()

    def on_edit(self, event):
        sel = self.list_box.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Vui lòng chọn một kênh để sửa.", "Thông báo", wx.OK | wx.ICON_WARNING)
            return
            
        channel = self.channels[sel]
        dlg = ChannelDialog(self, "Sửa kênh", channel.get('name', ''), channel.get('url', ''))
        if dlg.ShowModal() == wx.ID_OK:
            name, url = dlg.get_data()
            if name and url:
                self.channels[sel] = {"name": name, "url": url}
                self.update_listbox()
        dlg.Destroy()

    def on_delete(self, event):
        sel = self.list_box.GetSelection()
        if sel == wx.NOT_FOUND:
            wx.MessageBox("Vui lòng chọn một kênh để xóa.", "Thông báo", wx.OK | wx.ICON_WARNING)
            return
            
        name = self.channels[sel].get('name', '')
        if wx.MessageBox(f"Bạn có chắc muốn xóa kênh '{name}' không?", "Xác nhận", wx.YES_NO | wx.ICON_QUESTION) == wx.YES:
            del self.channels[sel]
            self.update_listbox()

    def on_save_file(self, event):
        self.save_data()

if __name__ == "__main__":
    app = wx.App()
    frame = ManagerFrame()
    frame.Show()
    app.MainLoop()
