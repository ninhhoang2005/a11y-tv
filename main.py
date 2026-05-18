import wx
import vlc
import requests
import sys
import os
import threading

# --- Constants & Version ---
VERSION = "1.0"
APP_NAME = "a11y tv"
DATA_URL = "http://lc.ktgame207.com/a11y_tv_data/tv_channel.json"

class DataManager:
    def __init__(self):
        self.channels = []
        self.filtered_channels = []

    def fetch_data(self, callback):
        def run():
            try:
                # Tải dữ liệu json trực tiếp từ link
                r = requests.get(DATA_URL, timeout=15)
                r.raise_for_status() # Bắn ra lỗi nếu mã HTTP không phải 200 (ví dụ 404, 500)
                channels_data = r.json()
                
                self.channels = channels_data
                self.filtered_channels = self.channels
                wx.CallAfter(callback, True)
            except Exception as e:
                print(f"Lỗi tải dữ liệu: {e}")
                wx.CallAfter(callback, False)
        threading.Thread(target=run, daemon=True).start()

    def search(self, query):
        if not query:
            self.filtered_channels = self.channels
        else:
            q = query.lower()
            self.filtered_channels = [c for c in self.channels if q in c.get('name', '').lower()]
        return self.filtered_channels

class PlayerFrame(wx.Frame):
    def __init__(self, parent, channel):
        super().__init__(parent, title=f"Đang phát: {channel.get('name', 'Unknown')}", style=wx.DEFAULT_FRAME_STYLE)
        self.channel = channel
        self.SetBackgroundColour(wx.BLACK)
        
        try:
            self.Instance = vlc.Instance()
            self.player = self.Instance.media_player_new()
        except Exception:
            wx.MessageBox("Lỗi khởi tạo VLC. Hãy chắc chắn bạn đã cài VLC 64-bit.", "Lỗi", wx.OK | wx.ICON_ERROR)
            self.Close()
            return

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.BLACK)
        
        # Sizer cho video
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.panel, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)

        self.create_controls()

        # Dùng CHAR_HOOK để bắt phím tắt ở cấp độ cao nhất của Frame
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.play_stream()
        self.ShowFullScreen(True)

    def create_controls(self):
        self.ctrl_panel = wx.Panel(self.panel, size=(-1, 60))
        self.ctrl_panel.SetBackgroundColour(wx.Colour(30, 30, 30))
        
        inner_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_play_pause = wx.Button(self.ctrl_panel, label="Tạm dừng")
        self.btn_play_pause.Bind(wx.EVT_BUTTON, lambda e: self.toggle_play())
        
        self.btn_mute = wx.Button(self.ctrl_panel, label="Tắt tiếng")
        self.btn_mute.Bind(wx.EVT_BUTTON, lambda e: self.toggle_mute())
        
        self.btn_close = wx.Button(self.ctrl_panel, label="Đóng [Esc]")
        self.btn_close.Bind(wx.EVT_BUTTON, lambda e: self.Close())

        inner_sizer.Add(self.btn_play_pause, 0, wx.ALL | wx.CENTER, 10)
        inner_sizer.Add(self.btn_mute, 0, wx.ALL | wx.CENTER, 10)
        inner_sizer.AddStretchSpacer()
        inner_sizer.Add(self.btn_close, 0, wx.ALL | wx.CENTER, 10)
        self.ctrl_panel.SetSizer(inner_sizer)
        
        ctrl_sizer = wx.BoxSizer(wx.VERTICAL)
        ctrl_sizer.AddStretchSpacer()
        ctrl_sizer.Add(self.ctrl_panel, 0, wx.EXPAND)
        self.panel.SetSizer(ctrl_sizer)

    def play_stream(self):
        url = self.channel.get('url', '')
        Media = self.Instance.media_new(url)
        self.player.set_media(Media)
        if os.name == 'nt': self.player.set_hwnd(self.panel.GetHandle())
        else: self.player.set_xwindow(self.panel.GetHandle())
        self.player.play()

    def on_char_hook(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_ESCAPE:
            self.Close()
        elif key == wx.WXK_UP:
            vol = self.player.audio_get_volume()
            self.player.audio_set_volume(min(vol + 5, 100))
        elif key == wx.WXK_DOWN:
            vol = self.player.audio_get_volume()
            self.player.audio_set_volume(max(vol - 5, 0))
        elif key == ord('M') or key == ord('m'):
            self.toggle_mute()
        elif key == wx.WXK_SPACE:
            self.toggle_play()
        else:
            event.Skip()

    def toggle_play(self):
        if self.player.is_playing():
            self.player.pause()
            self.btn_play_pause.SetLabel("Phát")
        else:
            self.player.play()
            self.btn_play_pause.SetLabel("Tạm dừng")

    def toggle_mute(self):
        is_mute = self.player.audio_get_mute()
        self.player.audio_set_mute(not is_mute)
        self.btn_mute.SetLabel("Bật tiếng" if not is_mute else "Tắt tiếng")

    def on_close(self, event):
        self.player.stop()
        self.player.release()
        self.Instance.release()
        event.Skip()

class MainFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title=f"{APP_NAME} v{VERSION}", size=(600, 500))
        self.data_mgr = DataManager()
        self.setup_ui()
        self.Centre()
        
        # Bắt phím Enter toàn cục cho Frame
        self.Bind(wx.EVT_CHAR_HOOK, self.on_char_hook)
        
        self.status_bar.SetStatusText("Đang kết nối tới đám mây để tải kênh...")
        self.data_mgr.fetch_data(self.on_data_loaded)

    def setup_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        self.search_ctrl = wx.SearchCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.search_ctrl.SetDescriptiveText("Nhập tên kênh...")
        self.search_ctrl.Bind(wx.EVT_TEXT, self.on_search)

        self.list_box = wx.ListBox(panel, style=wx.LB_SINGLE | wx.LB_NEEDED_SB)
        self.list_box.Bind(wx.EVT_LISTBOX_DCLICK, lambda e: self.on_play_selected())
        self.list_box.Bind(wx.EVT_CONTEXT_MENU, self.on_context_menu)

        self.status_bar = self.CreateStatusBar()

        main_sizer.Add(wx.StaticText(panel, label="Tìm kiếm kênh:"), 0, wx.ALL, 5)
        main_sizer.Add(self.search_ctrl, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)
        main_sizer.Add(wx.StaticText(panel, label="Danh sách kênh:"), 0, wx.LEFT | wx.RIGHT, 10)
        main_sizer.Add(self.list_box, 1, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(main_sizer)

    def on_char_hook(self, event):
        key = event.GetKeyCode()
        # Nếu nhấn Enter khi đang ở bất kỳ đâu trong cửa sổ chính
        if key == wx.WXK_RETURN:
            # Nếu đang ở ô tìm kiếm mà nhấn Enter, cho phép tìm kiếm
            if self.FindFocus() == self.search_ctrl:
                event.Skip()
            else:
                self.on_play_selected()
        else:
            event.Skip()

    def on_data_loaded(self, success):
        if success:
            self.update_list()
            self.status_bar.SetStatusText(f"Sẵn sàng. Đã tải {len(self.data_mgr.channels)} kênh từ đám mây.")
            self.list_box.SetFocus()
        else:
            self.status_bar.SetStatusText("Không thể kết nối đám mây.")
            wx.MessageBox("Không thể tải kênh từ đám mây, vui lòng thử lại", "Lỗi Kết Nối", wx.OK | wx.ICON_ERROR)
            self.Close()
            sys.exit(1) # Đóng luôn phần mềm theo yêu cầu

    def update_list(self):
        self.list_box.Clear()
        for c in self.data_mgr.filtered_channels:
            self.list_box.Append(c.get('name', 'Unknown'))
        if self.list_box.GetCount() > 0:
            self.list_box.SetSelection(0)

    def on_search(self, event):
        query = self.search_ctrl.GetValue()
        self.data_mgr.search(query)
        self.update_list()

    def on_play_selected(self):
        selection = self.list_box.GetSelection()
        if selection != wx.NOT_FOUND:
            channel = self.data_mgr.filtered_channels[selection]
            player = PlayerFrame(self, channel)
            player.Show()

    def on_context_menu(self, event):
        menu = wx.Menu()
        item_play = menu.Append(wx.ID_ANY, "Phát (Enter)")
        self.Bind(wx.EVT_MENU, lambda e: self.on_play_selected(), item_play)
        self.PopupMenu(menu)
        menu.Destroy()

if __name__ == "__main__":
    app = wx.App()
    frame = MainFrame()
    frame.Show()
    app.MainLoop()
