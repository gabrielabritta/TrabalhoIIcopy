from kivy.uix.boxlayout import BoxLayout
from popups import ModbusPopup, ScanPopup, MotorPopup, CommandsPopup, RealTimeGraphPopup, HistGraphPopup
from pyModbusTCP.client import ModbusClient
from pyModbusTCP.utils import get_2comp
from kivy.core.window import Window
from kivy.clock import Clock
from threading import Thread
from time import sleep
from datetime import datetime
from pymodbus.payload import BinaryPayloadBuilder, BinaryPayloadDecoder
from pymodbus.constants import Endian
from functools import partial
from threading import Lock
from db import Base,Session,engine
from models import DadoCLP
import copy
import random
from kivy_garden.graph import LinePlot
from sqlalchemy.orm import load_only
from datetime import datetime


class MainWidget(BoxLayout):
    """
    Widget principal da aplicação
    """
    _updateThread = None
    _updateWidgets = True
    _tags = {}
    _max_points = 20

    def __init__(self, **kwargs):
        """
        Construtor do widget principal
        """
        super().__init__()
        self._scan_time = kwargs.get('scan_time')
        self._serverIp = kwargs.get('server_ip')
        self._serverPort = kwargs.get('server_port')
        self._modbusPopup = ModbusPopup(self._serverIp, self._serverPort)
        self._scanPopup = ScanPopup(self._scan_time)
        self._commands = CommandsPopup()
        self._motor = MotorPopup()
        self._modbusClient = ModbusClient(host=self._serverIp, port=self._serverPort)
        self._meas = {}
        self._meas['timestamp'] = None
        self._meas['values'] = {}
        self._lock = Lock()
        self._autoRelig = False
        self._pressMin = 0
        self._pressMax = 5
        self._session = Session() #incializando session pro BD
        Base.metadata.create_all(engine) #criando pro BD
        
        for key, value in kwargs.get('modbus_addrs').items():
            self._tags[key] = value
            if key == 'pit01':
                plot_color = (1,0,0,1)
            else:
                plot_color = (random.random(),random.random(),random.random(),1)
            self._tags[key]['color'] = plot_color
        
        self._realTimeGraph = RealTimeGraphPopup(self._max_points,[(1,0,0,1),(0,0,1,1)],tags = self._tags)
        self._hGraph = HistGraphPopup(tags=self._tags)

    def connectOrDisconnect(self, ip, port):
        if self._modbusClient.is_open:
            self._modbusClient.close()
            self._modbusPopup.dismiss()
            self._modbusPopup.ids.connect_button.text = "Conectar"
            self.ids.img_con.source = 'imgs/desconectado.png'
            self._updateWidgets = False
            self.ids.measButton.disabled = True
            self.ids.commandsButton.disabled = True
        else:
            self._modbusPopup.dismiss()
            self._modbusPopup.ids.connect_button.text = "Desconectar"
            self._updateWidgets = True
            self.ids.measButton.disabled = False
            self.ids.commandsButton.disabled = False
            self.startDataRead(ip, port)

    def startDataRead(self, ip, port):
        """
        Método utilizado para a configuração do IP e porta do servidor MODBUS e
        inicializar uma thread para a leitura dos dados e atualização da interface gráfica
        """
        self._serverIP = ip
        self._serverPort = port
        self._modbusClient.host = self._serverIP
        self._modbusClient.port = self._serverPort

        try:
            Window.set_system_cursor("wait")
            self._modbusClient.open()
            Window.set_system_cursor("arrow")

            if self._modbusClient.is_open:
                self._updateThread = Thread(target=self.updater)
                self._updateThread.start()
                self.ids.img_con.source = 'imgs/conectado.png'
                
            else:
                self._modbusPopup.setInfo("Falha na conexão com o servidor")
        except Exception as e:
            print("Erro: ", e.args)

    def updater(self):
        """
        Método que invoca as rotinas de leitura dos dados, atualização da interface e inserção dos dados no Banco de dados
        """
        
        while self._updateWidgets:
            try:
                with self._lock:
                    self.readData()
                self.updateGUI()
                self.insertDB()
                sleep(self._scan_time/1000)
            except Exception as e:
                #self._modbusClient.close()
                print("Erro: ", e.args)

    def readData(self):
        """
        Método para a leitura dos dados por meio do protocolo MODBUS
        """
        self._meas['timestamp'] = datetime.now()
        for key, value in self._tags.items():
            if value['type'] == "mainLabel":
                self._meas['values'][key] = self.readFP(value['address'], value['div'])
            elif value['type'] == "Valve" or value['type'] == "activeMotor":
                self._meas['values'][key] = self.readMultipleBits(value['address'], value['bit'])
            elif value['type'] == "negative":
                self._meas['values'][key] = self.readNegativeNumber(value['address'], value['div'])
            else:
                try:
                    self._meas['values'][key] = self.readSingleRegister(value['address'], value['div'])
                except Exception as e:
                    print("teste")

        if self._autoRelig == True and self._meas['values']['pit01'] < float(self._pressMin):
            self.commandMotor(1)
        if self._autoRelig == True and self._meas['values']['pit01'] > float(self._pressMax):
            self.commandMotor(0)

    def readNegativeNumber(self, address, divisor):
        """
        Método para a leitura e decodificação de dados negativos
        """
        codificatedData = self._modbusClient.read_holding_registers(address, 1)[0]
        data = get_2comp(codificatedData, 16)

        return round(data/divisor, 2)

    def readFP(self, address, divisor):
        """
        Método para a leitura e decodificação de dados floating point
        """
        codificatedData = self._modbusClient.read_holding_registers(address, 2)
        decoder = BinaryPayloadDecoder.fromRegisters(codificatedData, byteorder=Endian.Big, wordorder=Endian.Little)

        return round(decoder.decode_32bit_float()/divisor, 2)
    
    def readMultipleBits(self, address, bit):
        """
        Método para a leitura de um bit específico em um registrador
        """
        value = self._modbusClient.read_holding_registers(address,1)[0]
        bitsList = [int(x) for x in '{0:016b}'.format(value)]

        return bitsList[15 - bit]
    
    def readSingleRegister(self, address, divisor):
        """
        Método para a leitura de um registrador 16bits
        """
        value = self._modbusClient.read_holding_registers(address, 1)
        if value is not None and len(value) > 0:
            return round(value[0]/divisor,2)

    def writeHolding(self, address, value, multi=1):
        """
        Método para a escrita de Holding Registers por meio do protocolo MODBUS
        """
        try:
            if not isinstance(value, str) or len(value) > 0:
                self._modbusClient.write_single_register(address, int(value)*multi)
        except Exception as e:
            print("deu ruim")
        
    def writeBit(self, address, bit, value):
        '''
        Método para escrever em um bit específico de um registrador
        '''
        with self._lock:
            codificatedData = self._modbusClient.read_holding_registers(address, 1)
            if codificatedData is not None and len(codificatedData) > 0:
                codificatedData = self._modbusClient.read_holding_registers(address, 1)[0]
                register_list = [int(x) for x in '{0:016b}'.format(codificatedData)]
                register_list[15-bit] = value
                intValue = int("0b" + ''.join(map(str, register_list)), 2)

                self.writeHolding(address, intValue)
                #self._modbusClient.write_single_register(address, intValue)

    def updateGUI(self):
        """
        Método para atualização da interface gráfica a partir dos dados lidos
        """
        for key, value in self._tags.items():
            # Se for BIT alterar a label e a cor de fundo
            if value['type'] == "Valve":
                if self._meas['values'][key] == 1:
                    self.ids[key].text = "ABERTA"
                    self.ids[key].color = (1,1,1,1)
                    Clock.schedule_once(partial(self.changeBackgroundColor,key, (0.2,0.2,0.2)))
                    self._commands.ids[key+"open"].active = True
                    self._commands.ids[key+"close"].active = False

                elif self._meas['values'][key] == 0:
                    self.ids[key].text = "FECHADA" 
                    self.ids[key].color = (0,0,0,1)
                    Clock.schedule_once(partial(self.changeBackgroundColor,key, (0.6,0.6,0.6)))
                    self._commands.ids[key+"open"].active = False
                    self._commands.ids[key+"close"].active = True

            elif value['type'] == "motorInfo" or value['type'] ==  "negative":
                self._motor.ids[key].text = str(self._meas['values'][key]) + " " + value['unit']

            elif value['type'] == "mainLabel":
                self.ids[key].text = str(self._meas['values'][key]) + " " + value['unit']

            elif value['type'] == "startType":
                if self._meas['values'][key] == 3:
                    self.disableStartType('directStart')
                elif self._meas['values'][key] == 1:
                    self.disableStartType('softStarter')
                elif self._meas['values'][key] == 2:
                    self.disableStartType('inversorStart')

            elif value['type'] == "activeMotor":
                if self._meas['values'][key] == 0:
                    self._commands.ids['activeMotorButton'].disabled = True
                    self._commands.ids['desactiveMotorButton'].disabled = False
                    self.disableStartType('all')
                    self.ids[key].text = "LIGADO"
                    self.ids[key].color = (1,1,1,1)
                    Clock.schedule_once(partial(self.changeBackgroundColor,key, (0.2,0.2,0.2)))
                elif self._meas['values'][key] == 1:
                    self._commands.ids['activeMotorButton'].disabled = False
                    self._commands.ids['desactiveMotorButton'].disabled = True
                    self.ids[key].text = "DESLIGADO"
                    self.ids[key].color = (0,0,0,1)
                    Clock.schedule_once(partial(self.changeBackgroundColor,key, (0.6,0.6,0.6)))
                    
            elif value['type'] == "inversorFreq" and self._meas['values'][key]:
                self._commands.ids['inversorFreq'].value = int(self._meas['values'][key])

            elif value['type'] == "controlType":
                if self._meas['values'][key] == 0: 
                    self._commands.ids['auto'].active = True
                    self._commands.ids['minPress'].disabled = False
                    self._commands.ids['maxPress'].disabled = False

                elif self._meas['values'][key] == 1:
                    self._commands.ids['manual'].active = True
                    self._commands.ids['minPress'].disabled = True
                    self._commands.ids['maxPress'].disabled = True


        #Atualização da pressão
        self.ids.move_pit01.size = (self._meas['values']['pit01']/5*self.ids.pressure.size[0]*0.54, self.ids.move_pit01.size[1])
                
        
        #Atualização do gráfico
        self._realTimeGraph.ids.real_timeGraphPit.updateGraph((self._meas['timestamp'],self._meas['values']['pit01']),0)
        self._realTimeGraph.ids.real_timeGraphFit.updateGraph((self._meas['timestamp'],self._meas['values']['fit03']),0)

    def insertDB(self):
        #Armazenamento de dados no BD
        self._copyCLP = copy.deepcopy(self._meas)
        self._copyCLP['values'].pop('accTime')
        self._copyCLP['values'].pop('desaccTime')

        if self._copyCLP['values']['startType'] == 0:
            self._copyCLP['values']['startType'] = 'Direta'
        elif self._copyCLP['values']['startType'] == 1:
            self._copyCLP['values']['startType'] = 'Soft Start'
        elif self._copyCLP['values']['startType'] == 2:
            self._copyCLP['values']['startType'] = 'Inversor'
        
        if self._copyCLP['values']['activeMotor'] == 0:
            self._copyCLP['values']['activeMotor'] = 'Desligado'
        elif self._copyCLP['values']['activeMotor'] ==1:
            self._copyCLP['values']['activeMotor'] = 'Ligado'
            
        dado = DadoCLP(timestamp = self._copyCLP['timestamp'], **self._copyCLP['values'])
        self._session.add(dado)
        self._session.commit()

    def changeBackgroundColor(self, widgetId, rgb, dt):
        """
        Método para alterar a cor de fundo de uma label
        """
        self.ids[widgetId].canvas.before.children[0].rgb = rgb

    def changeTextInput(self, widgetId, text, dt):
        """
        Método para alterar a cor de fundo de uma label
        """
        self._commands.ids[widgetId].text = text

    def stopRefresh(self):
        """
        Método para interromper a interface
        """
        self._updateWidgets = False

    def commandMotor(self, commandType):
        startTypeDictionary = {
            3: 1319, #Direta
            1: 1316, #Soft
            2: 1312  #Inversor 
        }
        
        self.writeHolding(startTypeDictionary[self._meas['values']['startType']], commandType)
        #self._modbusClient.write_single_register(startTypeDictionary[self._meas['values']['startType']], commandType)

    def disableStartType(self, activeType): 
        startTypes = ['directStart', 'softStarter', 'inversorStart']

        for startType in startTypes:
            if activeType != startType and activeType != 'all':
                self._commands.ids[startType].disabled = False
            else:
                self._commands.ids[startType].disabled = True

            if activeType == 'inversorStart' or activeType == 'all':
                self._commands.ids['inversorFreq'].disabled = False
            else:
                self._commands.ids['inversorFreq'].disabled = True

            if activeType == 'directStart':
                self._commands.ids.accTime.disabled = True
                self._commands.ids.desaccTime.disabled = True
            else:
                self._commands.ids.accTime.disabled = False
                self._commands.ids.desaccTime.disabled = False
                
    def getDataDB(self):
        """
        Método que coleta as informações da interface fornecidas pelo usuário
        e requisita a busca no BD
        """
        try:
            if (not self.validateDate(self._hGraph.ids.txt_init_time.text) or not self.validateDate(self._hGraph.ids.txt_final_time.text)):
                return

            init_t = self.parseDTString(self._hGraph.ids.txt_init_time.text) 
            final_t = self.parseDTString(self._hGraph.ids.txt_final_time.text)
            cols = []
            for sensor in self._hGraph.ids.sensores.children:
                if sensor.ids.checkbox.active:
                    cols.append(sensor.id)
            if init_t is None or final_t is None or len(cols)==0:
                return

            data = self._session.query(DadoCLP).filter(DadoCLP.timestamp.between(init_t,final_t)).all()
            
            data_timeList = [reg.get_attr_list() for reg in data]
                
            if data is None or len(data)==0:
                return
            
            self._hGraph.ids.hist_timeGraph.clearPlots()

            for var in cols:          
                p = LinePlot(line_width = 1.5, color=self._tags[var]['color'])
                x = [i for i in range(len(data))]
                y = [getattr(row,var) for row in data]
                
                p.points = list(zip(x,y))                
                self._hGraph.ids.hist_timeGraph.add_plot(p)
                
            self._hGraph.ids.hist_timeGraph.ymax = self._tags[cols[0]]["ymax"]   
            self._hGraph.ids.hist_timeGraph.xmax = len(data)
            self._hGraph.ids.hist_timeGraph.update_x_labels([x for x in data_timeList])
            
        except Exception as e:
            print("Erro: ", e.args)
                
            
    def parseDTString(self, datetime_str):
        """
        Método que converte a string inserida pelo usuário para o formato
        utilizado na busca dos dados no BD
        """
        try:
            d = datetime.strptime(datetime_str, '%d/%m/%Y %H:%M:%S')
            return d
        except Exception as e:
            print("Erro: ",e.args)
            
    def validateDate(self, dateString): 
        try:
            format = "%d/%m/%Y %H:%M:%S"
            result = datetime.strptime(dateString, format)

            return True
        except ValueError:
            return False
