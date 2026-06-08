import os
import json
import sys
import random
from pathlib import Path
from ordenacao.ordenacao import (
    quicksort,
    radix_sort_por_ano, 
    heapsort,
    registrarAvaliacao,
    incrementar_emprestimo,
    _garantir_campos_metricas,
)
import qdarktheme
from datetime import datetime
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QPixmap, QColor, QCursor
from PySide6.QtWidgets import (
    QMainWindow, QCalendarWidget, QVBoxLayout,
    QGridLayout, QFormLayout, QWidget, QFrame,
    QApplication, QPushButton, QLabel, QDialog,
    QLineEdit, QComboBox, QSpinBox, QDateEdit, QListWidget,
    QDialogButtonBox, QMessageBox, QSplitter,
    QStackedWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QAbstractItemView, QDoubleSpinBox, QMenu
)

CAMINHO_DB_FILES = Path(__file__).parent / "db_files"
IDS_ALUNOS = os.path.join(CAMINHO_DB_FILES, "id_alunos.json")
INFO_ALUNOS = os.path.join(CAMINHO_DB_FILES, "info_alunos.json")
IDS_LIVROS = os.path.join(CAMINHO_DB_FILES, "id_livros.json")
INFO_LIVROS = os.path.join(CAMINHO_DB_FILES, "info_livros.json")
EMPRESTIMOS = os.path.join(CAMINHO_DB_FILES, "emprestimos.json")
ID_EMPRESTIMO = os.path.join(CAMINHO_DB_FILES, "id_emprestimo.json")
HISTORICO_DEVOLUCOES = os.path.join(CAMINHO_DB_FILES, "historico_devolucoes.json")

class Aluno:
    def __init__(self, id, nome, idade, serie, turno, contato, endereco):
        self.id = id
        self.nome = nome.title()
        self.idade = idade
        self.serie = serie
        self.turno = turno.title()
        self.contato = contato
        self.endereco = endereco.title()

class Livro:
    def __init__(
        self, numeracao, titulo, genero, autor, editora, quantidade,
        ano: int = 0,
        nota_media: float = 0.0,
        total_avaliacoes: int = 0,
        contagem_emprestimos: int = 0,
    ):
        self.numeracao = numeracao
        self.titulo = titulo.capitalize()
        self.genero = genero.capitalize()
        self.autor = autor.capitalize()
        self.editora = editora.capitalize()
        self.quantidade = quantidade
        self.ano = ano
        self.nota_media = nota_media
        self.total_avaliacoes = total_avaliacoes
        self.contagem_emprestimos = contagem_emprestimos

