from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.modalview import ModalView
from kivy.core.window import Window
from kivy.properties import StringProperty
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivy.uix.scrollview import ScrollView
from datetime import datetime
import json
import os
import uuid

# --------------------------
# Cores
# --------------------------
BG = "#f0f4f8"
FG_LABEL = "#000000"
BTN_PRIMARY = "#0078d7"
BTN_EDIT = "#00aaff"
BTN_DELETE = "#d9534f"
BTN_CALC = "#28a745"
BTN_STORE = "#6f42c1"
RESULT_BG = "#e0f0ff"

# --------------------------
# Constantes
# --------------------------
ARQUIVO_DADOS = "planadores.json"
ARQUIVO_MEDICOES = "medicoes.json"


class MedicaoStore:
    """Gerencia o histórico de medições salvas (resultados + comentário + data)"""
    def __init__(self, arquivo=ARQUIVO_MEDICOES):
        self.arquivo = arquivo
        self.medicoes = []
        self.carregar()
    
    def carregar(self):
        """Carrega as medições do arquivo JSON, se existir"""
        if os.path.exists(self.arquivo):
            try:
                with open(self.arquivo, "r", encoding='utf-8') as f:
                    self.medicoes = json.load(f)
            except Exception as e:
                print(f"Erro ao carregar medições: {e}")
                self.medicoes = []
        else:
            self.medicoes = []
        
        # Garante que registros antigos (salvos antes do recurso de exclusão) ganhem um id
        precisa_salvar = False
        for registro in self.medicoes:
            if "id" not in registro:
                registro["id"] = str(uuid.uuid4())
                precisa_salvar = True
        if precisa_salvar:
            self._persistir()
    
    def _persistir(self):
        """Escreve a lista atual de medições no arquivo"""
        try:
            with open(self.arquivo, "w", encoding='utf-8') as f:
                json.dump(self.medicoes, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao salvar medições: {e}")
            return False
    
    def salvar_medicao(self, registro):
        """Adiciona um novo registro de medição e persiste no arquivo"""
        registro["id"] = str(uuid.uuid4())
        self.medicoes.append(registro)
        sucesso = self._persistir()
        if sucesso:
            print(f"Medição salva em {self.arquivo}")
        else:
            self.medicoes.pop()
        return sucesso
    
    def excluir_medicao(self, id_medicao):
        """Remove uma medição pelo id e persiste a alteração"""
        registro = next((m for m in self.medicoes if m.get("id") == id_medicao), None)
        if registro is None:
            return False
        self.medicoes.remove(registro)
        sucesso = self._persistir()
        if not sucesso:
            self.medicoes.append(registro)
        return sucesso


class PlanadorManager:
    def __init__(self):
        self.planadores = {}
        self.valores_carregados = {"x": 1, "c": 2, "x_1_4": 3, "PN": 4}
        self.carregar_dados()
    
    def carregar_dados(self):
        """Carrega os planadores do arquivo JSON, cria arquivo com dados padrão se não existir"""
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, "r", encoding='utf-8') as f:
                    self.planadores = json.load(f)
                print(f"Dados carregados de {ARQUIVO_DADOS}")
            except Exception as e:
                print(f"Erro ao carregar dados: {e}")
                self.criar_arquivo_padrao()
        else:
            self.criar_arquivo_padrao()
    
    def criar_arquivo_padrao(self):
        """Cria arquivo com planadores padrão"""
        self.planadores = {
            "Enigma": {"x": 1.0, "c": 1.0, "x_1_4": 1.0, "PN": 1.0},
            "Explorer": {"x": 1.0, "c": 1.0, "x_1_4": 1.0, "PN": 1.0},
            "MNOS 20": {"x": 1.0, "c": 1.0, "x_1_4": 1.0, "PN": 1.0},
            "Tera": {"x": 1.0, "c": 1.0, "x_1_4": 1.0, "PN": 1.0}
        }
        self.salvar_dados()
        print(f"Arquivo {ARQUIVO_DADOS} criado com dados padrão")
    
    def salvar_dados(self):
        """Salva os planadores no arquivo JSON"""
        try:
            with open(ARQUIVO_DADOS, "w", encoding='utf-8') as f:
                json.dump(self.planadores, f, indent=4, ensure_ascii=False)
            print(f"Dados salvos em {ARQUIVO_DADOS}")
            return True
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            return False
    
    def carregar_valores(self, nome):
        """Carrega valores de um planador específico"""
        if nome in self.planadores:
            self.valores_carregados = self.planadores[nome].copy()
            return f"Carregado: {nome}"
        return "Selecione um planador válido."
    
    def editar_planador(self, nome_antigo, novo_nome, novos_dados):
        """Edita um planador existente"""
        if nome_antigo in self.planadores:
            # Remove o antigo e adiciona o novo
            del self.planadores[nome_antigo]
            self.planadores[novo_nome] = novos_dados
            return self.salvar_dados()
        return False
    
    def criar_planador(self, nome, dados):
        """Cria um novo planador"""
        if nome not in self.planadores:
            self.planadores[nome] = dados
            return self.salvar_dados()
        return False
    
    def deletar_planador(self, nome):
        """Deleta um planador"""
        if nome in self.planadores:
            del self.planadores[nome]
            return self.salvar_dados()
        return False
    
    def get_lista_planadores(self):
        """Retorna lista de nomes dos planadores"""
        return list(self.planadores.keys())


