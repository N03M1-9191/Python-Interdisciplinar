# Funções auxiliares, configurações e acesso ao banco SQLite.

import os
import sqlite3
from tkinter import Label, Entry
from datetime import datetime
from tkinter import ttk
from tkinter.messagebox import askyesno, showerror, showinfo

from classes import Usuario, Tarefa, Flashcard, data_iso_para_br


# Pasta do projeto no celular (Pydroid). Em outro computador, usa a
# pasta atual. O banco e o relatório são gravados nessa pasta.
pasta_projeto = '/storage/emulated/0/Documents/Projeto_Python'
pasta = pasta_projeto if os.path.isdir(pasta_projeto) else os.getcwd()

arquivo_banco = os.path.join(pasta, 'organizador.db')
arquivo_relatorio = os.path.join(pasta, 'relatorio_tarefas.txt')

prioridades = ['Baixa', 'Média', 'Alta']
dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']

fonte_titulo = ('Arial', 16, 'bold')
fonte_subtitulo = ('Arial', 11)
fonte_negrito = ('Arial', 10, 'bold')


def dataBR(texto):
    # Converte dd/mm/aaaa para aaaa-mm-dd (formato que ordena certo).
    try:
        data = datetime.strptime(texto.strip(), '%d/%m/%Y')
    except ValueError:
        raise ValueError('Data inválida.')
    return data.strftime('%Y-%m-%d')



# ----- operações com o banco de dados -----