class Biblioteca:
    def __init__(self):
        self.id_alunos = self.importacao(IDS_ALUNOS)
        self.info_alunos = self.importacao(INFO_ALUNOS)
        self.id_livros = self.importacao(IDS_LIVROS)
        self.info_livros = self.importacao(INFO_LIVROS)
        self.emprestimos = self.importacao(EMPRESTIMOS)
        self.id_emprestimo = self.importacao(ID_EMPRESTIMO)
        self.historico_devolucoes = self.importacao(HISTORICO_DEVOLUCOES)

        self._atribuir_notas_iniciais()
        
        self.bst = None
        self.rbt_intervalos = None
        self.indice_invertido = None
        self.buscador_fuzzy = None
        self.motor = None
        
        self.inicializar_indices()

    def importacao(self, caminho: str):
        with open(caminho, "r", encoding="utf-8-sig") as arq:
            return json.load(arq)

    def exportacao(self, caminho: str, dados: dict):
        with open(caminho, "w", encoding="utf-8") as arq:
            json.dump(dados, arq, ensure_ascii=False, indent=2)

    def _atribuir_notas_iniciais(self):
        """Gera nota média inicial para livros sem avaliações existentes."""
        mudou = False

        for livro in self.info_livros.values():
            if not isinstance(livro, dict):
                continue

            nota_media = livro.get("nota_media", 0.0)
            total_avaliacoes = livro.get("total_avaliacoes", 0)

            livro.setdefault("nota_media", 0.0)
            livro.setdefault("total_avaliacoes", 0)
            livro.setdefault("contagem_emprestimos", 0)

            if total_avaliacoes == 0 and (not isinstance(nota_media, (int, float)) or nota_media <= 0.0):
                nota_aleatoria = round(random.uniform(0.0, 5.0), 1)
                livro["nota_media"] = nota_aleatoria
                livro["total_avaliacoes"] = 1
                mudou = True

        if mudou:
            self.exportacao(INFO_LIVROS, self.info_livros)

    def inicializar_indices(self):
        from indices.rbt_livros import RBTBiblioteca 
        from indices.rbt_intervalos import RBTIntervalos
        from indices.bst_livros import BSTBiblioteca
        from indices.indice_invertido import IndiceInvertido
        from indices.busca_aproximada import BuscaAproximada
        from indices.motor_busca import MotorBusca

        livros_lista = list(self.info_livros.values())

        self.bst = RBTBiblioteca()
        
        self.bst.construir_de_lista(livros_lista)
        print(f"[RBT-Livros] {len(livros_lista)} livros indexados.")
        
        self.rbt_intervalos = RBTIntervalos()
        self.rbt_intervalos.construir_de_emprestimos(self.emprestimos)
        print(f"[RBT-Intervalos] Árvore de conflito de datas pronta.")

        self.indice_invertido = IndiceInvertido()
        self.indice_invertido.construir(livros_lista)
        print(f"[Invertido] {len(self.indice_invertido.vocabulario())} tokens.")

        self.buscador_fuzzy = BuscaAproximada(self.indice_invertido)
        print("[Fuzzy] Pronto.")

        self.motor = MotorBusca(self)
        print("[Motor] Todos os indices inicializados.")

    def cadastra_aluno(self, nome, idade, serie, turno, contato, endereco):
        _id = str(len(self.id_alunos))
        if _id in self.id_alunos:
            return False
        aluno = Aluno(_id, nome, idade, serie, turno, contato, endereco)
        self.id_alunos.append(_id)
        self.info_alunos[_id] = aluno.__dict__
        self.exportacao(IDS_ALUNOS, self.id_alunos)
        self.exportacao(INFO_ALUNOS, self.info_alunos)
        return self.info_alunos[_id]

    def cadastra_livro(self, numeracao, titulo, genero, autor, editora, qtd):
        livro = Livro(numeracao, titulo, genero, autor, editora, int(qtd) if isinstance(qtd, str) else qtd)
        if livro.total_avaliacoes == 0 and livro.nota_media <= 0.0:
            livro.nota_media = round(random.uniform(0.0, 5.0), 1)
            livro.total_avaliacoes = 1
        self.info_livros[numeracao] = livro.__dict__
        self.id_livros.append(numeracao)
        self.exportacao(IDS_LIVROS, self.id_livros)
        self.exportacao(INFO_LIVROS, self.info_livros)
        if self.bst:
            self.bst.inserir(self.info_livros[numeracao])
        if self.indice_invertido:
            self.indice_invertido.atualizar(self.info_livros[numeracao])
        return self.info_livros[numeracao]

    def altera_aluno(self, _id, nome, idade, serie, turno, contato, endereco):
        if _id not in self.id_alunos:
            return None
        aluno = Aluno(_id, nome, idade, serie, turno, contato, endereco)
        self.info_alunos[_id] = aluno.__dict__
        self.exportacao(INFO_ALUNOS, self.info_alunos)
        return self.info_alunos[_id]

    def altera_livro(self, numeracao, titulo, genero, autor, editora, qtd):
        if numeracao not in self.id_livros:
            return None
        livro_existente = self.info_livros.get(numeracao, {})
        livro = Livro(
            numeracao,
            titulo,
            genero,
            autor,
            editora,
            int(qtd) if isinstance(qtd, str) else qtd,
            nota_media=livro_existente.get("nota_media", 0.0),
            total_avaliacoes=livro_existente.get("total_avaliacoes", 0),
            contagem_emprestimos=livro_existente.get("contagem_emprestimos", 0),
        )
        self.info_livros[numeracao] = livro.__dict__
        self.exportacao(INFO_LIVROS, self.info_livros)
        if self.bst:
            self.bst.inserir(self.info_livros[numeracao])
        if self.indice_invertido:
            self.indice_invertido.atualizar(self.info_livros[numeracao])
        return self.info_livros[numeracao]

    def fazer_emprestimo(self, _id, livro, devo, inicio=None):
        from datetime import date as _date

        data_inicio = _date.fromisoformat(inicio) if inicio else _date.today()
        data_fim = _date.fromisoformat(devo)

        if data_fim < data_inicio:
            raise ValueError(
                "A data de devolução não pode ser anterior à data de início."
            )

        if self.rbt_intervalos:
            todos, _, _ = self.rbt_intervalos.buscar_todos_sobrepostos(data_inicio, data_fim)
            aluno_info_novo = self.info_alunos.get(_id, {})
            nome_novo = aluno_info_novo.get("nome", _id) if isinstance(aluno_info_novo, dict) else str(aluno_info_novo)
            for emp in todos:
                aluno_emp = emp.get("aluno", {})
                id_emp = aluno_emp.get("id") if isinstance(aluno_emp, dict) else None
                if id_emp == _id:
                    livro_emp = emp.get("livro", "?")
                    dev_emp   = emp.get("devolucao", "?")
                    raise ValueError(
                        f"O aluno '{nome_novo}' já possui o livro '{livro_emp}' "
                        f"emprestado até {dev_emp} neste período."
                    )

            titulo_normalizado = livro.strip().lower()
            qtd_exemplares = 0
            for dados in self.info_livros.values():
                if isinstance(dados, dict) and dados.get("titulo", "").lower() == titulo_normalizado:
                    qtd_exemplares = int(dados.get("quantidade", 1))
                    break
            if qtd_exemplares == 0:
                qtd_exemplares = 1  

            emprestimos_do_livro = [
                emp for emp in todos
                if emp.get("livro", "").lower() == titulo_normalizado
            ]
            if len(emprestimos_do_livro) >= qtd_exemplares:
                conflito = emprestimos_do_livro[0]
                dev_conf = conflito.get("devolucao", "?")
                raise ValueError(
                    f"Todos os {qtd_exemplares} exemplar(es) de '{livro.title()}' "
                    f"estão emprestados neste período (devolução mais próxima: {dev_conf})."
                )

        chave = str(datetime.now().microsecond)
        self.emprestimos[chave] = {
            "aluno": self.info_alunos[_id],
            "livro": livro.title(),
            "inicio": str(data_inicio),
            "devolucao": devo,
        }
        self.id_emprestimo[chave] = _id
        self.exportacao(EMPRESTIMOS, self.emprestimos)
        self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)
        
        if self.rbt_intervalos:
            dados_intervalo = dict(self.emprestimos[chave])
            dados_intervalo["chave"] = chave
            self.rbt_intervalos.inserir(data_inicio, data_fim, dados_intervalo)

        for numeracao, dados in self.info_livros.items():
                if isinstance(dados, dict) and dados.get("titulo", "").lower() == str(livro).lower():
                    incrementar_emprestimo(self.info_livros, numeracao)
                    self.exportacao(INFO_LIVROS, self.info_livros)
                    break

        return chave, self.emprestimos[chave]

    def fazer_devolucao(self, chave):
            emprestimo = self.emprestimos.get(chave)
            if not emprestimo:
                return

            aluno_info = emprestimo.get("aluno", {})
            if isinstance(aluno_info, dict):
                nome_aluno = aluno_info.get("nome", "Desconhecido")
            else:
                nome_aluno = str(aluno_info)

            chave_devolucao = f"DEV-{chave}"
            self.historico_devolucoes[chave_devolucao] = {
                "chave_emprestimo": chave,
                "livro": emprestimo.get("livro", ""),
                "aluno": nome_aluno,
                "data_devolucao": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            self.exportacao(HISTORICO_DEVOLUCOES, self.historico_devolucoes)

            self.emprestimos.pop(chave)
            self.id_emprestimo.pop(chave)
            self.exportacao(EMPRESTIMOS, self.emprestimos)
            self.exportacao(ID_EMPRESTIMO, self.id_emprestimo)

            if self.rbt_intervalos:
                self.rbt_intervalos.remover_por_chave(chave)

    def avaliar_livro(self, livro_id: str, nota: float) -> dict | None:
            resultado = registrarAvaliacao(self.info_livros, livro_id, nota)
            if resultado:
                self.exportacao(INFO_LIVROS, self.info_livros)
            return resultado

    def listar_livros_alfabetico(self, reverso: bool = False) -> list:
            return ordenar_por_titulo(self.info_livros, reverso=reverso)

    def listar_livros_por_ano(self, reverso: bool = False) -> list:
            return radix_sort_por_ano(list(self.info_livros.values()), reverso=reverso)
 
class JanelaPrincipal(QMainWindow):

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Sistema de Biblioteca")
        
        self.b1 = Biblioteca()
        
        self.ordenacao_coluna = None  
        self.ordenacao_reverso = False  
        
        self.janelaCA = JanelaCadastraAluno(self.b1)
        self.janelaCL = JanelaCadastroLivro(self.b1)
        self.janelaAA = JanelaAteraAluno(self.b1)
        self.janelaAL = JanelaAlteraLivro(self.b1)
        self.janelaEP = JanelaEmprestimo(self.b1)
        self.janelaDV = JanelaDevolucao(self.b1)
        
        self.splitter = QSplitter(Qt.Horizontal)
        
        self.sidebar = self._criar_sidebar()
        
        self.stacked = QStackedWidget()
        self.painel_acervo = self._criar_painel_acervo()
        self.painel_alunos = self._criar_painel_alunos()
        self.painel_emprestimos = self._criar_painel_emprestimos()
        self.painel_devolucoes = self._criar_painel_devolucoes()

        self.painel_relatorio = PainelRelatorio(self.b1)

        self.stacked.addWidget(self.painel_acervo)        
        self.stacked.addWidget(self.painel_alunos)        
        self.stacked.addWidget(self.painel_emprestimos)  
        self.stacked.addWidget(self.painel_devolucoes)    
        self.stacked.addWidget(self.painel_relatorio)

        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.stacked)
        self.splitter.setSizes([220, 1280])
        
        self.setCentralWidget(self.splitter)
        self.config_style()
        self._conectar_atualizacao_dialogos()
        self._atualizar_tabela_acervo()
        self._atualizar_tabela_alunos()
        self._atualizar_tabela_emprestimos()
        self._atualizar_cards()
    
    def _criar_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        logo_label = QLabel()
        pixmap = QPixmap("img/logo.png")
        pixmap = pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)
        
        separador1 = QFrame()
        separador1.setFrameShape(QFrame.HLine)
        separador1.setStyleSheet("background: rgba(173, 73, 225, 0.2);")
        layout.addWidget(separador1)
        
        secao_acervo = QLabel("ACERVO")
        secao_acervo.setObjectName("section-label")
        secao_acervo.setStyleSheet(
            "color: rgba(173, 73, 225, 0.45); font-size: 10px; "
            "letter-spacing: 2px; padding: 12px 16px 4px; font-weight: bold;"
        )
        layout.addWidget(secao_acervo)
        
        self.btn_acervo = self._criar_botao_nav("📚 Acervo de Livros", True)
        self.btn_acervo.clicked.connect(lambda: self._switch_panel(0, self.btn_acervo))
        layout.addWidget(self.btn_acervo)
        
        self.btn_alunos = self._criar_botao_nav("👥 Alunos")
        self.btn_alunos.clicked.connect(lambda: self._switch_panel(1, self.btn_alunos))
        layout.addWidget(self.btn_alunos)
        
        self.btn_emprestimos = self._criar_botao_nav("📤 Empréstimos")
        self.btn_emprestimos.clicked.connect(lambda: self._switch_panel(2, self.btn_emprestimos))
        layout.addWidget(self.btn_emprestimos)
        
        self.btn_devolucoes = self._criar_botao_nav("📥 Devoluções")
        self.btn_devolucoes.clicked.connect(lambda: self._switch_panel(3, self.btn_devolucoes))
        layout.addWidget(self.btn_devolucoes)
        
        self.btn_relatorio = self._criar_botao_nav("📊 Relatório")
        self.btn_relatorio.clicked.connect(lambda: self._switch_panel(4, self.btn_relatorio))
        layout.addWidget(self.btn_relatorio)

        self.nav_buttons = [self.btn_acervo, self.btn_alunos, self.btn_emprestimos, self.btn_devolucoes, self.btn_relatorio]
        
        separador2 = QFrame()
        separador2.setFrameShape(QFrame.HLine)
        separador2.setStyleSheet("background: rgba(173, 73, 225, 0.2); margin: 8px 0;")
        layout.addWidget(separador2)
        
        secao_cadastro = QLabel("CADASTRO")
        secao_cadastro.setObjectName("section-label")
        secao_cadastro.setStyleSheet(
            "color: rgba(173, 73, 225, 0.45); font-size: 10px; "
            "letter-spacing: 2px; padding: 12px 16px 4px; font-weight: bold;"
        )
        layout.addWidget(secao_cadastro)
        
        btn_novo_livro = self._criar_botao_nav("➕ Novo Livro")
        btn_novo_livro.clicked.connect(self.janelaCL.show)
        layout.addWidget(btn_novo_livro)
        
        btn_novo_aluno = self._criar_botao_nav("➕ Novo Aluno")
        btn_novo_aluno.clicked.connect(self.janelaCA.show)
        layout.addWidget(btn_novo_aluno)
        
        layout.addStretch()
        
        return sidebar
    
    def _criar_botao_nav(self, texto: str, ativo: bool = False) -> QPushButton:
        btn = QPushButton(texto)
        btn.setObjectName("nav-btn")
        btn.setProperty("active", ativo)
        btn.setFlat(True)
        btn.setStyleSheet(
            """
            QPushButton#nav-btn {
                background: transparent;
                border: none;
                border-left: 2px solid transparent;
                padding: 9px 16px 9px 14px;
                text-align: left;
                color: rgba(255,255,255,0.55);
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton#nav-btn:hover {
                background: rgba(173, 73, 225, 0.08);
                color: rgba(255,255,255,0.85);
            }
            QPushButton#nav-btn[active="true"] {
                background: rgba(173, 73, 225, 0.12);
                border-left: 2px solid #AD49E1;
                color: #c97ff0;
            }
            """
        )
        return btn
    
    def _switch_panel(self, index: int, btn: QPushButton):
        for b in self.nav_buttons:
            b.setProperty("active", False)
            b.style().unpolish(b)
            b.style().polish(b)
        
        btn.setProperty("active", True)
        btn.style().unpolish(btn)
        btn.style().polish(btn)
        
        self.stacked.setCurrentIndex(index)
        
        if index == 0:
            self._atualizar_tabela_acervo()
        elif index == 1:
            self._atualizar_tabela_alunos()
        elif index == 2:
            self._atualizar_tabela_emprestimos()
        elif index == 3:
            self._atualizar_tabela_devolucoes()
        self._atualizar_cards()
         
    def _criar_painel_acervo(self) -> QWidget:
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        metrics_layout = QHBoxLayout()
        self.card_livros = self._criar_metric_card("LIVROS NO\nACERVO", "0", "Total de livros cadastrados")
        self.card_emprestimos = self._criar_metric_card("EMPRÉSTIMOS\nATIVOS", "0", "Livros em circulação")
        self.card_alunos = self._criar_metric_card("ALUNOS\nCADASTRADOS", "0", "Total de alunos")
        self.card_disponiveis = self._criar_metric_card("DISPONÍVEIS\nAGORA", "0", "Prontos para empréstimo")
        self.card_livros_label = self.card_livros.valor_label
        self.card_emprestimos_label = self.card_emprestimos.valor_label
        self.card_alunos_label = self.card_alunos.valor_label
        self.card_disponiveis_label = self.card_disponiveis.valor_label
        
        metrics_layout.addWidget(self.card_livros)
        metrics_layout.addWidget(self.card_emprestimos)
        metrics_layout.addWidget(self.card_alunos)
        metrics_layout.addWidget(self.card_disponiveis)
        layout.addLayout(metrics_layout)
        
        busca_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search-bar")
        self.search_bar.setPlaceholderText(
            "Buscar por título, autor, gênero ou numeração (ex: tolkien · 0016 · 10-20)…"
        )
        self.search_bar.setFixedHeight(40)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setFixedWidth(100)
        btn_buscar.clicked.connect(self._buscar_livros)
        self.search_bar.returnPressed.connect(self._buscar_livros)
        
        busca_layout.addWidget(self.search_bar)
        busca_layout.addWidget(btn_buscar)
        layout.addLayout(busca_layout)
        
        self.status_label = QLabel()
        self.status_label.setObjectName("status-bar")
        self.status_label.setVisible(False)
        self.status_label.setStyleSheet(
            "background: rgba(173, 73, 225, 0.08); border: 1px solid rgba(173, 73, 225, 0.2); "
            "border-radius: 6px; padding: 5px 12px; color: rgba(255,255,255,0.6); font-size: 12px;"
        )
        layout.addWidget(self.status_label)
        
        filtros_layout = QHBoxLayout()
        self.label_filtros = QLabel("Filtros:")
        self.label_filtros.setStyleSheet("color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 500;")
        filtros_layout.addWidget(self.label_filtros)
        
        self.btn_todos = QPushButton("Todos")
        self.btn_todos.setCheckable(True)
        self.btn_todos.setChecked(True)
        self.btn_todos.clicked.connect(lambda: self._filtrar_livros("todos"))
        filtros_layout.addWidget(self.btn_todos)
        
        self.btn_disponiveis = QPushButton("Disponíveis")
        self.btn_disponiveis.setCheckable(True)
        self.btn_disponiveis.clicked.connect(lambda: self._filtrar_livros("disponiveis"))
        filtros_layout.addWidget(self.btn_disponiveis)
        
        filtros_layout.addStretch()

        layout.addLayout(filtros_layout)
        
        self.table_livros = QTableWidget()
        self.table_livros.setColumnCount(9)
        self.table_livros.setHorizontalHeaderLabels(
            ["Num.", "Título", "Autor", "Gênero", "Qtd.", "Nota", "Empr.", "Ano", "Ações"]
        )
        self.table_livros.setColumnWidth(0, 70)
        self.table_livros.setColumnWidth(1, 300)
        self.table_livros.setColumnWidth(2, 160)
        self.table_livros.setColumnWidth(3, 120)
        self.table_livros.setColumnWidth(4, 80)
        self.table_livros.setColumnWidth(5, 100)
        self.table_livros.setColumnWidth(6, 110)
        self.table_livros.setColumnWidth(7, 60)   
        self.table_livros.setColumnWidth(8, 220) 
        self.table_livros.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)
        self.table_livros.setColumnWidth(7, 70)
        self.table_livros.setColumnWidth(8, 180)
        self.table_livros.horizontalHeader().setSectionResizeMode(8, QHeaderView.Fixed)

        self.table_livros.setAlternatingRowColors(False)
        self.table_livros.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.15);
                color: #e0e0e0;
            }
            QTableWidget::item {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(173, 73, 225, 0.25);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: rgba(173, 73, 225, 0.1);
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.table_livros.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_livros.horizontalHeader().setStretchLastSection(False)
        self.table_livros.horizontalHeader().setSectionsClickable(True)
        self.table_livros.horizontalHeader().sectionClicked.connect(self._ordenar_por_coluna)
        layout.addWidget(self.table_livros)
        
        return painel
    
    def _criar_painel_alunos(self) -> QWidget:
        """Cria painel de alunos"""
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        busca_layout = QHBoxLayout()
        self.search_alunos = QLineEdit()
        self.search_alunos.setObjectName("search-bar")
        self.search_alunos.setPlaceholderText("Buscar aluno por nome ou ID…")
        self.search_alunos.setFixedHeight(40)
        
        btn_buscar = QPushButton("Buscar")
        btn_buscar.setFixedWidth(100)
        btn_buscar.clicked.connect(self._buscar_alunos)
        self.search_alunos.returnPressed.connect(self._buscar_alunos)
        
        busca_layout.addWidget(self.search_alunos)
        busca_layout.addWidget(btn_buscar)
        layout.addLayout(busca_layout)
        
        self.table_alunos = QTableWidget()
        self.table_alunos.setColumnCount(7)
        self.table_alunos.setHorizontalHeaderLabels(
            ["ID", "Nome", "Série", "Turno", "Contato", "Endereço", "Ações"]
        )
        self.table_alunos.setColumnWidth(0, 60)
        self.table_alunos.setColumnWidth(1, 200)
        self.table_alunos.setColumnWidth(2, 80)
        self.table_alunos.setColumnWidth(3, 100)
        self.table_alunos.setColumnWidth(4, 150)
        self.table_alunos.setColumnWidth(5, 200)
        self.table_alunos.setColumnWidth(6, 180)
        self.table_alunos.horizontalHeader().setSectionResizeMode(6, QHeaderView.Fixed)
        
        self.table_alunos.setAlternatingRowColors(False)
        self.table_alunos.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.15);
                color: #e0e0e0;
            }
            QTableWidget::item {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(173, 73, 225, 0.25);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: rgba(173, 73, 225, 0.1);
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.table_alunos.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_alunos)
        
        return painel
    
    def _criar_painel_emprestimos(self) -> QWidget:
        """Cria painel de empréstimos"""
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        titulo = QLabel("EMPRÉSTIMOS ATIVOS")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(titulo)
        
        # Tabela de empréstimos
        self.table_emprestimos = QTableWidget()
        self.table_emprestimos.setColumnCount(5)
        self.table_emprestimos.setHorizontalHeaderLabels(
            ["Chave", "Aluno", "Livro", "Devolução", "Ações"]
        )
        self.table_emprestimos.setColumnWidth(0, 100)
        self.table_emprestimos.setColumnWidth(1, 200)
        self.table_emprestimos.setColumnWidth(2, 250)
        self.table_emprestimos.setColumnWidth(3, 150)
        self.table_emprestimos.setColumnWidth(4, 180)
        self.table_emprestimos.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        
        self.table_emprestimos.setAlternatingRowColors(False)
        self.table_emprestimos.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.15);
                color: #e0e0e0;
            }
            QTableWidget::item {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(173, 73, 225, 0.25);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: rgba(173, 73, 225, 0.1);
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.table_emprestimos.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table_emprestimos)
        
        layout.addStretch()
        return painel
    
    def _criar_painel_devolucoes(self) -> QWidget:
        painel = QWidget()
        layout = QVBoxLayout(painel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        titulo = QLabel("HISTÓRICO DE DEVOLUÇÕES")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(titulo)

        self.table_devolucoes = QTableWidget()
        self.table_devolucoes.setColumnCount(4)
        self.table_devolucoes.setHorizontalHeaderLabels(
            ["Chave Devolução", "Livro", "Aluno", "Data de Devolução"]
        )
        self.table_devolucoes.setColumnWidth(0, 150)
        self.table_devolucoes.setColumnWidth(1, 280)
        self.table_devolucoes.setColumnWidth(2, 200)
        self.table_devolucoes.setColumnWidth(3, 180)
        self.table_devolucoes.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.table_devolucoes.setAlternatingRowColors(False)
        self.table_devolucoes.setStyleSheet("""
            QTableWidget {
                background-color: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.15);
                color: #e0e0e0;
            }
            QTableWidget::item {
                background-color: #1a1a2e;
                color: #e0e0e0;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(173, 73, 225, 0.25);
                color: #ffffff;
            }
            QTableWidget::item:hover {
                background-color: rgba(173, 73, 225, 0.1);
            }
            QScrollBar:vertical {
                background: #1a1a2e;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 4px;
            }
        """)
        self.table_devolucoes.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_devolucoes.setEditTriggers(QAbstractItemView.NoEditTriggers)

        layout.addWidget(self.table_devolucoes)
        return painel
    
    def _criar_metric_card(self, titulo: str, valor: str, subtitulo: str) -> QFrame:
        """Cria um card de métrica"""
        card = QFrame()
        card.setObjectName("metric-card")
        card.setStyleSheet(
            "background: rgba(255,255,255,0.04); border: 1px solid rgba(173, 73, 225, 0.15); "
            "border-radius: 8px; padding: 12px;"
        )
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 12, 12, 12)
        
        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet(
            "font-size: 11px; color: rgba(173, 73, 225, 0.6); letter-spacing: 0.5px; font-weight: bold;"
        )
        layout.addWidget(titulo_label)
        
        valor_label = QLabel(valor)
        valor_label.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(valor_label)
        
        subtitulo_label = QLabel(subtitulo)
        subtitulo_label.setStyleSheet("font-size: 11px; color: rgba(255,255,255,0.5);")
        layout.addWidget(subtitulo_label)
        
        # Armazenar labels para atualização
        card.titulo_label = titulo_label
        card.valor_label = valor_label
        card.subtitulo_label = subtitulo_label
        
        return card
    
    def _atualizar_tabela_acervo(self):
        """Atualiza a tabela de acervo"""
        self._popular_tabela_livros(list(self.b1.info_livros.values()))

    def _atualizar_tabela_alunos(self):
        """Atualiza a tabela de alunos"""
        self.table_alunos.setRowCount(0)
        
        for aluno_id, aluno in self.b1.info_alunos.items():
            row = self.table_alunos.rowCount()
            self.table_alunos.insertRow(row)
            
            if isinstance(aluno, dict):
                item_id = QTableWidgetItem(str(aluno_id))
                item_id.setForeground(Qt.white)
                self.table_alunos.setItem(row, 0, item_id)
                item_nome = QTableWidgetItem(str(aluno.get("nome", "")))
                item_nome.setForeground(Qt.white)
                self.table_alunos.setItem(row, 1, item_nome)
                item_serie = QTableWidgetItem(str(aluno.get("serie", "")))
                item_serie.setForeground(Qt.white)
                self.table_alunos.setItem(row, 2, item_serie)
                item_turno = QTableWidgetItem(str(aluno.get("turno", "")))
                item_turno.setForeground(Qt.white)
                self.table_alunos.setItem(row, 3, item_turno)
                item_contato = QTableWidgetItem(str(aluno.get("contato", "")))
                item_contato.setForeground(Qt.white)
                self.table_alunos.setItem(row, 4, item_contato)
                item_endereco = QTableWidgetItem(str(aluno.get("endereco", "")))
                item_endereco.setForeground(Qt.white)
                self.table_alunos.setItem(row, 5, item_endereco)
                               
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                btn_editar = QPushButton("Editar")
                btn_editar.setFixedWidth(70)
                btn_editar.clicked.connect(
                    lambda checked, aid=aluno_id: self._abrir_altera_aluno(aid)
                )
                
                btn_layout.addWidget(btn_editar)
                self.table_alunos.setCellWidget(row, 6, btn_container)
    
    def _atualizar_tabela_emprestimos(self):
        """Atualiza a tabela de empréstimos"""
        self.table_emprestimos.setRowCount(0)
        
        for chave, emprestimo in self.b1.emprestimos.items():
            row = self.table_emprestimos.rowCount()
            self.table_emprestimos.insertRow(row)
            
            if isinstance(emprestimo, dict):
                item_chave = QTableWidgetItem(str(chave))
                item_chave.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 0, item_chave)
                
                aluno_info = emprestimo.get("aluno", {})
                if isinstance(aluno_info, dict):
                    aluno_nome = aluno_info.get("nome", "N/A")
                else:
                    aluno_nome = str(aluno_info)
                item_aluno = QTableWidgetItem(aluno_nome)
                item_aluno.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 1, item_aluno)
                
                item_livro = QTableWidgetItem(str(emprestimo.get("livro", "")))
                item_livro.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 2, item_livro)
                item_devolucao = QTableWidgetItem(str(emprestimo.get("devolucao", "")))
                item_devolucao.setForeground(Qt.white)
                self.table_emprestimos.setItem(row, 3, item_devolucao)
                
                btn_container = QWidget()
                btn_layout = QHBoxLayout(btn_container)
                btn_layout.setContentsMargins(2, 2, 2, 2)
                
                btn_devolver = QPushButton("Devolver")
                btn_devolver.setFixedWidth(70)
                btn_devolver.clicked.connect(
                    lambda checked, c=chave: self._fazer_devolucao(c)
                )
                
                btn_layout.addWidget(btn_devolver)
                self.table_emprestimos.setCellWidget(row, 4, btn_container)

    def _atualizar_tabela_devolucoes(self):
        self.table_devolucoes.setRowCount(0)
        for chave_dev, registro in self.b1.historico_devolucoes.items():
            row = self.table_devolucoes.rowCount()
            self.table_devolucoes.insertRow(row)

            item_chave = QTableWidgetItem(str(chave_dev))
            item_chave.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 0, item_chave)

            item_livro = QTableWidgetItem(str(registro.get("livro", "")))
            item_livro.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 1, item_livro)

            item_aluno = QTableWidgetItem(str(registro.get("aluno", "")))
            item_aluno.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 2, item_aluno)

            item_data = QTableWidgetItem(str(registro.get("data_devolucao", "")))
            item_data.setForeground(Qt.white)
            self.table_devolucoes.setItem(row, 3, item_data)
    
    def _atualizar_cards(self):
        total_livros = len(self.b1.info_livros)
        emprestimos_ativos = len(self.b1.emprestimos)
        total_alunos = len(self.b1.info_alunos)
        disponiveis = sum(
            int(dados.get("quantidade", 0))
            for dados in self.b1.info_livros.values()
            if isinstance(dados, dict)
        )
        self.card_livros_label.setText(str(total_livros))
        self.card_emprestimos_label.setText(str(emprestimos_ativos))
        self.card_alunos_label.setText(str(total_alunos))
        self.card_disponiveis_label.setText(str(disponiveis))

    def _conectar_atualizacao_dialogos(self):
        self.janelaCA.finished.connect(self._atualizar_interface_dados)
        self.janelaCL.finished.connect(self._atualizar_interface_dados)
        self.janelaAA.finished.connect(self._atualizar_interface_dados)
        self.janelaAL.finished.connect(self._atualizar_interface_dados)
        self.janelaEP.finished.connect(self._atualizar_interface_dados)
        self.janelaDV.finished.connect(self._atualizar_interface_dados)

    def _atualizar_interface_dados(self):
        self._atualizar_tabela_acervo()
        self._atualizar_tabela_alunos()
        self._atualizar_tabela_emprestimos()
        self._atualizar_cards()
        self._atualizar_tabela_devolucoes()
    
    def _buscar_livros(self):
        query = self.search_bar.text().strip()

        if not query:
            self._atualizar_tabela_acervo()
            self.status_label.setVisible(False)
            return

        # Chama o motor central — ele decide qual algoritmo usar
        resposta = self.b1.motor.buscar(query)

        resultados  = resposta["resultados"]
        motor_usado = resposta["motor_usado"]
        tempo_ms    = resposta["tempo_ms"]
        comparacoes = resposta["comparacoes"]
        score       = resposta["score"]
        sugestao    = resposta["sugestao"]

        # Monta texto do status
        if motor_usado == "BST_EXATA":
            status = f"Motor: BST (exata) · {len(resultados)} resultado(s) · {comparacoes} comparações"
        elif motor_usado == "BST_INTERVALO":
            status = f"Motor: BST (intervalo) · {len(resultados)} resultado(s) · {comparacoes} comparações"
        elif motor_usado == "INVERTIDO":
            status = f"Motor: Índice Invertido (AND) · {len(resultados)} resultado(s)"
        elif motor_usado == "INVERTIDO_OR":
            status = f"Motor: Índice Invertido (OR) · {len(resultados)} resultado(s)"
        elif motor_usado == "FUZZY":
            status = f"Motor: Fuzzy · {len(resultados)} resultado(s)"
            if sugestao:
                status += f' · Você quis dizer: "{sugestao}"?'
        else:
            status = f"{len(resultados)} resultado(s)"

        # Popula a tabela com os resultados
        self._popular_tabela_livros(resultados)

        # Atualiza o label de status
        self.status_label.setText(status)
        self.status_label.setVisible(True)

    def _popular_tabela_livros(self, livros: list):
        livros_filtrados = [l for l in livros if isinstance(l, dict)]

        # Ordenação por coluna
        if self.ordenacao_coluna is None:  # Ordem original por Numeração
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: int(l.get("numeracao", 0)) if str(l.get("numeracao", "0")).isdigit() else 0,
                reverso=False
            )
        elif self.ordenacao_coluna == 1:  # Título
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: str(l.get("titulo") or "").lower(),
                reverso=self.ordenacao_reverso
            )
        elif self.ordenacao_coluna == 2:  # Autor
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: str(l.get("autor") or "").lower(),
                reverso=self.ordenacao_reverso
            )
        elif self.ordenacao_coluna == 3:  # Gênero
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: str(l.get("genero") or "").lower(),
                reverso=self.ordenacao_reverso
            )
        elif self.ordenacao_coluna == 5:  # Nota Média
            livros_ordenados = heapsort(
                livros_filtrados,
                chave=lambda l: float(l.get("nota_media") or 0.0),
                reverso=self.ordenacao_reverso
            )
        elif self.ordenacao_coluna == 6:  # Empréstimos
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: int(l.get("contagem_emprestimos", 0)),
                reverso=self.ordenacao_reverso
            )
        elif self.ordenacao_coluna == 7:  # Ano
            livros_ordenados = radix_sort_por_ano(livros_filtrados, reverso=self.ordenacao_reverso)
        else:  # Fallback para numeração
            livros_ordenados = quicksort(
                livros_filtrados,
                chave=lambda l: int(l.get("numeracao", 0)) if str(l.get("numeracao", "0")).isdigit() else 0,
                reverso=False
            )

        self.table_livros.setRowCount(0)
        for livro in livros_ordenados:
            numeracao = livro.get("numeracao", "")
            row = self.table_livros.rowCount()
            self.table_livros.insertRow(row)

            item_num = QTableWidgetItem(str(numeracao))
            item_num.setForeground(Qt.white)
            item_num.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 0, item_num)

            item_titulo = QTableWidgetItem(str(livro.get("titulo", "")))
            item_titulo.setForeground(Qt.white)
            self.table_livros.setItem(row, 1, item_titulo)

            item_autor = QTableWidgetItem(str(livro.get("autor", "")))
            item_autor.setForeground(Qt.white)
            self.table_livros.setItem(row, 2, item_autor)

            item_genero = QTableWidgetItem(str(livro.get("genero", "")))
            item_genero.setForeground(Qt.white)
            item_genero.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 3, item_genero)

            item_qtd = QTableWidgetItem(str(livro.get("quantidade", "")))
            item_qtd.setForeground(Qt.white)
            item_qtd.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 4, item_qtd)

            item_nota = QTableWidgetItem(f"{livro.get('nota_media', 0.0):.2f}")
            item_nota.setForeground(Qt.white)
            item_nota.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 5, item_nota)

            item_emprestimos = QTableWidgetItem(str(livro.get("contagem_emprestimos", 0)))
            item_emprestimos.setForeground(Qt.white)
            item_emprestimos.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 6, item_emprestimos)

            item_ano = QTableWidgetItem(str(livro.get("ano", "")))
            item_ano.setForeground(Qt.white)
            item_ano.setTextAlignment(Qt.AlignCenter)
            self.table_livros.setItem(row, 7, item_ano)

            btn_container = QWidget()
            btn_layout = QHBoxLayout(btn_container)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            btn_emprestar = QPushButton("Emprestar")
            btn_emprestar.setFixedWidth(88)
            btn_emprestar.clicked.connect(
                lambda checked, n=numeracao: self._abrir_emprestimo(n)
            )
            btn_editar = QPushButton("Editar")
            btn_editar.setFixedWidth(72)
            btn_editar.clicked.connect(
                lambda checked, n=numeracao: self._abrir_altera_livro(n)
            )
            btn_layout.addWidget(btn_emprestar)
            btn_layout.addWidget(btn_editar)
            self.table_livros.setCellWidget(row, 8, btn_container)
                
    def _ordenar_por_coluna(self, col_index: int):
        """Abre menu de contexto para ordenação da coluna clicada"""
        colunas_permitidas = [1, 5, 6, 7]
        colunas_texto = [1, 2, 3]
        colunas_numericas = [5, 6, 7]
        if col_index not in (colunas_texto + colunas_numericas):
            return

        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1a1a2e; color: #AD49E1; border: 1px solid #AD49E1; } "
                           "QMenu::item:selected { background-color: #AD49E1; color: white; }")

        if col_index in colunas_texto:
            label_asc = "Ordenar de A → Z"
            label_desc = "Ordenar de Z → A"
        elif col_index == 5:
            label_asc = "Menor Nota"
            label_desc = "Maior Nota"
        elif col_index == 6:
            label_asc = "Menos Populares"
            label_desc = "Mais Populares"
        elif col_index == 7:
            label_asc = "Mais Antigos"
            label_desc = "Mais Recentes"
        else:
            label_asc = "Menor para Maior"
            label_desc = "Maior para Menor"

        acao_asc = menu.addAction(label_asc)
        acao_desc = menu.addAction(label_desc)
        menu.addSeparator()
        acao_limpar = menu.addAction("Limpar Ordenação")

        acao = menu.exec(QCursor.pos())
        if not acao:
            return

        direcao = "asc" if acao == acao_asc else "desc" if acao == acao_desc else None
        self._executar_logica_ordenacao(col_index, direcao)
                
    def _executar_logica_ordenacao(self, col_index: int, direcao: str | None):
        """Executa a lógica de ordenação baseada na coluna e direção"""
        if direcao is None:  # Limpar ordenação
            self.ordenacao_coluna = None
            self.ordenacao_reverso = False
            headers = ["Num.", "Título", "Autor", "Gênero", "Qtd.", "Nota", "Empr.", "Ano", "Ações"]
            self.table_livros.setHorizontalHeaderLabels(headers)
        else:
            self.ordenacao_coluna = col_index
            self.ordenacao_reverso = (direcao == "desc")
            
            headers = ["Num.", "Título", "Autor", "Gênero", "Qtd.", "Nota", "Empr.", "Ano", "Ações"]
            if col_index == 1:  # Título
                headers[col_index] = f"Título {'↓' if direcao == 'asc' else '↑'}"
            elif col_index == 2:  # Autor
                headers[col_index] = f"Autor {'↓' if direcao == 'asc' else '↑'}"
            elif col_index == 3:  # Gênero
                headers[col_index] = f"Gênero {'↓' if direcao == 'asc' else '↑'}"
            elif col_index == 5:  # Nota
                headers[col_index] = f"Nota {'↓' if direcao == 'asc' else '↑'}"
            elif col_index == 6:  # Empréstimos
                headers[col_index] = f"Empr. {'↓' if direcao == 'asc' else '↑'}"
            elif col_index == 7:  # Ano
                headers[col_index] = f"Ano {'↓' if direcao == 'asc' else '↑'}"
            self.table_livros.setHorizontalHeaderLabels(headers)
        
        self._atualizar_tabela_acervo()
                
    def _buscar_alunos(self):
        """Busca alunos por nome ou ID"""
        query = self.search_alunos.text().lower()
        
        self.table_alunos.setRowCount(0)
        
        for aluno_id, aluno in self.b1.info_alunos.items():
            if isinstance(aluno, dict):
                nome = str(aluno.get("nome", "")).lower()
                aid = str(aluno_id).lower()
                
                if not query or query in nome or query in aid:
                    row = self.table_alunos.rowCount()
                    self.table_alunos.insertRow(row)
                    
                    item_id = QTableWidgetItem(str(aluno_id))
                    item_id.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 0, item_id)
                    item_nome = QTableWidgetItem(str(aluno.get("nome", "")))
                    item_nome.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 1, item_nome)
                    item_serie = QTableWidgetItem(str(aluno.get("serie", "")))
                    item_serie.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 2, item_serie)
                    item_turno = QTableWidgetItem(str(aluno.get("turno", "")))
                    item_turno.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 3, item_turno)
                    item_contato = QTableWidgetItem(str(aluno.get("contato", "")))
                    item_contato.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 4, item_contato)
                    item_endereco = QTableWidgetItem(str(aluno.get("endereco", "")))
                    item_endereco.setForeground(Qt.white)
                    self.table_alunos.setItem(row, 5, item_endereco)
                    
                    btn_container = QWidget()
                    btn_layout = QHBoxLayout(btn_container)
                    btn_layout.setContentsMargins(2, 2, 2, 2)
                    
                    btn_editar = QPushButton("Editar")
                    btn_editar.setFixedWidth(70)
                    btn_editar.clicked.connect(lambda checked, aid=aluno_id: self._abrir_altera_aluno(aid))
                    
                    btn_layout.addWidget(btn_editar)
                    self.table_alunos.setCellWidget(row, 6, btn_container)
    
    def _filtrar_livros(self, filtro: str):
        """Filtra a tabela de livros"""
        self.search_bar.clear()
        self.status_label.setVisible(False)
        
        self.btn_todos.setChecked(filtro == "todos")
        self.btn_disponiveis.setChecked(filtro == "disponiveis")

        livros_filtrados = []
        for livro in self.b1.info_livros.values():
            if not isinstance(livro, dict):
                continue
            if filtro == "todos":
                incluir = True
            elif filtro == "disponiveis":
                incluir = livro.get("quantidade", 0) > 0
            else:
                incluir = True
            if incluir:
                livros_filtrados.append(livro)

        self._popular_tabela_livros(livros_filtrados)
    
    def _abrir_emprestimo(self, numeracao: str):
        """Abre janela de empréstimo com livro pré-preenchido"""
        livro = self.b1.info_livros.get(numeracao)
        if isinstance(livro, dict):
            self.janelaEP.livro.setText(livro.get("titulo", ""))
        self.janelaEP.show()
    
    def _abrir_altera_livro(self, numeracao: str):
        """Abre janela de alteração de livro com dados pré-preenchidos"""
        livro = self.b1.info_livros.get(numeracao)
        if isinstance(livro, dict):
            pass
        self.janelaAL.show()
    
    def _abrir_altera_aluno(self, aluno_id: str):
        """Abre janela de alteração de aluno"""
        self.janelaAA.show()
    
    def _fazer_devolucao(self, chave: str):
        """Faz a devolução de um livro"""
        try:
            emprestimo = self.b1.emprestimos.get(chave)
            livro_titulo = ""
            livro_id = None

            if isinstance(emprestimo, dict):
                livro_titulo = emprestimo.get("livro", "")
                for numeracao, livro in self.b1.info_livros.items():
                    if isinstance(livro, dict) and livro.get("titulo", "").lower() == str(livro_titulo).lower():
                        livro_id = numeracao
                        break

            self.b1.fazer_devolucao(chave)

            if livro_id and self._perguntar_avaliacao(livro_titulo):
                nota = self._abrir_janela_avaliacao(livro_titulo)
                if nota is not None:
                    try:
                        self.b1.avaliar_livro(livro_id, nota)
                        faz_msg_box("Avaliação registrada!", f"Você avaliou '{livro_titulo}' com {nota} estrelas.", False)
                    except ValueError as e:
                        faz_msg_box("Erro", str(e), True)

            faz_msg_box("Sucesso", "Devolução realizada com sucesso!", False)
            self._atualizar_tabela_emprestimos()
            self._atualizar_tabela_devolucoes()
            self._atualizar_cards()
        except KeyError:
            faz_msg_box("Erro", "Chave de empréstimo não encontrada!", True)
    
    def _perguntar_avaliacao(self, livro_titulo: str) -> bool:
        pergunta = QMessageBox(self)
        pergunta.setWindowTitle("Avaliação do Livro")
        pergunta.setText(f"Deseja avaliar este livro?\n{livro_titulo}")
        pergunta.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        pergunta.setDefaultButton(QMessageBox.Yes)
        return pergunta.exec() == QMessageBox.Yes

    def _abrir_janela_avaliacao(self, livro_titulo: str) -> float | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Avaliar Livro")
        dialog.setMinimumSize(360, 180)
        dialog.setStyleSheet(self.styleSheet())

        layout = QFormLayout(dialog)
        label = QLabel(f"Avalie '{livro_titulo}' (0-5 estrelas)")
        layout.addRow(label)

        nota_spin = QDoubleSpinBox()
        nota_spin.setRange(0.0, 5.0)
        nota_spin.setSingleStep(0.1)
        nota_spin.setValue(5.0)
        nota_spin.setDecimals(1)
        layout.addRow("Nota (estrelas):", nota_spin)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b_box.accepted.connect(dialog.accept)
        b_box.rejected.connect(dialog.reject)
        layout.addWidget(b_box)

        if dialog.exec() == QDialog.Accepted:
            return float(nota_spin.value())
        return None
    
    def config_style(self):
        """Configura o estilo visual"""
        screen = QApplication.primaryScreen()
        screen_size = screen.size()

        self.resize(int(screen_size.width() * 0.95), int(screen_size.height() * 0.95))
        self.showMaximized()

        # Tema escuro roxo
        STYLESHEET = """
        QMainWindow, QDialog {
            background-color: #1a1a2e;
        }
        QFrame#sidebar {
            background-color: #12122a;
            border-right: 1px solid rgba(173, 73, 225, 0.2);
        }
        QPushButton#nav-btn {
            background: transparent;
            border: none;
            border-left: 2px solid transparent;
            padding: 9px 16px 9px 14px;
            text-align: left;
            color: rgba(255,255,255,0.55);
            font-size: 13px;
        }
        QPushButton#nav-btn:hover {
            background: rgba(173, 73, 225, 0.08);
            color: rgba(255,255,255,0.85);
        }
        QPushButton#nav-btn[active="true"] {
            background: rgba(173, 73, 225, 0.12);
            border-left: 2px solid #AD49E1;
            color: #c97ff0;
        }
        QFrame#metric-card {
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(173, 73, 225, 0.15);
            border-radius: 8px;
            padding: 12px;
        }
        QTableWidget {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(173, 73, 225, 0.12);
            border-radius: 8px;
            gridline-color: rgba(255,255,255,0.04);
        }
        QTableWidget::item:selected {
            background: rgba(173, 73, 225, 0.2);
        }
        QHeaderView::section {
            background: rgba(173, 73, 225, 0.07);
            color: rgba(120, 30, 170, 1.0);
            font-size: 10px;
            letter-spacing: 1px;
            border: none;
            padding: 6px 8px;
            cursor: pointing_hand;
        }
        QHeaderView::section:hover {
            background: rgba(173, 73, 225, 0.15);
        }
       QLineEdit#search-bar {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(173, 73, 225, 0.3);
            border-radius: 8px;
            padding: 9px 14px 9px 14px;
            color: #e0e0e0;
            font-size: 13px;
        }
        QLabel#status-bar {
            background: rgba(173, 73, 225, 0.08);
            border: 1px solid rgba(173, 73, 225, 0.2);
            border-radius: 6px;
            padding: 5px 12px;
            color: rgba(255,255,255,0.6);
            font-size: 12px;
        }
        QLabel#section-label {
            color: rgba(173, 73, 225, 0.45);
            font-size: 10px;
            letter-spacing: 2px;
            padding: 12px 16px 4px;
        }
        QPushButton {
            background: rgba(173, 73, 225, 0.2);
            color: #e0e0e0;
            border: 1px solid rgba(173, 73, 225, 0.3);
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: rgba(173, 73, 225, 0.3);
        }
        QPushButton:pressed {
            background: rgba(173, 73, 225, 0.4);
        }
        """

        STYLESHEET += """
        QTableWidget {
            color: #e0e0e0;
        }
        QTableWidgetItem {
            color: #e0e0e0;
        }
        """
        
        self.setStyleSheet(STYLESHEET)


