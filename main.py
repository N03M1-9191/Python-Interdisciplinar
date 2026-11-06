# Programa principal: interface gráfica do Organizador de tarefas.
import random
import re
import sqlite3
from tkinter import (
    Tk, Toplevel, Label, Frame, Button, Entry, Listbox, Scrollbar, Text
)
from datetime import datetime
from tkinter import ttk
from tkinter.messagebox import askyesno, showerror, showinfo
from classes import Usuario
from funcoes import (
    BancoDados, dias_semana, fonte_negrito, fonte_subtitulo,
    fonte_titulo, pasta, arquivo_relatorio, prioridades,
    criarCampo, criarSelecao, dataBR
)


class Interface(Tk):
    # Janela principal e todas as telas do Organizador de tarefas.

    def __init__(self):
        super().__init__()
        self.title('Organizador de tarefas')
        self.usuario = None
        self.janela_menu = None
        self.banco = BancoDados()
        try:
            self.banco.criar_tabelas()
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))
        Label(
            self,
            text='Organizador de tarefas',
            font=fonte_titulo
        ).pack(padx=20, pady=(30, 20))
        quadro = Frame(
            self
        )
        quadro.pack(pady=10)
        self.botaoCadastrar = Button(
            quadro,
            text='Cadastrar',
            width=9,
            command=self.abrirCadastro
        )
        self.botaoMenu = Button(
            quadro,
            text='Menu',
            width=9,
            command=self.abrirMenu
        )
        self.botaoLogin = Button(
            quadro,
            text='Login',
            width=9,
            command=self.abrirLogin
        )
        self.botaoCadastrar.grid(row=0, column=0, padx=5)
        self.botaoMenu.grid(row=0, column=1, padx=5)
        self.botaoLogin.grid(row=0, column=2, padx=5)
        self.botaoMenu.grid_remove()



    # ----- cadastro e acesso de usuários -----



    def abrirCadastro(self):
        # Abre a janela de cadastro de usuário.
        janela = Toplevel(self)
        janela.title('Cadastro')
        Label(
            janela,
            text='Cadastre-se:',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=15)
        campoNome = criarCampo(quadro, 0, 'Nome:')
        campoEmail = criarCampo(quadro, 1, 'Email:')
        campoSenha = criarCampo(quadro, 2, 'Senha:', senha=True)
        Button(
            janela,
            text='Cadastrar',
            command=lambda: self.confirmarCadastro(
                janela, campoNome, campoEmail, campoSenha
            )
        ).pack(pady=15)



    def confirmarCadastro(self, janela, campoNome, campoEmail, campoSenha):
        # Valida os dados e grava o usuário no banco.
        try:
            nome = campoNome.get().strip()
            email = campoEmail.get().strip()
            senha = campoSenha.get()
            if not nome:
                raise ValueError('Informe o nome.')
            if any((caractere.isdigit() for caractere in nome)):
                raise ValueError('O nome não pode conter números.')
            if not re.match('^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$', email):
                raise ValueError('Informe um e-mail válido.')
            if len(senha) < 4:
                raise ValueError('A senha deve ter pelo menos 4 caracteres.')
            id_usuario = self.banco.cadastrar_usuario(nome, email, senha)
            showinfo('Cadastro', 'Cadastro realizado com sucesso!', parent=janela)
            self.entrarSistema(Usuario(id_usuario, nome, email.lower()))
            janela.destroy()
        except ValueError as erro:
            showerror('Dados inválidos', str(erro))
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def abrirLogin(self):
        # Abre a janela de login.
        janela = Toplevel(self)
        janela.title('Login')
        Label(
            janela,
            text='Faça o Login:',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=15)
        campoLogin = criarCampo(quadro, 0, 'Nome/email:')
        campoSenha = criarCampo(quadro, 1, 'Senha:', senha=True)
        Button(
            janela,
            text='Login',
            command=lambda: self.confirmarLogin(
                janela, campoLogin, campoSenha
            )
        ).pack(pady=15)



    def confirmarLogin(self, janela, campoLogin, campoSenha):
        # Confere os dados digitados com o banco.
        try:
            login = campoLogin.get().strip()
            senha = campoSenha.get()
            if not login or not senha:
                raise ValueError('Preencha o nome/e-mail e a senha.')
            usuario = self.banco.autenticar(login, senha)
            if usuario is None:
                raise ValueError('Nome/e-mail ou senha incorretos.')
            self.entrarSistema(usuario)
            janela.destroy()
        except ValueError as erro:
            showerror('Dados inválidos', str(erro))
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def entrarSistema(self, usuario):
        # Guarda o usuário logado, mostra o botão Menu e abre o menu.
        self.usuario = usuario
        self.botaoMenu.grid()
        self.abrirMenu()



    def abrirMenu(self):
        # Abre o menu com as 8 opções.
        if self.usuario is None:
            return
        if self.janela_menu is not None and self.janela_menu.winfo_exists():
            self.janela_menu.destroy()
        janela = Toplevel(self)
        janela.title('Menu')
        self.janela_menu = janela
        Label(
            janela,
            text='Menu',
            font=fonte_titulo
        ).pack(padx=20, pady=(15, 0))
        Label(
            janela,
            text=f'Bem vindo, {self.usuario.nome}!',
            font=fonte_subtitulo
        ).pack(pady=(0, 10))
        opcoes = [
            ('Adicionar', self.abrirAdicionar),
            ('Listar', self.abrirListar),
            ('Marcar como concluída', self.abrirConcluir),
            ('Editar tarefa', self.abrirEditar),
            ('Remover tarefa', self.abrirRemover),
            ('Flashcards', self.abrirFlashcards),
            ('Preencher grade', lambda: self.abrirGrade(True)),
            ('Exibir grade', lambda: self.abrirGrade(False))
        ]
        for texto, comando in opcoes:
            Button(
                janela,
                text=texto,
                width=24,
                command=comando
            ).pack(padx=20, pady=3)
        Label(
            janela,
            text=''
        ).pack()



    # ----- gerenciamento de tarefas -----



    def abrirAdicionar(self):
        # Janela para cadastrar uma nova tarefa.
        janela = Toplevel(self)
        janela.title('Adicionar tarefa')
        Label(
            janela,
            text='Adicione uma nova tarefa:',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=15)
        campoNome = criarCampo(quadro, 0, 'Nome:')
        campoDisciplina = criarCampo(quadro, 1, 'Disciplina:')
        campoData = criarCampo(quadro, 2, 'Data:')
        campoDescricao = criarCampo(quadro, 3, 'Descrição:')
        campoPrioridade = criarSelecao(quadro, 4, 'Prioridade:', prioridades)
        campoPrioridade.set('Média')
        Button(
            janela,
            text='Adicionar',
            command=lambda: self.salvarTarefa(
                campoNome, campoDisciplina, campoData,
                campoDescricao, campoPrioridade
            )
        ).pack(pady=15)



    def salvarTarefa(self, campoNome, campoDisciplina, campoData, campoDescricao, campoPrioridade):
        # Valida os campos e insere a tarefa no banco.
        try:
            nome = campoNome.get().strip()
            disciplina = campoDisciplina.get().strip()
            descricao = campoDescricao.get().strip()
            prioridade = campoPrioridade.get()
            if not nome or not disciplina or (not descricao):
                raise ValueError('Preencha nome, disciplina e descrição.')
            if prioridade not in prioridades:
                raise ValueError('Escolha a prioridade.')
            data_iso = dataBR(campoData.get())
            self.banco.adicionar_tarefa(
                self.usuario.id, nome, descricao, data_iso,
                prioridade, disciplina
            )
            showinfo('Tarefa', 'Tarefa adicionada com sucesso!')
            for campo in (campoNome, campoData, campoDescricao):
                campo.delete(0, 'end')
            campoDisciplina.delete(0, 'end')
        except ValueError as erro:
            showerror('Dados inválidos', str(erro))
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def abrirListar(self):
        # Janela com filtro, lista, resumo e botão de relatório.
        id_usuario = self.usuario.id
        janela = Toplevel(self)
        janela.title('Tarefas')
        Label(
            janela,
            text='Tarefas',
            font=fonte_titulo
        ).pack(padx=20, pady=8)
        quadro_filtros = Frame(
            janela
        )
        quadro_filtros.pack(pady=4)
        Label(
            quadro_filtros,
            text='Prioridade:'
        ).pack(side='left', padx=4)
        filtro = ttk.Combobox(
            quadro_filtros,
            values=['Todas'] + prioridades,
            state='readonly',
            width=12
        )
        filtro.set('Todas')
        filtro.pack(side='left', padx=4)
        Label(
            quadro_filtros,
            text='Status:'
        ).pack(side='left', padx=4)
        filtro_status = ttk.Combobox(
            quadro_filtros,
            values=['Todos', 'Pendente', 'Concluída'],
            state='readonly',
            width=12
        )
        filtro_status.set('Todos')
        filtro_status.pack(side='left', padx=4)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=10, pady=5, fill='both', expand=True)
        lista = Listbox(
            quadro,
            width=60,
            height=10
        )
        barra = Scrollbar(
            quadro,
            orient='vertical',
            command=lista.yview
        )
        barra_horizontal = Scrollbar(
            janela,
            orient='horizontal',
            command=lista.xview
        )
        lista.configure(yscrollcommand=barra.set, xscrollcommand=barra_horizontal.set)
        lista.pack(side='left', fill='both', expand=True)
        barra.pack(side='right', fill='y')
        barra_horizontal.pack(fill='x', padx=10)
        resumo = Label(
            janela,
            text='',
            justify='left',
            font=fonte_negrito
        )
        resumo.pack(pady=6)
        Button(
            janela,
            text='Gerar relatório',
            command=self.gerarRelatorio
        ).pack(pady=8)

        def atualizar(evento=None):
            try:
                escolha = filtro.get()
                prioridade = None if escolha == 'Todas' else escolha
                escolha_status = filtro_status.get()
                status = None if escolha_status == 'Todos' else escolha_status
                tarefas = self.banco.listar_tarefas(id_usuario, prioridade, status)
                lista.delete(0, 'end')
                for tarefa in tarefas:
                    lista.insert('end', tarefa.rotulo())
                if not tarefas:
                    lista.insert('end', 'Nenhuma tarefa encontrada.')
                total, concluidas = self.banco.resumo(id_usuario)
                porcentagem = concluidas / total * 100 if total else 0
                resumo.config(text=f'Resumo geral: {total} tarefa(s)\nConcluídas: {concluidas} | Pendentes: {total - concluidas}\nPorcentagem concluída: {porcentagem:.1f}%')
            except sqlite3.Error as erro:
                showerror('Erro no banco de dados', str(erro))
        filtro.bind('<<ComboboxSelected>>', atualizar)
        filtro_status.bind('<<ComboboxSelected>>', atualizar)
        atualizar()



    def montarRelatorio(self):
        # Monta o texto do relatório com todas as tarefas do usuário.
        id_usuario = self.usuario.id
        tarefas = self.banco.listar_tarefas(id_usuario)
        total, concluidas = self.banco.resumo(id_usuario)
        porcentagem = concluidas / total * 100 if total else 0
        linha = '=' * 40
        traco = '-' * 40
        texto = [linha, '        RELATÓRIO DE TAREFAS', linha, '', f"Data de emissão: {datetime.now().strftime('%d/%m/%Y')}", f'Usuário: {self.usuario.nome}', '']
        for numero, tarefa in enumerate(tarefas, start=1):
            texto += [traco, f'TAREFA {numero}', f'Título: {tarefa.titulo}', f'Descrição: {tarefa.descricao}', f'Disciplina: {tarefa.disciplina}', f'Data: {tarefa.dataBR()}', f'Prioridade: {tarefa.prioridade}', f'Status: {tarefa.status}', '']
        texto += [linha, f'Total de tarefas: {total}', f'Concluídas: {concluidas}', f'Pendentes: {total - concluidas}', f'Porcentagem concluída: {porcentagem:.1f}%', linha, 'Fim do relatório']
        return '\n'.join(texto)



    def gerarRelatorio(self):
        # Abre a janela do relatório (com botão para salvar em TXT).
        relatorio = self.montarRelatorio()
        janela = Toplevel(self)
        janela.title('Relatório')
        Label(
            janela,
            text='Relatório de tarefas',
            font=fonte_titulo
        ).pack(padx=20, pady=8)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=10, pady=5, fill='both', expand=True)
        caixa = Text(
            quadro,
            width=44,
            height=16,
            wrap='word'
        )
        barra = Scrollbar(
            quadro,
            orient='vertical',
            command=caixa.yview
        )
        caixa.configure(yscrollcommand=barra.set)
        caixa.pack(side='left', fill='both', expand=True)
        barra.pack(side='right', fill='y')
        caixa.insert('end', relatorio)
        caixa.config(state='disabled')
        Button(
            janela,
            text='Salvar relatório em TXT',
            command=lambda: self.salvar_relatorio(relatorio)
        ).pack(pady=10)



    def salvar_relatorio(self, relatorio):
        # Grava o relatório em um arquivo de texto.
        try:
            with open(arquivo_relatorio, 'w', encoding='utf-8') as arquivo:
                arquivo.write(relatorio)
            showinfo('Relatório', f'Relatório salvo em:\n{arquivo_relatorio}')
        except OSError as erro:
            showerror('Erro de arquivo', str(erro))



    def selecionarTarefa(self, titulo, subtitulo, texto_botao, acao, so_pendentes=False):
        # Janela padrão: escolher uma tarefa numa caixa de seleção e
        # clicar no botão. A 'acao' recebe (tarefa, recarregar).
        id_usuario = self.usuario.id
        janela = Toplevel(self)
        janela.title(titulo)
        Label(
            janela,
            text=titulo,
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        Label(
            janela,
            text=subtitulo
        ).pack()
        combo = ttk.Combobox(
            janela,
            state='readonly',
            width=34
        )
        combo.pack(padx=15, pady=10)
        tarefas = []

        def recarregar():
            try:
                todas = self.banco.listar_tarefas(id_usuario)
                tarefas[:] = [t for t in todas if not (so_pendentes and t.esta_concluida())]
                combo['values'] = tuple((t.rotulo_curto() for t in tarefas))
                combo.set('')
            except sqlite3.Error as erro:
                showerror('Erro no banco de dados', str(erro))

        def clicar():
            try:
                indice = combo.current()
                if indice < 0:
                    raise ValueError('Selecione uma tarefa na lista.')
                acao(tarefas[indice], recarregar)
            except ValueError as erro:
                showerror('Dados inválidos', str(erro))
        Button(
            janela,
            text=texto_botao,
            command=clicar
        ).pack(pady=15)
        recarregar()



    def abrirConcluir(self):
        # Tela para marcar uma tarefa como concluída.
        self.selecionarTarefa(
            'Marcar uma tarefa como Concluída',
            'Selecione uma tarefa para marcar como concluída:',
            'Concluída', self.concluirTarefa, so_pendentes=True
        )



    def concluirTarefa(self, tarefa, recarregar):
        try:
            self.banco.concluir_tarefa(tarefa.id, self.usuario.id)
            showinfo('Tarefa', f'"{tarefa.titulo}" marcada como concluída.')
            recarregar()
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def abrirRemover(self):
        # Tela para remover uma tarefa.
        self.selecionarTarefa(
            'Remova uma tarefa',
            'Selecione a tarefa que deseja remover:',
            'Remover', self.removerTarefa
        )



    def removerTarefa(self, tarefa, recarregar):
        try:
            if askyesno('Confirmar exclusão', f'Deseja realmente remover a tarefa:\n{tarefa.titulo}?'):
                self.banco.remover_tarefa(tarefa.id, self.usuario.id)
                showinfo('Tarefa', 'Tarefa removida com sucesso.')
                recarregar()
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def abrirEditar(self):
        # Tela para escolher a tarefa que será editada.
        self.selecionarTarefa(
            'Editar uma tarefa',
            'Selecione a tarefa que deseja editar:',
            'Editar', self.editarTarefa
        )



    def editarTarefa(self, tarefa, recarregar):
        # Abre a janela para digitar a nova descrição.
        janela = Toplevel(self)
        janela.title('Editar tarefa')
        Label(
            janela,
            text=f'Editar {tarefa.titulo}',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=15)
        campoDescricao = criarCampo(quadro, 0, 'Nova descrição:')
        campoDescricao.insert(0, tarefa.descricao)
        Button(
            janela,
            text='Concluído',
            command=lambda: self.salvarEdicao(
                    janela, tarefa, campoDescricao, recarregar
                )
        ).pack(pady=15)



    def salvarEdicao(self, janela, tarefa, campoDescricao, recarregar):
        # UPDATE da descrição.
        try:
            nova = campoDescricao.get().strip()
            if not nova:
                raise ValueError('Informe a nova descrição.')
            self.banco.editar_descricao(tarefa.id, self.usuario.id, nova)
            showinfo('Tarefa', 'Descrição alterada com sucesso.', parent=janela)
            janela.destroy()
            recarregar()
        except ValueError as erro:
            showerror('Dados inválidos', str(erro))
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    # ----- cadastro e estudo de flashcards -----



    def abrirFlashcards(self):
        # Pequeno menu de flashcards.
        janela = Toplevel(self)
        janela.title('Flashcards')
        Label(
            janela,
            text='Flashcards',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        Button(
            janela,
            text='Cadastrar',
            width=20,
            command=self.abrirCadastroFlashcard
        ).pack(pady=5)
        Button(
            janela,
            text='Estudar',
            width=20,
            command=self.abrirEstudo
        ).pack(pady=5)
        Label(
            janela,
            text=''
        ).pack()



    def abrirCadastroFlashcard(self):
        # Janela para cadastrar pergunta (frente) e resposta (verso).
        janela = Toplevel(self)
        janela.title('Cadastrar flashcard')
        Label(
            janela,
            text='Novo flashcard',
            font=fonte_titulo
        ).pack(padx=20, pady=10)
        quadro = Frame(
            janela
        )
        quadro.pack(padx=15)
        campoPergunta = criarCampo(quadro, 0, 'Pergunta:')
        campoResposta = criarCampo(quadro, 1, 'Resposta:')
        campoDisciplina = criarCampo(quadro, 2, 'Disciplina:')
        Button(
            janela,
            text='Salvar',
            command=lambda: self.salvarFlashcard(
                    campoPergunta, campoResposta, campoDisciplina
                )
        ).pack(pady=15)



    def salvarFlashcard(self, campoPergunta, campoResposta, campoDisciplina):
        # Valida e grava o flashcard.
        try:
            pergunta = campoPergunta.get().strip()
            resposta = campoResposta.get().strip()
            disciplina = campoDisciplina.get().strip()
            if not pergunta or not resposta or (not disciplina):
                raise ValueError('Preencha pergunta, resposta e disciplina.')
            self.banco.adicionar_flashcard(self.usuario.id, pergunta, resposta, disciplina)
            showinfo('Flashcard', 'Flashcard cadastrado com sucesso!')
            campoPergunta.delete(0, 'end')
            campoResposta.delete(0, 'end')
            campoDisciplina.delete(0, 'end')
        except ValueError as erro:
            showerror('Dados inválidos', str(erro))
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    def abrirEstudo(self):
        # Modo estudo: pergunta -> 'Ver resposta' -> 'Próximo'.
        try:
            cartas = self.banco.listar_flashcards(self.usuario.id)
            if not cartas:
                showinfo('Flashcards', 'Nenhum flashcard cadastrado ainda.')
                return
            random.shuffle(cartas)
            janela = Toplevel(self)
            janela.title('Estudar')
            info = Label(
                janela,
                font=fonte_negrito
            )
            info.pack(padx=20, pady=(15, 5))
            pergunta = Label(
                janela,
                font=fonte_subtitulo,
                wraplength=300
            )
            pergunta.pack(padx=20, pady=10)
            resposta = Label(
                janela,
                wraplength=300,
                fg='#1a5fb4'
            )
            resposta.pack(padx=20, pady=10)
            botoes = Frame(
                janela
            )
            botoes.pack(pady=15)
            botaoResposta = Button(
                botoes,
                text='Ver resposta'
            )
            botaoProximo = Button(
                botoes,
                text='Próximo'
            )
            botaoResposta.grid(row=0, column=0, padx=5)
            botaoProximo.grid(row=0, column=1, padx=5)
            posicao = [0]

            def mostrar():
                carta = cartas[posicao[0]]
                info.config(text=f'Cartão {posicao[0] + 1}/{len(cartas)} - {carta.disciplina}')
                pergunta.config(text=f'Pergunta: {carta.pergunta}')
                resposta.config(text='')
                botaoResposta.config(state='normal')

            def ver_resposta():
                resposta.config(text=f'Resposta: {cartas[posicao[0]].resposta}')
                botaoResposta.config(state='disabled')

            def proximo():
                posicao[0] += 1
                if posicao[0] >= len(cartas):
                    info.config(text='')
                    pergunta.config(text='Fim dos flashcards!')
                    resposta.config(text='')
                    botaoResposta.config(state='disabled')
                    botaoProximo.config(state='disabled')
                else:
                    mostrar()
            botaoResposta.config(command=ver_resposta)
            botaoProximo.config(command=proximo)
            mostrar()
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))



    # ----- grade de estudos -----



    def abrirGrade(self, editavel):
        # Mostra a grade (matriz). Se 'editavel', permite preencher.
        try:
            id_usuario = self.usuario.id
            matriz = self.banco.carregar_grade(id_usuario)
            if not editavel and len(matriz) == 1:
                showinfo('Grade', 'A grade ainda está vazia. Use a opção "Preencher grade".')
                return
            janela = Toplevel(self)
            janela.title('Grade de estudos')
            titulo = 'Preencher grade' if editavel else 'Grade de estudos'
            Label(
                janela,
                text=titulo,
                font=fonte_titulo
            ).pack(padx=20, pady=8)
            quadro = Frame(
                janela
            )
            quadro.pack(padx=10, pady=5)
            entradas = []

            def desenhar():
                for widget in quadro.winfo_children():
                    widget.destroy()
                entradas.clear()
                for coluna, texto in enumerate(matriz[0]):
                    Label(
                        quadro,
                        text=texto,
                        width=7,
                        font=fonte_negrito
                    ).grid(row=0, column=coluna)
                for i in range(1, len(matriz)):
                    Label(
                        quadro,
                        text=matriz[i][0],
                        width=7
                    ).grid(row=i, column=0)
                    linha_entradas = []
                    for coluna in range(1, len(matriz[i])):
                        if editavel:
                            campo = Entry(
                                quadro,
                                width=7
                            )
                            campo.insert(0, matriz[i][coluna])
                            campo.grid(row=i, column=coluna, padx=1, pady=1)
                            linha_entradas.append(campo)
                        else:
                            Label(
                                quadro,
                                text=matriz[i][coluna],
                                width=7,
                                wraplength=60,
                                relief='groove'
                            ).grid(row=i, column=coluna, padx=1, pady=1)
                    entradas.append(linha_entradas)

            def ler_entradas():
                # Copia o que está nos campos de volta para a matriz.
                for i, linha in enumerate(entradas, start=1):
                    for coluna, campo in enumerate(linha, start=1):
                        matriz[i][coluna] = campo.get().strip()
            desenhar()
            if not editavel:
                return
            controles = Frame(
                janela
            )
            controles.pack(side='bottom', pady=8)
            Label(
                controles,
                text='Novo horário:'
            ).pack(side='left', padx=3)
            campoHorario = Entry(
                controles,
                width=7
            )
            campoHorario.pack(side='left', padx=3)

            def adicionar_horario():
                try:
                    ler_entradas()
                    texto = campoHorario.get().strip()
                    try:
                        datetime.strptime(texto, '%H:%M')
                    except ValueError:
                        raise ValueError('Horário inválido.')
                    if texto in [linha[0] for linha in matriz[1:]]:
                        raise ValueError('Esse horário já está na grade.')
                    matriz.append([texto] + [''] * len(dias_semana))
                    campoHorario.delete(0, 'end')
                    desenhar()
                except ValueError as erro:
                    showerror('Dados inválidos', str(erro))

            def remover_ultimo():
                ler_entradas()
                if len(matriz) > 1:
                    matriz.pop()
                    desenhar()

            def salvar():
                try:
                    ler_entradas()
                    self.banco.salvar_grade(id_usuario, matriz)
                    showinfo('Grade', 'Grade salva com sucesso!', parent=janela)
                except sqlite3.Error as erro:
                    showerror('Erro no banco de dados', str(erro))
            Button(
                controles,
                text='Adicionar horário',
                command=adicionar_horario
            ).pack(side='left', padx=3)
            Button(
                controles,
                text='Remover horário',
                command=remover_ultimo
            ).pack(side='left', padx=3)
            Button(
                controles,
                text='Salvar grade',
                command=salvar
            ).pack(side='left', padx=3)
        except sqlite3.Error as erro:
            showerror('Erro no banco de dados', str(erro))
if __name__ == '__main__':
    Interface().mainloop()