class BancoDados:
    # Concentra todos os comandos SQL do sistema.


    def __init__(self, arquivo=arquivo_banco):
        self.arquivo = arquivo


    # ----- infraestrutura -----------------------------------------


    def _conectar(self):
        # Abre a conexão e ativa as chaves estrangeiras.
        conexao = sqlite3.connect(self.arquivo)
        conexao.execute('PRAGMA foreign_keys = ON')
        return conexao


    def _executar(self, comando, parametros=()):
        # Executa INSERT, UPDATE ou DELETE e confirma (commit).
        conexao = self._conectar()
        try:
            cursor = conexao.execute(comando, parametros)
            conexao.commit()
            return cursor.lastrowid
        finally:
            conexao.close()


    def _consultar(self, comando, parametros=()):
        # Executa um SELECT e devolve todas as linhas.
        conexao = self._conectar()
        try:
            return conexao.execute(comando, parametros).fetchall()
        finally:
            conexao.close()


    def criar_tabelas(self):
        # Cria as tabelas, caso ainda não existam.
        conexao = self._conectar()
        try:
            conexao.executescript("""
            CREATE TABLE IF NOT EXISTS usuario (
                id    INTEGER PRIMARY KEY AUTOINCREMENT,
                nome  TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                senha TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS disciplina (
                id   INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tarefa (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo        TEXT NOT NULL,
                descricao     TEXT NOT NULL,
                data_prazo    TEXT NOT NULL,
                prioridade    TEXT NOT NULL
                    CHECK (prioridade IN ('Baixa', 'Média', 'Alta')),
                status        TEXT NOT NULL DEFAULT 'Pendente'
                    CHECK (status IN ('Pendente', 'Concluída')),
                usuario_id    INTEGER NOT NULL,
                disciplina_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuario (id),
                FOREIGN KEY (disciplina_id) REFERENCES disciplina (id)
            );

            CREATE TABLE IF NOT EXISTS flashcard (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                pergunta      TEXT NOT NULL,
                resposta      TEXT NOT NULL,
                usuario_id    INTEGER NOT NULL,
                disciplina_id INTEGER NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuario (id),
                FOREIGN KEY (disciplina_id) REFERENCES disciplina (id)
            );

            CREATE TABLE IF NOT EXISTS grade (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                horario    TEXT NOT NULL,
                dia        INTEGER NOT NULL CHECK (dia BETWEEN 0 AND 6),
                materia    TEXT NOT NULL,
                FOREIGN KEY (usuario_id) REFERENCES usuario (id)
            );
            """)
            conexao.commit()
        finally:
            conexao.close()


    def _garantir_disciplina(self, conexao, nome):
        # Cria a disciplina se ela não existir e devolve o id dela.
        conexao.execute(
            'INSERT OR IGNORE INTO disciplina (nome) VALUES (?)', (nome,))
        linha = conexao.execute(
            'SELECT id FROM disciplina WHERE nome = ?', (nome,)).fetchone()
        return linha[0]


    # ----- usuários -----------------------------------------------


    def cadastrar_usuario(self, nome, email, senha):
        # Insere um novo usuário (a senha é guardada no banco)..
        try:
            return self._executar(
                'INSERT INTO usuario (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email.lower(), senha))
        except sqlite3.IntegrityError:
            raise ValueError('Já existe um cadastro com esse e-mail.')


    def autenticar(self, login, senha):
        # Confere nome/e-mail e senha. Devolve Usuario ou None.
        linhas = self._consultar(
            'SELECT id, nome, email, senha FROM usuario '
            'WHERE email = ? OR nome = ?', (login.lower(), login))
        for id_usuario, nome, email, senha_guardada in linhas:
            if senha == senha_guardada:
                return Usuario(id_usuario, nome, email)
        return None


    # ----- tarefas (CRUD) -----------------------------------------


    def adicionar_tarefa(self, usuario_id, titulo, descricao, data_iso,
                         prioridade, disciplina):
        # INSERT: cadastra uma tarefa.
        conexao = self._conectar()
        try:
            id_disciplina = self._garantir_disciplina(conexao, disciplina)
            conexao.execute(
                'INSERT INTO tarefa (titulo, descricao, data_prazo, '
                'prioridade, usuario_id, disciplina_id) '
                'VALUES (?, ?, ?, ?, ?, ?)',
                (titulo, descricao, data_iso, prioridade, usuario_id,
                 id_disciplina))
            conexao.commit()
        finally:
            conexao.close()


    def listar_tarefas(self, usuario_id, prioridade=None, status=None):
        # SELECT com JOIN: lista tarefas e permite filtrar por prioridade
        # e status.
        comando = (
            'SELECT t.id, t.titulo, t.descricao, t.data_prazo, '
            't.prioridade, t.status, d.nome '
            'FROM tarefa t INNER JOIN disciplina d '
            'ON d.id = t.disciplina_id WHERE t.usuario_id = ?')
        parametros = [usuario_id]

        if prioridade is not None:
            comando += ' AND t.prioridade = ?'
            parametros.append(prioridade)

        if status is not None:
            comando += ' AND t.status = ?'
            parametros.append(status)

        comando += ' ORDER BY t.data_prazo DESC, t.id DESC'

        linhas = self._consultar(comando, tuple(parametros))
        return [Tarefa(*linha) for linha in linhas]


    def resumo(self, usuario_id):
        # Devolve (total de tarefas, total de concluídas).
        linha = self._consultar(
            "SELECT COUNT(*), "
            "COALESCE(SUM(CASE WHEN status = 'Concluída' THEN 1 ELSE 0 END), 0) "
            "FROM tarefa WHERE usuario_id = ?", (usuario_id,))[0]
        return linha[0], linha[1]


    def concluir_tarefa(self, tarefa_id, usuario_id):
        # UPDATE: marca a tarefa como concluída.
        self._executar(
            "UPDATE tarefa SET status = 'Concluída' "
            'WHERE id = ? AND usuario_id = ?', (tarefa_id, usuario_id))


    def editar_descricao(self, tarefa_id, usuario_id, nova_descricao):
        # UPDATE: altera a descrição da tarefa.
        self._executar(
            'UPDATE tarefa SET descricao = ? '
            'WHERE id = ? AND usuario_id = ?',
            (nova_descricao, tarefa_id, usuario_id))


    def remover_tarefa(self, tarefa_id, usuario_id):
        # DELETE: remove a tarefa.
        self._executar(
            'DELETE FROM tarefa WHERE id = ? AND usuario_id = ?',
            (tarefa_id, usuario_id))


    # ----- flashcards ---------------------------------------------


    def adicionar_flashcard(self, usuario_id, pergunta, resposta,
                            disciplina):
        # INSERT: cadastra um flashcard.
        conexao = self._conectar()
        try:
            id_disciplina = self._garantir_disciplina(conexao, disciplina)
            conexao.execute(
                'INSERT INTO flashcard (pergunta, resposta, usuario_id, '
                'disciplina_id) VALUES (?, ?, ?, ?)',
                (pergunta, resposta, usuario_id, id_disciplina))
            conexao.commit()
        finally:
            conexao.close()


    def listar_flashcards(self, usuario_id):
        # SELECT com JOIN: flashcards do usuário.
        linhas = self._consultar(
            'SELECT f.id, f.pergunta, f.resposta, d.nome '
            'FROM flashcard f INNER JOIN disciplina d '
            'ON d.id = f.disciplina_id WHERE f.usuario_id = ? '
            'ORDER BY f.id', (usuario_id,))
        return [Flashcard(*linha) for linha in linhas]


    # ----- grade de estudos (matriz) ------------------------------


    def carregar_grade(self, usuario_id):
        # Monta a matriz da grade: 1ª linha = dias, demais = horários.
        matriz = [['Horário'] + dias_semana]
        linhas = self._consultar(
            'SELECT horario, dia, materia FROM grade '
            'WHERE usuario_id = ? ORDER BY id', (usuario_id,))

        posicao = {}   # horário -> índice da linha na matriz
        for horario, dia, materia in linhas:
            if horario not in posicao:
                matriz.append([horario] + [''] * len(dias_semana))
                posicao[horario] = len(matriz) - 1
            matriz[posicao[horario]][dia + 1] = materia
        return matriz


    def salvar_grade(self, usuario_id, matriz):
        # Apaga a grade antiga do usuário e grava a matriz atual.
        conexao = self._conectar()
        try:
            conexao.execute('DELETE FROM grade WHERE usuario_id = ?',
                            (usuario_id,))
            for linha in matriz[1:]:
                for dia in range(len(dias_semana)):
                    conexao.execute(
                        'INSERT INTO grade (usuario_id, horario, dia, '
                        'materia) VALUES (?, ?, ?, ?)',
                        (usuario_id, linha[0], dia, linha[dia + 1]))
            conexao.commit()
        finally:
            conexao.close()


# ---------------------------------------------------------------
# 4. INTERFACE (tkinter)
# ---------------------------------------------------------------

def criarCampo(quadro, linha, texto, senha=False):
    # Cria um rótulo + campo de texto na linha indicada (grid).
    Label(
        quadro,
        text=texto,
        anchor='w'
    ).grid(row=linha, column=0, padx=5, pady=5, sticky='w')
    entrada = Entry(
        quadro,
        width=24,
        show='*' if senha else ''
    )
    entrada.grid(row=linha, column=1, padx=5, pady=5)
    return entrada


def criarSelecao(quadro, linha, texto, valores, somente_leitura=True):
    # Cria um rótulo + caixa de seleção (Combobox) na linha indicada.
    Label(
        quadro,
        text=texto,
        anchor='w'
    ).grid(row=linha, column=0, padx=5, pady=5, sticky='w')
    combo = ttk.Combobox(
        quadro,
        values=valores,
        width=22,
        state='readonly' if somente_leitura else 'normal'
    )
    combo.grid(row=linha, column=1, padx=5, pady=5)
    return combo