class JanelaCadastraAluno(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Cadastro de Aluno")
        self.setMinimumSize(900, 350)
        self.layoutca = QFormLayout()
        self.setLayout(self.layoutca)

        self.campo_texto = [nome := QLineEdit(), idade := QSpinBox(),
                            serie := QLineEdit(), turno := QLineEdit(),
                            contato := QLineEdit(), endereco := QLineEdit()]
        self.titulos = ["Nome Aluno", "Idade", "Série", "Turno", "Contato", "Endereço"]

        for titulo, campo in zip(self.titulos, self.campo_texto):
            self.layoutca.addRow(titulo, campo)

        self.botoes_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        self.layoutca.addWidget(self.botoes_box)

        self.botoes_box.accepted.connect(self.faz_slot(
            biblioteca.cadastra_aluno,
            nome, idade, serie,
            turno, contato, endereco
        ))

        self.botoes_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, i, s, t, c, e = args
            if self.verifica_campos(n, i, s, t, c, e):
                msg = func(n.text(), str(i.value()), s.text(), t.text(), c.text(), e.text())
                for b in args:
                    b.clear()
                faz_msg_box("Cadastro realizado!", str(msg), False)
            else:
                faz_msg_box("Erro", "Preencha todos os campos corretamente.", True)

        return slot

    def verifica_campos(self, nome, idade, serie, turno, contato, endereco):
        if not nome.text() or not serie.text() or not turno.text() or not contato.text() or not endereco.text():
            return False
        if idade.value() <= 0:
            return False
        return True


#Configurações da janela de cadastro dos livros 
class JanelaCadastroLivro(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Cadastro de Livro")
        self.setMinimumSize(900, 350)
        layoutcl = QFormLayout()
        self.setLayout(layoutcl)

        layoutcl.addRow("Numeração:", numeracao := QSpinBox())
        numeracao.setRange(0, 9999999)

        layoutcl.addRow("Titulo Livro:", titulo := QLineEdit())
        layoutcl.addRow("Genero:", genero := QLineEdit())
        layoutcl.addRow("Autor:", autor := QLineEdit())
        layoutcl.addRow("Editora:", editora := QLineEdit())
        layoutcl.addRow("Quantidade:", qtd := QSpinBox())
        qtd.setRange(0, 9999)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutcl.addWidget(b_box)

        b_box.accepted.connect(
            self.faz_slot(
                biblioteca.cadastra_livro,
                numeracao, titulo, genero, autor, editora, qtd
            )
        )
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, t, g, a, e, q = args
            if self.verifica_campos(*args):  
                msg = func(
                    n.text(), t.text(), g.text(), a.text(), e.text(), q.value()
                )
                for b in args:
                    b.clear()
                faz_msg_box(
                    "Cadastro Realizado!", str(msg), False
                )
        return slot

    def verifica_campos(self, *args):
        n, t, g, a, e, q = args
        if not n.text() or not t.text() or not g.text() or not a.text() or not e.text():
            faz_msg_box("Erro", "Todos os campos precisam ser preenchidos.", True)
            return False
        if q.value() <= 0:
            faz_msg_box("Erro", "A quantidade deve ser maior que zero.", True)
            return False
        return True
    
def faz_msg_box(titulo, mensagem, erro=False):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensagem)
    if erro:
        msg.setIcon(QMessageBox.Critical)  
    else:
        msg.setIcon(QMessageBox.Information)  
    msg.exec()

class JanelaAteraAluno(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Altera Cadastro - Aluno")
        self.setMinimumSize(900, 350)
        layoutaa = QFormLayout()
        self.setLayout(layoutaa)

        campo_texto = [_id := QSpinBox(), nome := QLineEdit(),
                       idade := QSpinBox(), serie := QLineEdit(),
                       turno := QLineEdit(), contato := QLineEdit(),
                       endereco := QLineEdit()]

        _id.setRange(0, 999999)
        titulos = ["ID", "Nome Aluno", "Idade", "Série", "Turno", "Contato", "Endereço"]

        for titulo, campo in zip(titulos, campo_texto):
            layoutaa.addRow(str(titulo), campo)

        self.botoes_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutaa.addWidget(self.botoes_box)

        self.botoes_box.accepted.connect(self.faz_slot(
            biblioteca.altera_aluno,
            _id, nome, idade, serie, turno, contato, endereco
        ))

        self.botoes_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            __id, n, i, s, t, c, e = args
            if self.verifica_campos(*args):
                aluno_id = str(__id.value())
                msg = func(aluno_id, n.text(), i.text(), s.text(), t.text(), c.text(), e.text())

                if msg is None:
                    faz_msg_box("ERRO!", "O ID digitado não existe.", True)
                else:
                    for b in args:
                        b.clear()
                    faz_msg_box("Cadastro atualizado!", str(msg), False)

        return slot

    def verifica_campos(self, *args):
        nome, idade, serie, turno, contato, endereco = args[1:]

        if not nome.text() or not serie.text() or not turno.text() or not contato.text() or not endereco.text():
            return False
        if idade.value() <= 0:
            return False
        return True


#Configurações da janela de alteção dos livros 
class JanelaAlteraLivro(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
                QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)

        self.setWindowTitle("Altera Cadastro - Livro")
        self.setMinimumSize(900, 350)
        layoutcl = QFormLayout()
        self.setLayout(layoutcl)

        layoutcl.addRow("Numeração:", numeracao := QSpinBox())
        numeracao.setRange(0, 9999999)

        layoutcl.addRow("Titulo Livro:", titulo := QLineEdit())
        layoutcl.addRow("Genero:", genero := QLineEdit())
        layoutcl.addRow("Autor:", autor := QLineEdit())
        layoutcl.addRow("Editora:", editora := QLineEdit())
        layoutcl.addRow("Quantidade:", qtd := QSpinBox())
        qtd.setRange(0, 999)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutcl.addWidget(b_box)

        b_box.accepted.connect(
            self.faz_slot(
                biblioteca.altera_livro,
                numeracao, titulo, genero, autor, editora, qtd
            )
        )
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func, *args):
        def slot():
            n, t, g, a, e, q = args
            if self.verifica_campos(*args): 
                msg = func(
                    n.text(), t.text(), g.text(), a.text(), e.text(), q.value()
                )
                for b in args:
                    b.clear()
                if msg is None:
                    faz_msg_box("ERRO!", "ID não encontrado.", True)
                    return
                # Exibe a mensagem de sucesso após a alteração
                faz_msg_box("Cadastro Alterado!", "O livro foi alterado com sucesso.", False) 

        return slot

    def verifica_campos(self, *args):
        n, t, g, a, e, q = args
        if not n.text() or not t.text() or not g.text() or not a.text() or not e.text():
            faz_msg_box("Erro", "Todos os campos precisam ser preenchidos.", True)
            return False
        if q.value() <= 0:
            faz_msg_box("Erro", "A quantidade deve ser maior que zero.", True)
            return False
        return True

def faz_msg_box(titulo, mensagem, erro=False):
    msg = QMessageBox()
    msg.setWindowTitle(titulo)
    msg.setText(mensagem)  
    if erro:
        msg.setIcon(QMessageBox.Critical)  
    else:
        msg.setIcon(QMessageBox.Information)  
    msg.exec()


#Configurações da janela de Emprestimo
class JanelaEmprestimo(QDialog):


    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.biblioteca = biblioteca
        self.setWindowTitle("Empréstimo de Livro")
        self.setMinimumSize(520, 360)
        self.setStyleSheet("""
            QDialog, QWidget { background-color: #1a1a2e; color: #e0e0e0; }
            QLabel            { color: #e0e0e0; }
            QLineEdit, QDateEdit {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173,73,225,0.3);
                border-radius: 6px; padding: 7px 12px; color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173,73,225,0.2);
                border: 1px solid rgba(173,73,225,0.4);
                border-radius: 6px; padding: 8px 18px; color: #e0e0e0;
            }
            QPushButton:hover { background: rgba(173,73,225,0.35); }
        """)

        from PySide6.QtCore import QDate

        layout = QFormLayout(self)

        self._id = QLineEdit()
        layout.addRow("ID do Aluno:", self._id)

        self.livro = QLineEdit()
        layout.addRow("Título do Livro:", self.livro)

        self.data_inicio = QDateEdit()
        self.data_inicio.setCalendarPopup(True)
        self.data_inicio.setDate(QDate.currentDate())
        layout.addRow("Data de Início:", self.data_inicio)

        self.data_fim = QDateEdit()
        self.data_fim.setCalendarPopup(True)
        self.data_fim.setDate(QDate.currentDate().addDays(15))
        layout.addRow("Data de Devolução:", self.data_fim)

        
        self.status_intervalo = QLabel("Selecione as datas para verificar disponibilidade.")
        self.status_intervalo.setWordWrap(True)
        self.status_intervalo.setStyleSheet("color: #aaaaaa; font-style: italic;")
        layout.addRow("📅 Disponibilidade:", self.status_intervalo)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b_box.accepted.connect(self.realiza_emprestimo)
        b_box.rejected.connect(self.reject)
        layout.addWidget(b_box)

        
        self.data_inicio.dateChanged.connect(self._verificar_disponibilidade)
        self.data_fim.dateChanged.connect(self._verificar_disponibilidade)
        self._id.textChanged.connect(self._verificar_disponibilidade)
        self.livro.textChanged.connect(self._verificar_disponibilidade)


    def _verificar_disponibilidade(self):
        """Consulta a RBTIntervalos e atualiza o label de status."""
        from datetime import date as _date

        inicio_q = self.data_inicio.date()
        fim_q    = self.data_fim.date()

        if fim_q < inicio_q:
            self.status_intervalo.setText("⚠️  A data de devolução é anterior ao início.")
            self.status_intervalo.setStyleSheet("color: #ff9800; font-weight: bold;")
            return

        inicio = _date(inicio_q.year(), inicio_q.month(), inicio_q.day())
        fim    = _date(fim_q.year(),    fim_q.month(),    fim_q.day())

        if not self.biblioteca.rbt_intervalos:
            return

        titulo_digitado = self.livro.text().strip().lower()
        _id = self._id.text().strip()

        todos, _, _ = self.biblioteca.rbt_intervalos.buscar_todos_sobrepostos(inicio, fim)

        # 1) Mesmo aluno já tem empréstimo no período
        if _id:
            for emp in todos:
                aluno_emp = emp.get("aluno", {})
                id_emp = aluno_emp.get("id") if isinstance(aluno_emp, dict) else None
                if id_emp == _id:
                    livro_emp = emp.get("livro", "?")
                    dev_emp   = emp.get("devolucao", "?")
                    self.status_intervalo.setText(
                        f"🔴  Este aluno já possui '{livro_emp}' emprestado até {dev_emp}."
                    )
                    self.status_intervalo.setStyleSheet("color: #f44336; font-weight: bold;")
                    return

        # 2) Todos os exemplares do livro estão emprestados no período
        if titulo_digitado:
            qtd_exemplares = 0
            for dados in self.biblioteca.info_livros.values():
                if isinstance(dados, dict) and dados.get("titulo", "").lower() == titulo_digitado:
                    qtd_exemplares = int(dados.get("quantidade", 1))
                    break
            if qtd_exemplares == 0:
                qtd_exemplares = 1

            emprestimos_livro = [
                emp for emp in todos
                if emp.get("livro", "").lower() == titulo_digitado
            ]
            if len(emprestimos_livro) >= qtd_exemplares:
                dev_conf = emprestimos_livro[0].get("devolucao", "?")
                self.status_intervalo.setText(
                    f"🔴  Todos os {qtd_exemplares} exemplar(es) estão emprestados neste período "
                    f"(devolução mais próxima: {dev_conf})."
                )
                self.status_intervalo.setStyleSheet("color: #f44336; font-weight: bold;")
                return

        # Período livre
        self.status_intervalo.setText(
            f"✅  Período disponível: {inicio.strftime('%d/%m/%Y')} → {fim.strftime('%d/%m/%Y')}"
        )
        self.status_intervalo.setStyleSheet("color: #4caf50; font-weight: bold;")

    
    def realiza_emprestimo(self):
        """Processa o empréstimo; bloqueia se houver conflito."""
        _id   = self._id.text().strip()
        livro = self.livro.text().strip()
        inicio = self.data_inicio.date().toString("yyyy-MM-dd")
        fim    = self.data_fim.date().toString("yyyy-MM-dd")

        if not _id or not livro:
            faz_msg_box("Erro", "Preencha o ID do aluno e o título do livro.", True)
            return

        try:
            chave, _ = self.biblioteca.fazer_emprestimo(_id, livro, fim, inicio=inicio)
            faz_msg_box(
                "Empréstimo realizado! ✅",
                f"Livro: {livro}\nChave: {chave}\n"
                f"Devolução prevista: {fim}",
                False,
            )
            self.accept()
        except KeyError as e:
            faz_msg_box("Erro", f"ID de aluno não encontrado: {e}", True)
        except ValueError as e:
            faz_msg_box("Conflito de datas — Empréstimo bloqueado 🔴", str(e), True)


class PainelRelatorio(QWidget):

    ESTILO = """
        QWidget { background: #1a1a2e; color: #e0e0e0; }
        QLabel  { color: #e0e0e0; }
        QLabel#titulo   { color: #AD49E1; font-size: 16px; font-weight: bold; }
        QPushButton {
            background: rgba(173,73,225,0.25);
            border: 1px solid rgba(173,73,225,0.5);
            border-radius: 6px; padding: 8px 20px; color: #e0e0e0;
        }
        QPushButton:hover { background: rgba(173,73,225,0.4); }
        QDateEdit {
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(173,73,225,0.3);
            border-radius: 5px; padding: 5px; color: #e0e0e0;
        }
        QTableWidget {
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(173,73,225,0.12);
            border-radius: 8px; gridline-color: rgba(255,255,255,0.04);
        }
        QHeaderView::section {
            background: rgba(173,73,225,0.07);
            color: rgba(173,73,225,1.0); padding: 6px;
            border: none; font-weight: bold;
        }
        QTableWidget::item { padding: 4px; }
        QTableWidget::item:selected { background: rgba(173,73,225,0.2); }
    """

    def __init__(self, biblioteca, parent=None):
        super().__init__(parent)
        self.biblioteca = biblioteca
        self.setStyleSheet(self.ESTILO)
        self._construir_ui()

    def _construir_ui(self):
        from PySide6.QtCore import QDate

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(14)

        titulo = QLabel("📊 Relatório de Empréstimos por Período")
        titulo.setObjectName("titulo")
        root.addWidget(titulo)

        periodo = QHBoxLayout()
        periodo.addWidget(QLabel("De:"))

        self.date_inicio = QDateEdit()
        self.date_inicio.setCalendarPopup(True)
        self.date_inicio.setDate(QDate.currentDate().addDays(-30))
        periodo.addWidget(self.date_inicio)

        periodo.addSpacing(12)
        periodo.addWidget(QLabel("Até:"))

        self.date_fim = QDateEdit()
        self.date_fim.setCalendarPopup(True)
        self.date_fim.setDate(QDate.currentDate().addDays(30))
        periodo.addWidget(self.date_fim)

        periodo.addSpacing(20)
        btn = QPushButton("🔍  Gerar Relatório")
        btn.clicked.connect(self._gerar)
        periodo.addWidget(btn)
        periodo.addStretch()
        root.addLayout(periodo)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(
            ["Chave", "Aluno", "Livro", "Início", "Devolução"]
        )
        self.tabela.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tabela.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabela.setSelectionBehavior(QAbstractItemView.SelectRows)
        root.addWidget(self.tabela)

    def _gerar(self):
        """Consulta a RBTIntervalos e popula a tabela."""
        from datetime import date as _date

        if not self.biblioteca.rbt_intervalos:
            return

        qi = self.date_inicio.date()
        qf = self.date_fim.date()
        inicio = _date(qi.year(), qi.month(), qi.day())
        fim    = _date(qf.year(),  qf.month(),  qf.day())

        resultados, _, _ = self.biblioteca.rbt_intervalos.buscar_todos_sobrepostos(
            inicio, fim
        )

        self.tabela.setRowCount(0)
        for emp in resultados:
            row = self.tabela.rowCount()
            self.tabela.insertRow(row)

            aluno_info = emp.get("aluno", {})
            nome_aluno = aluno_info.get("nome", "?") if isinstance(aluno_info, dict) else str(aluno_info)

            for col, valor in enumerate([
                emp.get("chave", "?"),
                nome_aluno,
                emp.get("livro", "?"),
                emp.get("inicio", "?"),
                emp.get("devolucao", "?"),
            ]):
                item = QTableWidgetItem(str(valor))
                item.setForeground(Qt.white)
                self.tabela.setItem(row, col, item)


class JanelaDevolucao(QDialog):
    def __init__(self, biblioteca: Biblioteca, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setStyleSheet("""
            QDialog, QWidget {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QSpinBox {
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(173, 73, 225, 0.3);
                border-radius: 6px;
                padding: 7px 12px;
                color: #e0e0e0;
            }
            QPushButton {
                background: rgba(173, 73, 225, 0.2);
                border: 1px solid rgba(173, 73, 225, 0.4);
                border-radius: 6px;
                padding: 8px 18px;
                color: #e0e0e0;
            }
            QPushButton:hover {
                background: rgba(173, 73, 225, 0.35);
            }
        """)
        self.setWindowTitle("Devolução")
        self.setMinimumSize(600, 350)

        layoutdv = QFormLayout()
        self.setLayout(layoutdv)

        self.chave = QSpinBox()
        self.chave.setRange(0, 9999999)
        layoutdv.addRow("Chave da Devolução:", self.chave)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layoutdv.addWidget(b_box)

        self.biblioteca = biblioteca
        b_box.accepted.connect(self.faz_slot(biblioteca.fazer_devolucao))
        b_box.rejected.connect(self.reject)

    def faz_slot(self, func):
        def slot():
            chave_value = self.chave.value()
            emprestimo = self.biblioteca.emprestimos.get(str(chave_value))
            livro_titulo = ""
            livro_id = None

            if isinstance(emprestimo, dict):
                livro_titulo = emprestimo.get("livro", "")
                for numeracao, livro in self.biblioteca.info_livros.items():
                    if isinstance(livro, dict) and livro.get("titulo", "").lower() == str(livro_titulo).lower():
                        livro_id = numeracao
                        break

            try:
                func(str(chave_value))
                self.chave.clear()

                if livro_id and self._perguntar_avaliacao(livro_titulo):
                    nota = self._abrir_janela_avaliacao(livro_titulo)
                    if nota is not None:
                        try:
                            self.biblioteca.avaliar_livro(livro_id, nota)
                            faz_msg_box("Avaliação registrada!", f"Você avaliou '{livro_titulo}' com {nota} estrelas.", False)
                        except ValueError as e:
                            faz_msg_box("Erro", str(e), True)

                faz_msg_box("Devolução Realizada!", "Devolução bem sucedida.", False)
                self.accept()
            except KeyError:
                faz_msg_box("Falha!", "Devolução mal sucedida.\nERRO: CHAVE NÃO ENCONTRADA", True)
        return slot

    def _perguntar_avaliacao(self, livro_titulo: str) -> bool:
        pergunta = QMessageBox(self)
        pergunta.setWindowTitle("Avaliação do Livro")
        pergunta.setText(f"Deseja avaliar este livro?\n{livro_titulo}")
        pergunta.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        pergunta.setDefaultButton(QMessageBox.Yes)
        return pergunta.exec() == QMessageBox.Yes

    def _abrir_janela_avaliacao(self, livro_titulo: str) -> float | None:
        dialog = QDialog(self)
        dialog.setWindowTitle("Avaliar Livro")
        dialog.setMinimumSize(360, 180)
        dialog.setStyleSheet(self.styleSheet())

        layout = QFormLayout(dialog)
        label = QLabel(f"Avalie '{livro_titulo}' (0-5 estrelas)")
        layout.addRow(label)

        nota_spin = QDoubleSpinBox()
        nota_spin.setRange(0.0, 5.0)
        nota_spin.setSingleStep(0.1)
        nota_spin.setValue(5.0)
        nota_spin.setDecimals(1)
        layout.addRow("Nota (estrelas):", nota_spin)

        b_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        b_box.accepted.connect(dialog.accept)
        b_box.rejected.connect(dialog.reject)
        layout.addWidget(b_box)

        if dialog.exec() == QDialog.Accepted:
            return float(nota_spin.value())
        return None

if __name__ == "__main__":
    app = QApplication(sys.argv)

    janelaCentral = JanelaPrincipal()

    janelaCentral.show()
    sys.exit(app.exec())  