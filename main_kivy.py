from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.scrollview import ScrollView
from kivy.core.window import Window
from kivy.clock import Clock
from liuyao import calculate_liuyao, format_liuyao_result
from bazi import calculate_bazi, format_bazi_result

Window.size = (400, 700)

class PaipanTab(TabbedPanelItem):
    pass

class LiuyaoTab(PaipanTab):
    def __init__(self, **kwargs):
        super().__init__(text='六爻', **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 日期输入
        date_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        self.year_input = TextInput(hint_text='年', input_filter='int', size_hint_x=0.3)
        self.month_input = TextInput(hint_text='月', input_filter='int', size_hint_x=0.3)
        self.day_input = TextInput(hint_text='日', input_filter='int', size_hint_x=0.3)
        date_layout.add_widget(self.year_input)
        date_layout.add_widget(self.month_input)
        date_layout.add_widget(self.day_input)
        
        # 六爻输入
        yao_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        self.yao_inputs = []
        for i in range(6):
            yao_input = TextInput(hint_text=f'第{i+1}爻', input_filter='int', size_hint_x=1/6)
            self.yao_inputs.append(yao_input)
            yao_layout.add_widget(yao_input)
        
        # 按钮
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        self.calc_btn = Button(text='排盘', on_press=self.calculate)
        self.clear_btn = Button(text='清空', on_press=self.clear)
        btn_layout.add_widget(self.calc_btn)
        btn_layout.add_widget(self.clear_btn)
        
        # 结果显示
        scroll = ScrollView()
        self.result_label = Label(text='', size_hint_y=None, text_size=(self.width, None))
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        scroll.add_widget(self.result_label)
        
        layout.add_widget(date_layout)
        layout.add_widget(yao_layout)
        layout.add_widget(btn_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
    
    def calculate(self, instance):
        try:
            year = int(self.year_input.text) if self.year_input.text else 2024
            month = int(self.month_input.text) if self.month_input.text else 6
            day = int(self.day_input.text) if self.day_input.text else 15
            
            yao_list = []
            for yao_input in self.yao_inputs:
                val = int(yao_input.text) if yao_input.text else 1
                yao_list.append(val)
            
            res = calculate_liuyao(yao_list, year, month, day)
            if 'error' in res:
                self.result_label.text = f'错误: {res["error"]}'
            else:
                self.result_label.text = format_liuyao_result(res)
        except Exception as e:
            self.result_label.text = f'错误: {str(e)}'
    
    def clear(self, instance):
        self.year_input.text = ''
        self.month_input.text = ''
        self.day_input.text = ''
        for yao_input in self.yao_inputs:
            yao_input.text = ''
        self.result_label.text = ''

class BaziTab(PaipanTab):
    def __init__(self, **kwargs):
        super().__init__(text='八字', **kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # 日期输入
        date_layout = BoxLayout(orientation='horizontal', size_hint_y=0.15)
        self.year_input = TextInput(hint_text='年', input_filter='int', size_hint_x=0.3)
        self.month_input = TextInput(hint_text='月', input_filter='int', size_hint_x=0.3)
        self.day_input = TextInput(hint_text='日', input_filter='int', size_hint_x=0.3)
        self.hour_input = TextInput(hint_text='时', input_filter='int', size_hint_x=0.1)
        date_layout.add_widget(self.year_input)
        date_layout.add_widget(self.month_input)
        date_layout.add_widget(self.day_input)
        date_layout.add_widget(self.hour_input)
        
        # 按钮
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.1)
        self.calc_btn = Button(text='排盘', on_press=self.calculate)
        self.clear_btn = Button(text='清空', on_press=self.clear)
        btn_layout.add_widget(self.calc_btn)
        btn_layout.add_widget(self.clear_btn)
        
        # 结果显示
        scroll = ScrollView()
        self.result_label = Label(text='', size_hint_y=None, text_size=(self.width, None))
        self.result_label.bind(texture_size=self.result_label.setter('size'))
        scroll.add_widget(self.result_label)
        
        layout.add_widget(date_layout)
        layout.add_widget(btn_layout)
        layout.add_widget(scroll)
        
        self.add_widget(layout)
    
    def calculate(self, instance):
        try:
            year = int(self.year_input.text) if self.year_input.text else 2024
            month = int(self.month_input.text) if self.month_input.text else 6
            day = int(self.day_input.text) if self.day_input.text else 15
            hour = int(self.hour_input.text) if self.hour_input.text else 12
            
            res = calculate_bazi(year, month, day, hour)
            if 'error' in res:
                self.result_label.text = f'错误: {res["error"]}'
            else:
                self.result_label.text = format_bazi_result(res)
        except Exception as e:
            self.result_label.text = f'错误: {str(e)}'
    
    def clear(self, instance):
        self.year_input.text = ''
        self.month_input.text = ''
        self.day_input.text = ''
        self.hour_input.text = ''
        self.result_label.text = ''

class PaipanApp(App):
    def build(self):
        tp = TabbedPanel()
        tp.add_widget(LiuyaoTab())
        tp.add_widget(BaziTab())
        return tp

if __name__ == '__main__':
    PaipanApp().run()
