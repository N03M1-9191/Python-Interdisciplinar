# Classes de dados do Organizador de tarefas.

from datetime import datetime


def data_iso_para_br(texto):
    # Converte aaaa-mm-dd para dd/mm/aaaa.
    return datetime.strptime(texto, '%Y-%m-%d').strftime('%d/%m/%Y')


class Usuario:
    # Representa o usuário que fez login.


    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email


class Tarefa:
    # Representa uma tarefa lida do banco de dados.


    def __init__(self, id, titulo, descricao, data_iso, prioridade,
                 status, disciplina):
        self.id = id
        self.titulo = titulo
        self.descricao = descricao
        self.data_iso = data_iso
        self.prioridade = prioridade
        self.status = status
        self.disciplina = disciplina


    def dataBR(self):
        # Devolve a data no formato dd/mm/aaaa.
        return data_iso_para_br(self.data_iso)


    def esta_concluida(self):
        # Retorna True se a tarefa já foi concluída.
        return self.status == 'Concluída'


    def rotulo(self):
        # Texto exibido na Listbox.
        return (f'{self.dataBR()} | {self.titulo} | '
                f'{self.disciplina} | {self.descricao}')


    def rotulo_curto(self):
        # Texto exibido nas caixas de seleção.
        return f'{self.titulo} ({self.dataBR()})'


class Flashcard:
    # Representa um flashcard (pergunta na frente, resposta atrás).


    def __init__(self, id, pergunta, resposta, disciplina):
        self.id = id
        self.pergunta = pergunta
        self.resposta = resposta
        self.disciplina = disciplina
