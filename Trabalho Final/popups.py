from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.slider import Slider
from timeseriesgraph import TimeSeriesGraph
from kivy_garden.graph import LinePlot
from kivy.uix.boxlayout import BoxLayout

class ModbusPopup(Popup):
    """
    Popup da configuração do protocolo MODBUS
    """
    _info_lb = None
    
    def __init__(self, server_ip, server_port, **kwargs):
        """
        Construtor da classe ScanPopup
        """
        super().__init__(**kwargs)
        self.ids.txt_ip.text = str(server_ip)
        self.ids.txt_port.text = str(server_port)

    def setInfo(self, message):
        self._info_lb = Label(text = message)
        self.ids.layout.add_widget(self._info_lb)

    def clearInfo(self): 
        if self._info_lb is not None:
            self.ids.layout.remove_widget(self._info_lb)


class ScanPopup(Popup):
    """
    Popup da configuração do tempo de varredura
    """
    def __init__(self, scanTime, **kwargs):
        """
        Construtor da classe ScanPopup
        """
        super().__init__(**kwargs)
        self.ids.txt_st.text = str(scanTime)

class MotorPopup(Popup):
    """
    Popup das demais informações do motor
    """
    pass

class CommandsPopup(Popup):
    """
    Popup dos comandos para atuação
    """
    pass
    
class RealTimeGraphPopup(Popup):
    def __init__(self,xmax,plot_color,tags,**kwargs):
        super().__init__(**kwargs)
        self._plotPit = LinePlot(line_width=1.5,color=plot_color[0])
        self.ids.real_timeGraphPit.add_plot(self._plotPit)
        self.ids.real_timeGraphPit.xmax = xmax
        self._plotFit = LinePlot(line_width=1.5,color=plot_color[1])
        self.ids.real_timeGraphFit.add_plot(self._plotFit)
        self.ids.real_timeGraphFit.xmax = xmax
        
class LabelCheckBoxPointsPitDataGraph(BoxLayout):
    pass

class LabelCheckBoxPointsFitDataGraph(BoxLayout):
    pass

class HistGraphPopup(Popup):
    def __init__(self,**kwargs):
        super().__init__()
        for key,value in kwargs.get('tags').items():
            if key == 'velocity' or key == 'torque' or key == 'pit01' or key == 'fit03' or key == 'P' or key == 'Q' or  key == 'S' or key == 'current':
                cb = LabelCheckBoxHistGraph()
                cb.ids.label.text= key + ' [' + value['unit'] + ']'
                cb.ids.label.color = value['color']
                cb.id = key
                cb.ids.checkbox.group = 'cb_hist'
                self.ids.sensores.add_widget(cb)
            else:
                continue

        
class LabelCheckBoxHistGraph(BoxLayout):
    pass
        