class EditarPlanadorPopup(ModalView):
    def __init__(self, manager, nome_planador, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.nome_antigo = nome_planador
        self.app_ref = app_ref
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))   
        
        # Nome do planador
        layout.add_widget(Label(
            text="Nome do Planador:",
            size_hint_y=None,
            height=dp(25),
            color=(1, 1, 1, 1),
            font_size='14sp'
        ))
        self.entry_nome = TextInput(
            text=self.nome_antigo,
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            foreground_color=(0, 0, 0, 1),
            font_size='14sp'
        )
        layout.add_widget(self.entry_nome)
        
        # Campos de dados
        dados = self.manager.planadores[self.nome_antigo]
        self.entries = {}
        labels = ["x", "c", "x[sub]1/4[/sub]", "PN"]
        chaves = ["x", "c", "x_1_4", "PN"]
        
        for lbl, chave in zip(labels, chaves):
            layout.add_widget(Label(
                text=lbl,
                markup=True,     
                font_size='14sp',                
                size_hint_y=None,
                height=dp(25),
                color=(1, 1, 1, 1)
            ))
            entry = TextInput(
                text=str(dados[chave]),
                multiline=False,
                size_hint_y=None,
                height=dp(40),
                foreground_color=(0, 0, 0, 1),
                font_size='14sp'
            )
            layout.add_widget(entry)
            self.entries[chave] = entry
            
        layout.add_widget(Widget(size_hint_y=1))
        
        # Botões
        btn_layout = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(50))
        
        btn_salvar = Button(
            text="Salvar",
            background_color=tuple(int(BTN_PRIMARY[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        btn_salvar.bind(on_press=self.salvar)
        
        btn_cancelar = Button(
            text="Cancelar",
            background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        btn_cancelar.bind(on_press=lambda x: self.dismiss())
        
        btn_layout.add_widget(btn_salvar)
        btn_layout.add_widget(btn_cancelar)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def salvar(self, instance):
        try:
            novo_nome = self.entry_nome.text.strip()
            if not novo_nome:
                self.app_ref.status_text = "Nome inválido."
                return
            
            # Verifica se o novo nome já existe (exceto se for o mesmo)
            if novo_nome != self.nome_antigo and novo_nome in self.manager.planadores:
                self.app_ref.status_text = f"Já existe um planador com o nome '{novo_nome}'."
                return
            
            novos_dados = {}
            for chave, entry in self.entries.items():
                novos_dados[chave] = float(entry.text)
            
            success = self.manager.editar_planador(self.nome_antigo, novo_nome, novos_dados)
            if success:
                self.app_ref.atualizar_spinner()
                self.app_ref.spinner.text = novo_nome
                self.app_ref.status_text = f"Atualizado: {novo_nome}"
                self.dismiss()
            else:
                self.app_ref.status_text = "Erro ao salvar no arquivo."
        except ValueError:
            self.app_ref.status_text = "Erro: valores devem ser numéricos."


class CriarPlanadorPopup(ModalView):
    def __init__(self, manager, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.manager = manager
        self.app_ref = app_ref
        self.size_hint = (0.9, 0.8)
        self.auto_dismiss = False
        
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        # Nome do planador
        layout.add_widget(Label(
            text="Nome do Planador:",
            size_hint_y=None,
            height=dp(25),
            color=(1, 1, 1, 1),
            font_size='14sp'
        ))
        self.entry_nome = TextInput(
            text="",
            multiline=False,
            size_hint_y=None,
            height=dp(40),
            foreground_color=(0, 0, 0, 1),
            font_size='14sp',
            padding=[dp(8), dp(8)]
        )
        layout.add_widget(self.entry_nome)
        
        # Campos de dados
        self.entries = {}
        labels = ["x", "c", "x[sub]1/4[/sub]", "PN"]
        chaves = ["x", "c", "x_1_4", "PN"]
        
        for lbl, chave in zip(labels, chaves):
            layout.add_widget(Label(
                text=lbl,
                markup=True,
                font_size='14sp',
                size_hint_y=None,
                height=dp(25),
                color=(1, 1, 1, 1)
            ))
            entry = TextInput(
                text="",  
                multiline=False,
                size_hint_y=None,
                height=dp(40),
                foreground_color=(0, 0, 0, 1),
                font_size='14sp',
                padding=[dp(8), dp(8)]
            )
            layout.add_widget(entry)
            self.entries[chave] = entry
        
        # Espaço flexível no final
        layout.add_widget(Widget(size_hint_y=1))
        
        # Botões
        btn_layout = BoxLayout(spacing=dp(8), size_hint_y=None, height=dp(50))
        
        btn_criar = Button(
            text="Criar",
            background_color=tuple(int(BTN_PRIMARY[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        btn_criar.bind(on_press=self.criar_planador)
        
        btn_cancelar = Button(
            text="Cancelar",
            background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='14sp'
        )
        btn_cancelar.bind(on_press=lambda x: self.dismiss())
        
        btn_layout.add_widget(btn_criar)
        btn_layout.add_widget(btn_cancelar)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
    
    def criar_planador(self, instance):
        try:
            nome_novo = self.entry_nome.text.strip()
            if not nome_novo:
                self.app_ref.status_text = "Nome inválido."
                return
            
            if nome_novo in self.manager.planadores:
                self.app_ref.status_text = f"Já existe um planador com o nome '{nome_novo}'."
                return
            
            dados = {}
            for chave, entry in self.entries.items():
                dados[chave] = float(entry.text)
            
            success = self.manager.criar_planador(nome_novo, dados)
            if success:
                self.app_ref.atualizar_spinner()
                self.app_ref.spinner.text = nome_novo
                self.app_ref.status_text = f"Criado: {nome_novo}"
                self.dismiss()
            else:
                self.app_ref.status_text = "Erro ao salvar no arquivo."
        except ValueError:
            self.app_ref.status_text = "Erro: valores devem ser numéricos."


class HistoricoPopup(ModalView):
    """Popup que mostra o histórico de medições armazenadas, filtrado por planador"""
    def __init__(self, medicao_store, manager, **kwargs):
        super().__init__(**kwargs)
        self.medicao_store = medicao_store
        self.manager = manager
        self.size_hint = (0.92, 0.85)
        self.auto_dismiss = False
        
        self.build_ui()
    
    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        
        # Fundo branco para a popup toda (facilita leitura)
        with layout.canvas.before:
            Color(1, 1, 1, 1)
            self.bg_rect = Rectangle(pos=layout.pos, size=layout.size)
        layout.bind(pos=self._update_bg, size=self._update_bg)
        
        # Título
        layout.add_widget(Label(
            text="[b]Histórico de Medições[/b]",
            markup=True,
            size_hint_y=None,
            height=dp(30),
            color=(0, 0, 0, 1),
            font_size='16sp'
        ))
        
        # Spinner de seleção do planador
        layout.add_widget(Label(
            text="Selecione o planador:",
            size_hint_y=None,
            height=dp(22),
            color=(0, 0, 0, 1),
            font_size='13sp'
        ))
        
        nomes_com_medicoes = sorted({m.get("planador", "") for m in self.medicao_store.medicoes})
        self.spinner_hist = Spinner(
            text='Selecione um planador',
            values=nomes_com_medicoes if nomes_com_medicoes else self.manager.get_lista_planadores(),
            size_hint_y=None,
            height=dp(40),
            color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            font_size='14sp'
        )
        self.spinner_hist.bind(text=self.on_selecionar_planador)
        layout.add_widget(self.spinner_hist)
        
        # Área rolável com as medições
        self.scroll = ScrollView(size_hint=(1, 1))
        self.lista_layout = GridLayout(cols=1, spacing=dp(8), size_hint_y=None, padding=(0, dp(5)))
        self.lista_layout.bind(minimum_height=self.lista_layout.setter('height'))
        self.scroll.add_widget(self.lista_layout)
        layout.add_widget(self.scroll)
        
        self._mostrar_mensagem("Selecione um planador para ver as medições.")
        
        # Botão fechar
        btn_fechar = Button(
            text="Fechar",
            background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45),
            font_size='14sp'
        )
        btn_fechar.bind(on_press=lambda x: self.dismiss())
        layout.add_widget(btn_fechar)
        
        self.add_widget(layout)
    
    def _update_bg(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size
    
    def _mostrar_mensagem(self, texto):
        self.lista_layout.clear_widgets()
        lbl = Label(
            text=texto,
            color=(0.3, 0.3, 0.3, 1),
            font_size='13sp',
            size_hint_y=None,
            height=dp(40)
        )
        self.lista_layout.add_widget(lbl)
    
    def on_selecionar_planador(self, spinner, texto):
        if not texto or texto == 'Selecione um planador':
            self._mostrar_mensagem("Selecione um planador para ver as medições.")
            return
        
        registros = [m for m in self.medicao_store.medicoes if m.get("planador") == texto]
        
        self.lista_layout.clear_widgets()
        
        if not registros:
            self._mostrar_mensagem(f"Nenhuma medição armazenada para '{texto}'.")
            return
        
        # Mais recentes primeiro
        registros = list(reversed(registros))
        
        for reg in registros:
            comentario = reg.get("comentario", "").strip()
            texto_comentario = comentario if comentario else "-"
            
            card_text = (
                f"[b]{reg.get('data', '-')}[/b]\n"
                f"P[sub]frente[/sub]: {reg.get('P_frente', 0):.1f}   "
                f"P[sub]tras[/sub]: {reg.get('P_tras', 0):.1f}   "
                f"L: {reg.get('L', 0):.1f}\n"
                f"P[sub]total[/sub]: {reg.get('P_total', 0):.1f}   "
                f"x[sub]cg[/sub]: {reg.get('xcg', 0):.1f}   "
                f"x_bar[sub]cg[/sub]: {reg.get('xcg_bar', 0):.1f}\n"
                f"CMA %: {reg.get('cma_pct', 0):.2f}   SM: {reg.get('SM', 0):.1f}\n"
                f"Comentário: {texto_comentario}"
            )
            
            card = BoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                padding=dp(8),
                spacing=dp(8)
            )
            with card.canvas.before:
                Color(*tuple(int(RESULT_BG[i:i+2], 16)/255 for i in (1, 3, 5)))
                rect = Rectangle(pos=card.pos, size=card.size)
            def _upd(instance, value, rect=rect):
                rect.pos = instance.pos
                rect.size = instance.size
            card.bind(pos=_upd, size=_upd)
            
            largura_conteudo = self.lista_layout.width * 0.8 - dp(16)
            card_label = Label(
                text=card_text,
                markup=True,
                halign='left',
                valign='top',
                color=(0, 0, 0, 1),
                font_size='12sp',
                size_hint_y=None,
                size_hint_x=0.8,
                text_size=(largura_conteudo, None)
            )
            def _ajustar_altura(instance, value, card=card):
                card.height = value[1] + dp(16)
            card_label.bind(texture_size=_ajustar_altura)
            
            btn_excluir = Button(
                text="Excluir",
                size_hint_x=0.2,
                size_hint_y=1,
                background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
                color=(1, 1, 1, 1),
                font_size='12sp'
            )
            btn_excluir.bind(on_press=lambda inst, reg=reg: self.confirmar_exclusao(reg, texto))
            
            card.add_widget(card_label)
            card.add_widget(btn_excluir)
            self.lista_layout.add_widget(card)
    
    def confirmar_exclusao(self, registro, planador_atual):
        """Mostra uma confirmação antes de excluir a medição definitivamente"""
        from kivy.uix.popup import Popup
        
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(
            text=f"Excluir a medição de {registro.get('data', '-')}?",
            color=(0, 0, 0, 1),
            font_size='14sp'
        ))
        
        btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
        
        btn_sim = Button(
            text="Sim",
            background_color=tuple(int(BTN_PRIMARY[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='13sp'
        )
        btn_nao = Button(
            text="Não",
            background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='13sp'
        )
        
        btn_layout.add_widget(btn_sim)
        btn_layout.add_widget(btn_nao)
        content.add_widget(btn_layout)
        
        popup = Popup(
            title="Confirmar Exclusão",
            content=content,
            size_hint=(0.8, 0.3),
            title_color=(0, 0, 0, 1),
            title_size='14sp'
        )
        
        def _excluir(instance):
            self.medicao_store.excluir_medicao(registro.get("id"))
            popup.dismiss()
            self.on_selecionar_planador(self.spinner_hist, planador_atual)
        
        btn_sim.bind(on_press=_excluir)
        btn_nao.bind(on_press=lambda x: popup.dismiss())
        popup.open()


class PlanadorApp(App):
    status_text = StringProperty("")
    resultado_text = StringProperty("")
    
    def build(self):
        Window.clearcolor = tuple(int(BG[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,)
        
        self.manager = PlanadorManager()
        self.medicao_store = MedicaoStore()
        self.ultimo_resultado = None
        
        # Layout principal
        self.root_layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        
        # 1. Título (altura fixa)
        title_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(35))
        title = Label(
            text="Cálculo de CG do Planador",
            font_size='16sp',
            bold=True,
            color=(0, 0, 0, 1)
        )
        title_layout.add_widget(title)
        self.root_layout.add_widget(title_layout)
        
        # 2. Spinner (altura fixa)
        spinner_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(45))
        self.spinner = Spinner(
            text='Selecione um planador',
            values=self.manager.get_lista_planadores(),
            size_hint_y=None,
            height=dp(40),
            color=(0, 0, 0, 1),
            background_color=(1, 1, 1, 1),
            font_size='14sp'
        )
        self.spinner.bind(text=self.on_spinner_select)
        spinner_layout.add_widget(self.spinner)
        self.root_layout.add_widget(spinner_layout)
        
        # 3. Botões de controle (altura fixa)
        btn_layout = GridLayout(cols=4, spacing=dp(5), size_hint_y=None, height=dp(45))
        
        btn_editar = Button(
            text="Editar",
            background_color=tuple(int(BTN_EDIT[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        btn_editar.bind(on_press=self.editar_planador)
        btn_layout.add_widget(btn_editar)
        
        btn_criar = Button(
            text="Criar Novo",
            background_color=tuple(int(BTN_PRIMARY[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        btn_criar.bind(on_press=self.criar_planador)
        btn_layout.add_widget(btn_criar)
        
        btn_deletar = Button(
            text="Deletar",
            background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        btn_deletar.bind(on_press=self.deletar_planador)
        btn_layout.add_widget(btn_deletar)
        
        btn_historico = Button(
            text="Histórico",
            background_color=tuple(int(BTN_STORE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            font_size='12sp'
        )
        btn_historico.bind(on_press=self.abrir_historico)
        btn_layout.add_widget(btn_historico)
        
        self.root_layout.add_widget(btn_layout)
        
        # 4. Status (altura fixa)
        status_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(30))
        self.status_label = Label(
            text=self.status_text,
            color=(0, 0, 0, 1),
            font_size='12sp'
        )
        status_layout.add_widget(self.status_label)
        self.root_layout.add_widget(status_layout)
        
        # 5. Campos de entrada (altura flexível com pesos)
        input_layout = BoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=0.25)
        
        campos = ["P_frente", "P_tras", "L"]
        self.entries = {}
        
        for campo in campos:
            if campo == "P_frente":
                texto = "P[sub]frente[/sub]:"
            elif campo == "P_tras":
                texto = "P[sub]tras[/sub]:"
            else:
                texto = "L:"

            row = BoxLayout(orientation='horizontal', spacing=dp(5))
            
            row.add_widget(Label(
                text=texto,
                markup=True,  
                font_size='18sp',
                size_hint_x=0.4,
                color=(0, 0, 0, 1)
            ))

            entry = TextInput(
                multiline=False,
                size_hint_x=0.6,
                foreground_color=(0, 0, 0, 1),
                font_size='14sp',
                padding=[dp(8), dp(8)]
            )
            row.add_widget(entry)
            self.entries[campo] = entry
            
            input_layout.add_widget(row)
        
        self.root_layout.add_widget(input_layout)
        
        # 6. Botões Calcular / Armazenar (altura fixa)
        calc_layout = BoxLayout(orientation='horizontal', spacing=dp(8), size_hint_y=None, height=dp(50))
        btn_calcular = Button(
            text="Calcular",
            background_color=tuple(int(BTN_CALC[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45),
            font_size='14sp'
        )
        btn_calcular.bind(on_press=self.calcular)
        calc_layout.add_widget(btn_calcular)
        
        self.btn_armazenar = Button(
            text="Armazenar",
            background_color=tuple(int(BTN_STORE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
            color=(1, 1, 1, 1),
            size_hint_y=None,
            height=dp(45),
            font_size='14sp',
            disabled=True
        )
        self.btn_armazenar.bind(on_press=self.armazenar_medicao)
        calc_layout.add_widget(self.btn_armazenar)
        
        self.root_layout.add_widget(calc_layout)
        
        # 7. Área de resultado (altura flexível - maior parte)
        result_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=0.4,
            padding=dp(10),
            spacing=dp(8)
        )
        
        # Fundo da área de resultado
        with result_layout.canvas.before:
            Color(*tuple(int(RESULT_BG[i:i+2], 16)/255 for i in (1, 3, 5)))
            self.rect = Rectangle(pos=result_layout.pos, size=result_layout.size)
        
        result_layout.bind(pos=self.update_rect, size=self.update_rect)
        
        # Label do resultado (altura ajustada ao conteúdo, não ocupa tudo)
        self.resultado_label = Label(
            text=self.resultado_text,
            markup=True,
            font_size='16sp',
            halign='center',
            valign='top',
            color=(0, 0, 0, 1),
            size_hint_y=None
        )
        
        # Configurar text_size para permitir quebra de linha e altura dinâmica
        def _ajustar_label(*args):
            self.resultado_label.text_size = (result_layout.width - dp(20), None)
        def _ajustar_altura(instance, value):
            instance.height = value[1]
        self.resultado_label.bind(texture_size=_ajustar_altura)
        result_layout.bind(size=_ajustar_label)
        
        result_layout.add_widget(self.resultado_label)
        
        # Comentário: ocupa o espaço livre restante da área de resultado,
        # e só fica visível/interativo depois que houver um resultado calculado
        self.comentario_wrapper = BoxLayout(
            orientation='vertical',
            size_hint_y=1,
            spacing=dp(3),
            opacity=0,
            disabled=True
        )
        self.comentario_wrapper.add_widget(Label(
            text="Comentário:",
            size_hint_y=None,
            height=dp(20),
            color=(0, 0, 0, 1),
            font_size='13sp',
            halign='left'
        ))
        self.comentario_entry = TextInput(
            text="",
            multiline=True,
            hint_text="Adicione uma observação sobre esta medição...",
            foreground_color=(0, 0, 0, 1),
            font_size='13sp',
            padding=[dp(8), dp(8)]
        )
        self.comentario_wrapper.add_widget(self.comentario_entry)
        result_layout.add_widget(self.comentario_wrapper)
        
        self.root_layout.add_widget(result_layout)
        
        # 8. Footer (altura fixa)
        footer_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=dp(25))
        info_label = Label(
            text=f"Dados salvos em: {ARQUIVO_DADOS}",
            font_size='10sp',
            color=(0.5, 0.5, 0.5, 1)
        )
        footer_layout.add_widget(info_label)
        self.root_layout.add_widget(footer_layout)
        
        return self.root_layout
    
    def update_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*tuple(int(RESULT_BG[i:i+2], 16)/255 for i in (1, 3, 5)))
            Rectangle(pos=instance.pos, size=instance.size)
    
    def on_spinner_select(self, spinner, text):
        """Carrega automaticamente os valores quando um planador é selecionado"""
        if text and text != 'Selecione um planador':
            self.status_text = self.manager.carregar_valores(text)
    
    def atualizar_spinner(self):
        """Atualiza a lista de planadores no spinner"""
        self.spinner.values = self.manager.get_lista_planadores()
        # Configurar dropdown após criar o Spinner
        if hasattr(self.spinner, 'dropdown'):
            self.spinner.dropdown.max_height = dp(200)
            # Configurar fonte das opções individualmente
            for item in self.spinner.dropdown.container.children:
                if isinstance(item, Label):
                    item.font_size = '14sp'
    
    def editar_planador(self, instance):
        if self.spinner.text and self.spinner.text != 'Selecione um planador':
            popup = EditarPlanadorPopup(self.manager, self.spinner.text, self)
            popup.open()
        else:
            self.status_text = "Selecione um planador antes de editar."
    
    def criar_planador(self, instance):
        popup = CriarPlanadorPopup(self.manager, self)
        popup.open()
    
    def abrir_historico(self, instance):
        popup = HistoricoPopup(self.medicao_store, self.manager)
        popup.open()
    
    def deletar_planador(self, instance):
        if self.spinner.text and self.spinner.text != 'Selecione um planador':
            from kivy.uix.popup import Popup
            from kivy.uix.boxlayout import BoxLayout
            
            content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
            content.add_widget(Label(
                text=f"Excluir o planador '{self.spinner.text}'?",
                color=(0, 0, 0, 1),
                font_size='14sp'
            ))
            
            btn_layout = BoxLayout(spacing=dp(10), size_hint_y=None, height=dp(40))
            
            btn_sim = Button(
                text="Sim",
                background_color=tuple(int(BTN_PRIMARY[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
                color=(1, 1, 1, 1),
                font_size='13sp'
            )
            btn_sim.bind(on_press=lambda x: self.confirmar_delecao(popup))
            
            btn_nao = Button(
                text="Não",
                background_color=tuple(int(BTN_DELETE[i:i+2], 16)/255 for i in (1, 3, 5)) + (1,),
                color=(1, 1, 1, 1),
                font_size='13sp'
            )
            btn_nao.bind(on_press=lambda x: popup.dismiss())
            
            btn_layout.add_widget(btn_sim)
            btn_layout.add_widget(btn_nao)
            content.add_widget(btn_layout)
            
            popup = Popup(
                title="Confirmar Exclusão",
                content=content,
                size_hint=(0.8, 0.3),
                title_color=(0, 0, 0, 1),
                title_size='14sp'
            )
            popup.open()
        else:
            self.status_text = "Selecione um planador para deletar."
    
    def confirmar_delecao(self, popup):
        nome_planador = self.spinner.text
        success = self.manager.deletar_planador(nome_planador)
        if success:
            self.atualizar_spinner()
            self.spinner.text = ""
            self.status_text = f"Planador '{nome_planador}' deletado."
        popup.dismiss()
    
    def calcular(self, instance):
        # Verificar se um planador foi selecionado
        if not self.spinner.text or self.spinner.text == 'Selecione um planador':
            self.resultado_text = "[b]Selecione um planador[/b]"
            self.comentario_wrapper.opacity = 0
            self.comentario_wrapper.disabled = True
            self.btn_armazenar.disabled = True
            self.ultimo_resultado = None
            return

        try:
            P_frente = float(self.entries["P_frente"].text) if self.entries["P_frente"].text else 0
            P_tras = float(self.entries["P_tras"].text) if self.entries["P_tras"].text else 0
            L = float(self.entries["L"].text) if self.entries["L"].text else 0
        
            x = self.manager.valores_carregados["x"]
            c = self.manager.valores_carregados["c"]
            x_1_4 = self.manager.valores_carregados["x_1_4"]
            PN = self.manager.valores_carregados["PN"]
            Dfix = 17
        
            xcg = (P_tras * L / (P_frente + P_tras)) + Dfix
            xcg_bar = xcg - x
            cma_pct = xcg_bar / c
            SM = xcg_bar - PN
            Ptot = P_frente + P_tras
            
            # Formatar resultados
            self.resultado_text = (
                f"[b]P[sub]total[/sub]:[/b] {Ptot:.1f}\n"
                f"[b]x[sub]cg[/sub]:[/b] {xcg:.1f}\n"
                f"[b]x_bar[sub]cg[/sub]:[/b] {xcg_bar:.1f}\n"
                f"[b]CMA %:[/b] {cma_pct:.2f}\n"
                f"[b]SM:[/b] {SM:.1f}"
            )
            self.comentario_wrapper.opacity = 1
            self.comentario_wrapper.disabled = False
            self.comentario_entry.text = ""
            self.btn_armazenar.disabled = False
            
            # Guarda os valores brutos deste cálculo para poder armazenar depois
            self.ultimo_resultado = {
                "planador": self.spinner.text,
                "P_frente": P_frente,
                "P_tras": P_tras,
                "L": L,
                "P_total": Ptot,
                "xcg": xcg,
                "xcg_bar": xcg_bar,
                "cma_pct": cma_pct,
                "SM": SM
            }
        
        except ValueError:
            self.resultado_text = "[color=ff0000]Erro: insira apenas números.[/color]"
            self.comentario_wrapper.opacity = 0
            self.comentario_wrapper.disabled = True
            self.btn_armazenar.disabled = True
            self.ultimo_resultado = None
        except ZeroDivisionError:
            self.resultado_text = "[color=ff0000]Erro: divisão por zero. Verifique os valores.[/color]"
            self.comentario_wrapper.opacity = 0
            self.comentario_wrapper.disabled = True
            self.btn_armazenar.disabled = True
            self.ultimo_resultado = None
    
    def armazenar_medicao(self, instance):
        """Salva o último resultado calculado, junto com o comentário e a data, no histórico"""
        if not self.ultimo_resultado:
            self.status_text = "Calcule uma medição antes de armazenar."
            return
        
        registro = dict(self.ultimo_resultado)
        registro["comentario"] = self.comentario_entry.text.strip()
        registro["data"] = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        sucesso = self.medicao_store.salvar_medicao(registro)
        if sucesso:
            self.status_text = f"Medição armazenada em {ARQUIVO_MEDICOES}."
        else:
            self.status_text = "Erro ao armazenar a medição no arquivo."
    
    def on_status_text(self, instance, value):
        self.status_label.text = value
    
    def on_resultado_text(self, instance, value):
        self.resultado_label.text = value
    
    def on_stop(self):
        """Executado quando o app é fechado"""
        print("Aplicativo fechado. Dados persistidos.")
        print(f"Total de planadores: {len(self.manager.planadores)}")


if __name__ == '__main__':
    PlanadorApp().run()