from kivy.app import App
from mainwidget import MainWidget
from kivy.lang.builder import Builder


class MainApp(App):
    """
    Classe com o aplicativo
    """

    def build(self):
        """
        Método que gera o aplicativo com base no widget principal
        """
        self._widget = MainWidget(
            scan_time=1000,                     
            # server_ip='192.168.0.14', #INTERNO
            # server_port=502,

            # server_ip='10.15.20.17', #EXTERNO
            # server_port=10014,

            server_ip='localhost', #SIMULADOR
            server_port=502,
            modbus_addrs=self.getTagsConfigs()
        )

        return self._widget

    def getTagsConfigs(self):
        return {
            "velocity": {"type": "mainLabel", "address": 884, "div": 1, "unit": "RPM", "ymax": 3500},
            "torque": {"type": "mainLabel", "address": 1420, "div": 1, "unit": "N.m", "ymax": 4},
            "pit01": {"type": "mainLabel", "address": 714, "div": 1, "unit": "kgf/cm3", "ymax": 5},
            "fv01": {"type": "mainLabel", "address": 1310, "div": 1, "unit": "%", "ymax": 100},
            "fit02": {"type": "mainLabel", "address": 718, "div": 1, "unit": "Nm3/min", "ymax": 15},
            "fit03": {"type": "mainLabel", "address": 716, "div": 1, "unit": "Nm3/min", "ymax": 15},
            "xv1": {"type": "Valve", "address": 712, "bit": 0},
            "xv2": {"type": "Valve", "address": 712, "bit": 1},
            "xv3": {"type": "Valve", "address": 712, "bit": 2},
            "xv4": {"type": "Valve", "address": 712, "bit": 3},
            "xv5": {"type": "Valve", "address": 712, "bit": 4},
            "xv6": {"type": "Valve", "address": 712, "bit": 5},
            "freq": {"type": "motorInfo", "address": 830, "div": 100, "unit": "Hz"},
            "current": {"type": "motorInfo", "address": 845, "div": 10, "unit": "A", "ymax": 5},
            "P": {"type": "motorInfo", "address": 855, "div": 1, "unit": "W", "ymax": 1500},
            "Q": {"type": "negative", "address": 859, "div": 1, "unit": "VAr", "ymax": 1000},
            "S": {"type": "motorInfo", "address": 863, "div": 1, "unit": "VA", "ymax": 2000},
            "startType": {"type": "startType", "address": 1216, "div": 1},
            "activeMotor": {"type": "activeMotor", "address": 1328, "bit": 1},
            "inversorFreq": {"type": "inversorFreq", "address": 1313, "div": 10},
            "accTime": {"type": "accDccTime", "address": 1317, "div": 10},
            "desaccTime": {"type": "accDccTime", "address": 1318, "div": 10}
        }

    def on_stop(self):
        """
        Método executado quando a aplicação é fechada
        """
        self._widget.stopRefresh()


if __name__ == '__main__':
    Builder.load_string(open("mainwidget.kv", encoding="utf-8").read(), rulesonly=True)
    Builder.load_string(open("popups.kv", encoding="utf-8").read(), rulesonly=True)
    MainApp().run()
