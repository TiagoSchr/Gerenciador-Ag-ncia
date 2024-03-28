from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QDateEdit, QTextEdit, QCheckBox, QMessageBox, QGridLayout, QTableView
from PySide6.QtCore import QDate
from PySide6.QtSql import QSqlDatabase, QSqlQuery, QSqlQueryModel
from mysql.connector import Error
from PySide6.QtGui import QStandardItemModel, QStandardItem
import mysql.connector
import sys

class AgencyManagerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerenciador da Agência")
        self.setGeometry(100, 100, 1000, 600)
        self.conexao = self.conectar_bd()
        self.setupUI()
        self.exibir_clientes()

    def conectar_bd(self):
        """Conecta ao banco de dados MySQL usando mysql.connector."""
        try:
            conexao = mysql.connector.connect(
                host="seu ip localhost",
                user="nome do user do banco de dados",
                password="senha",
                database="nome do banco  de dados"
            )
            if conexao.is_connected():
                return conexao
            else:
                QMessageBox.critical(self, "Erro ao conectar ao banco de dados",
                                     "Não foi possível conectar ao banco de dados.")
                sys.exit(1)
        except Error as e:
            QMessageBox.critical(self, "Erro ao conectar ao MySQL", f"Erro: {e}")
            sys.exit(1)
   
    def setupUI(self):
        """Configura a interface do usuário."""
        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)
        mainLayout = QVBoxLayout(centralWidget)
        gridLayout = QGridLayout()
        mainLayout.addLayout(gridLayout)

        # Labels e Campos de Entrada
        labels_texts = ["Data", "Cliente", "Tipo de Serviço", "Dia de Pagamento", "Observações", "Valor (R$)", "Pago"]
        for i, text in enumerate(labels_texts):
            gridLayout.addWidget(QLabel(text), i, 0)

        self.dataEdit = QDateEdit()
        self.dataEdit.setDate(QDate.currentDate())
        gridLayout.addWidget(self.dataEdit, 0, 1)

        self.clienteEdit = QLineEdit()
        gridLayout.addWidget(self.clienteEdit, 1, 1)

        self.tipoServicoEdit = QLineEdit()
        gridLayout.addWidget(self.tipoServicoEdit, 2, 1)

        self.diaPagamentoEdit = QDateEdit()
        self.diaPagamentoEdit.setDate(QDate.currentDate())
        self.diaPagamentoEdit.setCalendarPopup(True)
        gridLayout.addWidget(self.diaPagamentoEdit, 3, 1)

        self.observacoesEdit = QTextEdit()
        gridLayout.addWidget(self.observacoesEdit, 4, 1)

        self.valorEdit = QLineEdit()
        gridLayout.addWidget(self.valorEdit, 5, 1)

        self.pagoCheck = QCheckBox()
        gridLayout.addWidget(self.pagoCheck, 6, 1)

        # Botões
        self.addButton = QPushButton("Adicionar")
        self.addButton.clicked.connect(self.adicionar_cliente)
        mainLayout.addWidget(self.addButton)

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Digite para pesquisar clientes...")
        self.searchEdit.textChanged.connect(self.exibir_clientes)
        mainLayout.addWidget(self.searchEdit)

        self.deleteButton = QPushButton("Excluir")
        self.deleteButton.clicked.connect(self.excluir_cliente_selecionado)
        mainLayout.addWidget(self.deleteButton)

        self.clientesTableView = QTableView()
        self.clientesModel = QSqlQueryModel()
        self.clientesTableView.setModel(self.clientesModel)
        self.clientesTableView.clicked.connect(self.item_selecionado)
        mainLayout.addWidget(self.clientesTableView)
        self.clientesTableView.clicked.connect(self.item_selecionado)
        
   
    def adicionar_cliente(self):
        """Adiciona um novo cliente ao banco de dados usando mysql.connector."""
        cliente_nome = self.clienteEdit.text()
        tipo_servico = self.tipoServicoEdit.text()
        observacoes = self.observacoesEdit.toPlainText()
        valor_texto = self.valorEdit.text()
        pago = 'Sim' if self.pagoCheck.isChecked() else 'Não'
        data_servico = self.dataEdit.date().toString("yyyy-MM-dd")
        dia_pagamento = self.diaPagamentoEdit.date().toString("yyyy-MM-dd")

        if not cliente_nome or not tipo_servico or not valor_texto:
            QMessageBox.warning(self, "Dados incompletos", "Por favor, preencha todos os campos obrigatórios.")
            return

        try:
            valor = float(valor_texto)
        except ValueError:
            QMessageBox.critical(self, "Erro ao adicionar cliente", "Valor inválido. Por favor, insira um número decimal para o valor.")
            return

        try:
            cursor = self.conexao.cursor(buffered=True)
            # Inserindo o serviço diretamente sem verificar por duplicatas
            cursor.execute("INSERT INTO Clientes (nome) VALUES (%s)", (cliente_nome,))
            cliente_id = cursor.lastrowid


            cursor.execute("INSERT INTO Servicos (tipo_servico) VALUES (%s)", (tipo_servico,))
            servico_id = cursor.lastrowid

            # Insira a nova ordem de serviço
            query_ordem_servico = """
                INSERT INTO OrdensDeServico (cliente_id, servico_id, data, observacoes, valor, pago, dia_pagamento) 
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_ordem_servico, (cliente_id, servico_id, data_servico, observacoes, valor, pago, dia_pagamento))
            self.conexao.commit()
            QMessageBox.information(self, "Sucesso", "Cliente adicionado com sucesso!")
        except Error as e:
            self.conexao.rollback()
            QMessageBox.critical(self, "Erro ao adicionar cliente", f"Erro: {e}")
        finally:
            cursor.close()

        self.exibir_clientes()  # Atualizar a exibição dos clientes
        self.limpar_campos()

    def limpar_campos(self):
        """Limpa os campos de entrada após adição."""
        self.clienteEdit.clear()
        self.tipoServicoEdit.clear()
        self.observacoesEdit.clear()
        self.valorEdit.clear()
        self.pagoCheck.setChecked(False)


    def exibir_clientes(self):
        """Exibe as ordens de serviço no QTableView, incluindo o cliente_id de forma oculta."""
        termo_pesquisa = '%' + self.searchEdit.text() + '%'
        query = """
        SELECT c.cliente_id, c.nome, s.tipo_servico, o.valor, o.pago, o.observacoes, o.data, o.dia_pagamento
        FROM OrdensDeServico o
        INNER JOIN Clientes c ON o.cliente_id = c.cliente_id
        INNER JOIN Servicos s ON o.servico_id = s.servico_id
        WHERE c.nome LIKE %s OR s.tipo_servico LIKE %s;
        """
        try:
            cursor = self.conexao.cursor()
            cursor.execute(query, (termo_pesquisa, termo_pesquisa))
            results = cursor.fetchall()

            self.model = QStandardItemModel()
            self.model.setHorizontalHeaderLabels([
                'ID', 'Nome', 'Tipo de Serviço', 'Valor', 'Pago', 'Observações', 'Data', 'Dia de Pagamento'
            ])

            for row_data in results:
                row = [QStandardItem(str(field)) for field in row_data]
                self.model.appendRow(row)

            # Oculta a coluna de ID para que não seja visível, mas ainda acessível
            self.clientesTableView.setModel(self.model)
            self.clientesTableView.setColumnHidden(0, True)
            self.clientesTableView.resizeColumnsToContents()
        except Error as e:
            QMessageBox.critical(self, "Erro ao buscar ordens de serviço", f"Erro na execução da consulta: {e}")
        finally:
            cursor.close()


    def item_selecionado(self, index):
    # O ID do cliente está na primeira coluna (índice 0, que é o nome do cliente)
        cliente_id_index = index.siblingAtColumn(0)
        if cliente_id_index.isValid():
            self.selected_cliente_id = cliente_id_index.data()
        else:
            QMessageBox.critical(self, "Erro de seleção", "Não foi possível obter o ID do cliente.")
            self.selected_cliente_id = None
    
    def excluir_cliente_selecionado(self):
        if self.selected_cliente_id is None:
            QMessageBox.warning(self, "Nenhum cliente selecionado", "Por favor, selecione um cliente para excluir.")
            return

        resposta = QMessageBox.question(self, "Confirmar exclusão", "Você tem certeza que deseja excluir o cliente selecionado e todas as suas ordens de serviço?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if resposta == QMessageBox.Yes:
            try:
                cursor = self.conexao.cursor()
                cliente_id = self.selected_cliente_id

                # Excluir ordens de serviço associadas ao cliente
                cursor.execute("DELETE FROM OrdensDeServico WHERE cliente_id = %s", (cliente_id,))

                # Excluir o cliente
                cursor.execute("DELETE FROM Clientes WHERE cliente_id = %s", (cliente_id,))
                self.conexao.commit()

                QMessageBox.information(self, "Sucesso", "Cliente e todas as ordens de serviço vinculadas foram excluídas com sucesso.")
            except Error as e:
                self.conexao.rollback()
                QMessageBox.critical(self, "Erro ao excluir cliente", f"Erro: {e}")
            finally:
                cursor.close()

            # Atualiza a visualização da lista de clientes após a exclusão
            self.selected_cliente_id = None
            self.exibir_clientes()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AgencyManagerApp()
    window.show()
    sys.exit(app.exec())
