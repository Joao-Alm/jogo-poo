import arcade
import random
import time
import datetime
from peewee import *
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Constantes
LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO_TELA = "Jogo POO - IFPR"

# ---------------------------------------------------------------------------
# Configuração do Spritesheet do jogador (AJUSTE conforme a SUA folha de sprites)
# ---------------------------------------------------------------------------
ARQUIVO_SPRITESHEET = r"imagens\jogador_spritesheet.png"
LARGURA_QUADRO = 64        # largura de cada quadro (px)
ALTURA_QUADRO = 64         # altura de cada quadro (px)
COLUNAS_SHEET = 4          # quantidade de colunas da folha
TOTAL_QUADROS = 4          # quantidade total de quadros
IDX_PARADO = 0             # índice do quadro de repouso
IDX_PULANDO = 1            # índice do quadro de pulo/queda
IDX_ANDANDO = [2, 3]       # índices dos quadros do ciclo de caminhada
INTERVALO_ANIMACAO = 0.1   # 100 ms entre quadros da caminhada

MAX_NOME = 15

db = SqliteDatabase("ranking.db")


class BaseModel(Model):
    class Meta:
        database = db


class Pontuacao(BaseModel):
    nome_jogador = CharField()
    pontos = IntegerField()
    tempo_partida = FloatField()
    data_hora = DateTimeField(default=datetime.datetime.now)

    def __str__(self):
        return f"{self.nome_jogador} - {self.pontos} pts ({self.tempo_partida:.1f}s)"


db.connect(reuse_if_open=True)
db.create_tables([Pontuacao])


class Bloco(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()
        try:
            self.texture = arcade.load_texture(r"imagens\bloco.png")
            self.scale = 0.25
        except Exception:
            self.texture = arcade.make_soft_square_texture(30, arcade.color.DARK_SLATE_GRAY)
        self.center_x = x - 4
        self.center_y = y - 6


class Jogador(arcade.Sprite):
    def __init__(self):
        super().__init__()

        self._carregar_texturas()

        # Define a textura inicial
        self.texture = self.tex_parado

        # Escala aplicada a cada estado do jogador
        self.escala_parado = 0.07
        self.escala_andando = 0.07
        self.escala_pulando = 0.07

        self.scale_x = self.escala_parado
        self.scale_y = self.escala_parado

        self.center_x = 100
        self.center_y = 100
        self.pontos = 0
        self.vidas = 3
        self.velocidade = 5
        self.tempo_invulneravel = 0
        self.virado_para = "direita"

        # Máquina de estados / animação
        self.estado_atual = "parado"
        self.indice_frame = 0
        self.tempo_animacao = 0.0
        self._ultimo_visual = None

    def _carregar_texturas(self):
        """Carrega os quadros via spritesheet; se falhar, usa as imagens individuais."""
        try:
            sheet = arcade.load_spritesheet(ARQUIVO_SPRITESHEET)
            quadros = sheet.get_texture_grid(
                size=(LARGURA_QUADRO, ALTURA_QUADRO),
                columns=COLUNAS_SHEET,
                count=TOTAL_QUADROS,
            )
            self.tex_parado = quadros[IDX_PARADO]
            self.tex_pulando = quadros[IDX_PULANDO]
            self.frames_andando = [quadros[i] for i in IDX_ANDANDO]
        except Exception:
            self._carregar_texturas_individuais()

    def _carregar_texturas_individuais(self):
        try:
            self.tex_parado = arcade.load_texture(r"imagens\jogador.png")
        except Exception:
            try:
                self.tex_parado = arcade.load_texture(r"imagens\jogador_parado.png")
            except Exception:
                self.tex_parado = arcade.make_soft_square_texture(32, arcade.color.GOLD)

        try:
            tex_andando = arcade.load_texture(r"imagens\jogador_andando.png")
        except Exception:
            tex_andando = self.tex_parado

        try:
            self.tex_pulando = arcade.load_texture(r"imagens\jogador_pulando.png")
        except Exception:
            self.tex_pulando = self.tex_parado

        self.frames_andando = [tex_andando]

    def update(self, delta_time=1 / 60, *args, **kwargs):
        # Invulnerabilidade (efeito de piscar)
        if self.tempo_invulneravel > 0:
            self.tempo_invulneravel -= delta_time
            self.alpha = 128 if int(self.tempo_invulneravel * 10) % 2 == 0 else 255
        else:
            self.alpha = 255

        # Limites da tela
        if self.left < 0:
            self.left = 0
        if self.right > LARGURA_TELA:
            self.right = LARGURA_TELA

        direcao = -1 if self.virado_para == "esquerda" else 1

        # Prioridade de estados: Pulo/Queda -> Repouso -> Andando
        if self.change_y != 0:
            novo_estado = "pulando"
        elif self.change_x == 0:
            novo_estado = "parado"
        else:
            novo_estado = "andando"

        if novo_estado != self.estado_atual:
            self.estado_atual = novo_estado
            self.indice_frame = 0
            self.tempo_animacao = 0.0

        if novo_estado == "pulando":
            textura = self.tex_pulando
            escala = self.escala_pulando
        elif novo_estado == "parado":
            textura = self.tex_parado
            escala = self.escala_parado
        else:
            # Alterna os quadros da caminhada a cada 100 ms
            self.tempo_animacao += delta_time
            while self.tempo_animacao >= INTERVALO_ANIMACAO:
                self.tempo_animacao -= INTERVALO_ANIMACAO
                self.indice_frame = (self.indice_frame + 1) % len(self.frames_andando)
            textura = self.frames_andando[self.indice_frame]
            escala = self.escala_andando

        # Só reaplica se algo realmente mudou (evita flicker e trabalho extra)
        chave = (id(textura), escala, direcao)
        if chave != self._ultimo_visual:
            self._ultimo_visual = chave
            self.texture = textura
            self.scale_x = escala * direcao
            self.scale_y = escala


class MoedaFixa(arcade.Sprite):
    def __init__(self, x, y):
        super().__init__()

        try:
            self.texture = arcade.load_texture(r"imagens\moeda.png")
            self.scale = 0.01
        except Exception:
            self.texture = arcade.make_soft_square_texture(
                15, arcade.color.YELLOW
            )

        self.center_x = x
        self.center_y = y
        self.valor = 1


class Inimigo(arcade.Sprite):
    def __init__(self, lista_blocos, x, y, min_x, max_x, velocidade=3.5):
        super().__init__()
        try:
            self.texture = arcade.load_texture(r"imagens\inimigo.png")
            self.scale = 0.015
        except Exception:
            self.texture = arcade.make_soft_square_texture(25, arcade.color.RED)
        self.center_x = x
        self.center_y = y
        self.change_x = velocidade
        self.min_x = min_x
        self.max_x = max_x
        self.lista_blocos = lista_blocos
        self.physics_engine = arcade.PhysicsEnginePlatformer(self, lista_blocos, gravity_constant=0.5)

    def update(self, delta_time):
        self.physics_engine.update()

        if self.center_x < self.min_x:
            self.center_x = self.min_x
            self.change_x *= -1
        elif self.center_x > self.max_x:
            self.center_x = self.max_x
            self.change_x *= -1

        if self.left < 0:
            self.left = 0
            self.change_x *= -1
        elif self.right > LARGURA_TELA:
            self.right = LARGURA_TELA
            self.change_x *= -1


class InimigoEspecial(arcade.Sprite):
    def __init__(self, lista_blocos, x, y, min_x, max_x, velocidade=4.5):
        super().__init__()
        try:
            self.texture = arcade.load_texture(r"imagens\inimigo_especial.png")
            self.scale = 0.06
        except Exception:
            self.texture = arcade.make_soft_square_texture(30, arcade.color.PURPLE)
        self.center_x = x
        self.center_y = y
        self.change_x = velocidade
        self.min_x = min_x
        self.max_x = max_x
        self.lista_blocos = lista_blocos
        self.physics_engine = arcade.PhysicsEnginePlatformer(self, lista_blocos, gravity_constant=0.5)

    def update(self, delta_time):
        self.physics_engine.update()

        if self.center_x < self.min_x:
            self.center_x = self.min_x
            self.change_x *= -1
        elif self.center_x > self.max_x:
            self.center_x = self.max_x
            self.change_x *= -1

        if self.left < 0:
            self.left = 0
            self.change_x *= -1
        elif self.right > LARGURA_TELA:
            self.right = LARGURA_TELA
            self.change_x *= -1


class Desenvolvedor(arcade.Sprite):
    def __init__(self):
        super().__init__()
        try:
            self.texture = arcade.load_texture(r"imagens\eu.png")
            self.scale = 0.08
        except Exception:
            self.texture = arcade.make_soft_square_texture(40, arcade.color.BLUE)
        self.center_x = LARGURA_TELA / 2
        self.center_y = ALTURA_TELA / 2 + 15


class MenuPrincipal(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("TUN TUN SAHUR: A CAÇADA DAS MOEDAS",
                         LARGURA_TELA / 2, ALTURA_TELA / 2 + 120,
                         arcade.color.WHITE, 25, anchor_x="center")
        arcade.draw_text("[J] Jogar", LARGURA_TELA / 2, ALTURA_TELA / 2 + 30,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[I] Instruções", LARGURA_TELA / 2, ALTURA_TELA / 2 - 10,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[S] Sobre o Jogo", LARGURA_TELA / 2, ALTURA_TELA / 2 - 50,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[R] Ranking", LARGURA_TELA / 2, ALTURA_TELA / 2 - 90,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[ESC] Sair", LARGURA_TELA / 2, ALTURA_TELA / 2 - 130,
                         arcade.color.WHITE, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.J:
            tela = JogoPrincipal()
            tela.setup()
            self.window.show_view(tela)
        elif key == arcade.key.I:
            self.window.show_view(Instrucoes())
        elif key == arcade.key.S:
            self.window.show_view(Sobre())
        elif key == arcade.key.R:
            self.window.show_view(TelaRanking())
        elif key == arcade.key.ESCAPE:
            arcade.close_window()


class Instrucoes(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("INSTRUÇÕES", LARGURA_TELA / 2, ALTURA_TELA / 2 + 120,
                         arcade.color.WHITE, 30, anchor_x="center")
        arcade.draw_text("Objetivo: Ajude Tun Tun Sahur a coletar moedas nas plataformas.",
                         LARGURA_TELA / 2, ALTURA_TELA / 2 + 60,
                         arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("Cuidado: Levar dano adiciona penalidade de tempo (+5s)!",
                         LARGURA_TELA / 2, ALTURA_TELA / 2 + 20,
                         arcade.color.YELLOW, 12, anchor_x="center")
        arcade.draw_text("Controles: Setas ou A/D = Movimentação | W / Seta Cima = Pular",
                         LARGURA_TELA / 2, ALTURA_TELA / 2 - 20,
                         arcade.color.WHITE, 12, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or key == arcade.key.M:
            self.window.show_view(MenuPrincipal())


class Sobre(arcade.View):
    def __init__(self):
        super().__init__()
        self.lista_desenvolvedor = arcade.SpriteList()
        self.lista_desenvolvedor.append(Desenvolvedor())

    def on_draw(self):
        self.clear()
        arcade.draw_text("SOBRE O JOGO", LARGURA_TELA / 2, ALTURA_TELA / 2 + 150,
                         arcade.color.WHITE, 30, anchor_x="center")
        self.lista_desenvolvedor.draw()
        arcade.draw_text("Desenvolvedor:", LARGURA_TELA / 2, ALTURA_TELA / 2 - 130,
                         arcade.color.WHITE, 15, anchor_x="center")
        arcade.draw_text("João Pedro Almeida", LARGURA_TELA / 2, ALTURA_TELA / 2 - 160,
                         arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[ESC] ou [M] para voltar ao Menu", LARGURA_TELA / 2, 50,
                         arcade.color.WHITE, 15, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or key == arcade.key.M:
            self.window.show_view(MenuPrincipal())


class JogoPrincipal(arcade.View):
    def __init__(self):
        super().__init__()
        self.tempo_inicio = 0
        self.penalidade_tempo = 0
        self.alerta = ""
        self.jogador = None
        self.lista_moedas = None
        self.lista_inimigos = None
        self.lista_blocos = None
        self.physics_engine = None
        self.jogo_finalizado = False
        self.fundo = None
        self.teclas_pressionadas = set()

        # Objetos de Texto Otimizados
        self.txt_pontos = arcade.Text("Pontos: 0", 10, ALTURA_TELA - 20, arcade.color.WHITE, 14)
        self.txt_vidas = arcade.Text("Vidas: 3", 10, ALTURA_TELA - 40, arcade.color.RED, 14, bold=True)
        self.txt_tempo = arcade.Text("Tempo: 0s", 10, ALTURA_TELA - 60, arcade.color.WHITE, 14)
        self.txt_alerta = arcade.Text("", LARGURA_TELA / 2, 50, arcade.color.RED, 18, anchor_x="center")

    def setup(self):
        self.tempo_inicio = time.time()
        self.penalidade_tempo = 0
        self.alerta = ""
        self.jogo_finalizado = False
        self.teclas_pressionadas.clear()

        try:
            self.fundo = arcade.load_texture(r"imagens\fundo.png")
        except Exception:
            self.fundo = None

        self.jogador = Jogador()
        self.lista_moedas = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()
        self.lista_blocos = arcade.SpriteList()

        for x in range(0, LARGURA_TELA + 20, 20):
            self.lista_blocos.append(Bloco(x, 20))

        for x in range(150, 650, 20):
            self.lista_blocos.append(Bloco(x, 180))

        for x in range(250, 550, 20):
            self.lista_blocos.append(Bloco(x, 340))

        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.jogador, self.lista_blocos, gravity_constant=0.5
        )

        # Posições fixas das moedas
        posicoes_moedas = [
            (100, 70), (300, 70), (500, 70), (700, 70),
            (200, 230), (400, 230), (600, 230),
            (300, 390), (450, 390)
        ]

        # Todas as moedas serão fixas
        for px, py in posicoes_moedas:
            self.lista_moedas.append(MoedaFixa(px, py))

        # Inimigos
        self.lista_inimigos.append(
            Inimigo(self.lista_blocos, 200, 60, 20, 780, velocidade=4.0)
        )
        self.lista_inimigos.append(
            Inimigo(self.lista_blocos, 400, 220, 150, 650, velocidade=3.5)
        )
        self.lista_inimigos.append(
            InimigoEspecial(self.lista_blocos, 400, 380, 250, 550, velocidade=4.5)
        )

    def on_draw(self):
        self.clear()
        if self.fundo:
            arcade.draw_texture_rect(self.fundo, arcade.LBWH(0, 0, LARGURA_TELA, ALTURA_TELA))

        self.lista_blocos.draw()
        arcade.draw_sprite(self.jogador)
        self.lista_moedas.draw()
        self.lista_inimigos.draw()

        tempo_decorrido = int((time.time() - self.tempo_inicio) + self.penalidade_tempo)

        self.txt_pontos.text = f"Pontos: {self.jogador.pontos}"
        self.txt_vidas.text = f"Vidas: {self.jogador.vidas}"
        self.txt_tempo.text = f"Tempo: {tempo_decorrido}s"

        self.txt_pontos.draw()
        self.txt_vidas.draw()
        self.txt_tempo.draw()

        if self.alerta:
            self.txt_alerta.text = self.alerta
            self.txt_alerta.draw()

    def on_update(self, delta_time):
        if self.jogo_finalizado:
            return

        self.physics_engine.update()

        # A máquina de estados do Player decide a animação (change_y / change_x)
        self.jogador.update(delta_time)
        self.lista_moedas.update(delta_time)
        self.lista_inimigos.update()

        moedas_coletadas = arcade.check_for_collision_with_list(
            self.jogador, self.lista_moedas
        )
        for moeda in moedas_coletadas:
            self.jogador.pontos += moeda.valor
            moeda.kill()

        if len(self.lista_moedas) == 0:
            self.jogo_finalizado = True
            tempo_total = (time.time() - self.tempo_inicio) + self.penalidade_tempo
            self.window.show_view(TelaVitoria(self.jogador.pontos, tempo_total))
            return

        if self.jogador.tempo_invulneravel <= 0:
            inimigos_atingidos = arcade.check_for_collision_with_list(
                self.jogador, self.lista_inimigos
            )
            for inimigo in inimigos_atingidos:
                self.jogador.vidas -= 1
                self.jogador.tempo_invulneravel = 1.5
                self.penalidade_tempo += 5
                self.alerta = f"DANO! +5s DE PENALIDADE! Vidas: {self.jogador.vidas}"

                if self.jogador.vidas <= 0:
                    self.jogo_finalizado = True
                    tempo_total = (time.time() - self.tempo_inicio) + self.penalidade_tempo
                    self.window.show_view(TelaDerrota(self.jogador.pontos, tempo_total))
                    return

    def _atualizar_movimento(self):
        vel = self.jogador.velocidade
        esquerda = arcade.key.LEFT in self.teclas_pressionadas or arcade.key.A in self.teclas_pressionadas
        direita = arcade.key.RIGHT in self.teclas_pressionadas or arcade.key.D in self.teclas_pressionadas

        if esquerda and not direita:
            self.jogador.change_x = -vel
            self.jogador.virado_para = "esquerda"
        elif direita and not esquerda:
            self.jogador.change_x = vel
            self.jogador.virado_para = "direita"
        else:
            self.jogador.change_x = 0

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MenuPrincipal())
            return

        self.teclas_pressionadas.add(key)

        # Bloqueio de pulo duplo: só pula se can_jump() for verdadeiro
        if key in [arcade.key.UP, arcade.key.W]:
            if self.physics_engine.can_jump():
                self.jogador.change_y = 14.5

        self._atualizar_movimento()

    def on_key_release(self, key, modifiers):
        if key in self.teclas_pressionadas:
            self.teclas_pressionadas.remove(key)
        self._atualizar_movimento()


class TelaVitoria(arcade.View):
    def __init__(self, pontos, tempo):
        super().__init__()
        self.pontos = pontos
        self.tempo = tempo
        self.nome = ""

    def on_draw(self):
        self.clear()
        arcade.draw_text("PARABÉNS! VOCÊ VENCEU!", LARGURA_TELA / 2, ALTURA_TELA / 2 + 130,
                         arcade.color.GOLD, 28, anchor_x="center")
        arcade.draw_text(f"Pontuação Final: {self.pontos}", LARGURA_TELA / 2,
                         ALTURA_TELA / 2 + 80, arcade.color.WHITE, 18,
                         anchor_x="center")
        arcade.draw_text(f"Tempo Total (com penalidades): {self.tempo:.1f} segundos", LARGURA_TELA / 2,
                         ALTURA_TELA / 2 + 45, arcade.color.WHITE, 16,
                         anchor_x="center")
        arcade.draw_text("Digite seu nome para salvar no Ranking:", LARGURA_TELA / 2,
                         ALTURA_TELA / 2, arcade.color.WHITE, 16,
                         anchor_x="center")

        arcade.draw_text(self.nome + "|", LARGURA_TELA / 2,
                         ALTURA_TELA / 2 - 45, arcade.color.YELLOW, 24,
                         anchor_x="center")

        arcade.draw_text("[ENTER] Salvar e ver Ranking | [ESC] Voltar ao Menu",
                         LARGURA_TELA / 2, 50, arcade.color.WHITE, 13,
                         anchor_x="center")

    def on_text(self, text):
        # Aceita apenas caracteres imprimíveis e limita o tamanho do nome
        if text.isprintable() and len(self.nome) < MAX_NOME:
            self.nome += text[:MAX_NOME - len(self.nome)]

    def on_key_press(self, key, modifiers):
        if key == arcade.key.BACKSPACE:
            self.nome = self.nome[:-1]
        elif key == arcade.key.ENTER or key == arcade.key.NUM_ENTER:
            if self.nome.strip():
                registro = Pontuacao.create(
                    nome_jogador=self.nome.strip(),
                    pontos=self.pontos,
                    tempo_partida=self.tempo
                )
                print(registro)  # usa o __str__ para depuração no console
                self.window.show_view(TelaRanking())
        elif key == arcade.key.ESCAPE:
            self.window.show_view(MenuPrincipal())


class TelaDerrota(arcade.View):
    def __init__(self, pontos, tempo):
        super().__init__()
        self.pontos = pontos
        self.tempo = tempo

    def on_draw(self):
        self.clear()
        arcade.draw_text("FIM DE JOGO - DERROTA", LARGURA_TELA / 2, ALTURA_TELA / 2 + 100,
                         arcade.color.RED, 30, anchor_x="center")
        arcade.draw_text("Suas vidas acabaram!", LARGURA_TELA / 2, ALTURA_TELA / 2 + 50,
                         arcade.color.SALMON, 18, anchor_x="center")
        arcade.draw_text(f"Pontuação: {self.pontos} | Tempo: {self.tempo:.1f}s",
                         LARGURA_TELA / 2, ALTURA_TELA / 2, arcade.color.WHITE, 16,
                         anchor_x="center")
        arcade.draw_text("[R] Jogar Novamente", LARGURA_TELA / 2, ALTURA_TELA / 2 - 60,
                         arcade.color.GOLD, 20, anchor_x="center")
        arcade.draw_text("[ESC] ou [M] Menu", LARGURA_TELA / 2, ALTURA_TELA / 2 - 100,
                         arcade.color.WHITE, 16, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            tela = JogoPrincipal()
            tela.setup()
            self.window.show_view(tela)
        elif key == arcade.key.ESCAPE or key == arcade.key.M:
            self.window.show_view(MenuPrincipal())


class TelaRanking(arcade.View):
    def __init__(self):
        super().__init__()
        # Consulta executada UMA única vez; list() força a execução agora
        # (o Peewee é "preguiçoso" e só consultaria o banco ao iterar).
        self.melhores = list(
            Pontuacao.select()
            .order_by(Pontuacao.pontos.desc(), Pontuacao.tempo_partida.asc())
            .limit(10)
        )

    def on_draw(self):
        self.clear()
        arcade.draw_text("RANKING - TOP 10", LARGURA_TELA / 2, ALTURA_TELA - 70,
                         arcade.color.GOLD, 30, anchor_x="center")

        if not self.melhores:
            arcade.draw_text("Nenhuma pontuação registrada ainda.",
                             LARGURA_TELA / 2, ALTURA_TELA / 2,
                             arcade.color.WHITE, 18, anchor_x="center")
        else:
            # Cabeçalho das colunas
            y_cab = ALTURA_TELA - 120
            arcade.draw_text("#", 120, y_cab, arcade.color.LIGHT_GRAY, 14, anchor_x="right")
            arcade.draw_text("Jogador", 150, y_cab, arcade.color.LIGHT_GRAY, 14)
            arcade.draw_text("Pontos", 520, y_cab, arcade.color.LIGHT_GRAY, 14, anchor_x="right")
            arcade.draw_text("Tempo", 640, y_cab, arcade.color.LIGHT_GRAY, 14, anchor_x="right")
            arcade.draw_text("Data", 680, y_cab, arcade.color.LIGHT_GRAY, 14)

            for i, p in enumerate(self.melhores):
                y = ALTURA_TELA - 160 - i * 36   # Y proporcional ao índice
                cor = arcade.color.GOLD if i == 0 else arcade.color.WHITE
                arcade.draw_text(f"{i + 1}º", 120, y, cor, 16, anchor_x="right")
                arcade.draw_text(p.nome_jogador, 150, y, cor, 16)
                arcade.draw_text(str(p.pontos), 520, y, cor, 16, anchor_x="right")
                arcade.draw_text(f"{p.tempo_partida:.1f}s", 640, y, cor, 16, anchor_x="right")
                arcade.draw_text(p.data_hora.strftime("%d/%m"), 680, y, cor, 16)

        arcade.draw_text("[ESC] ou [M] para voltar ao Menu", LARGURA_TELA / 2, 30,
                         arcade.color.WHITE, 14, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or key == arcade.key.M:
            self.window.show_view(MenuPrincipal())


def main():
    janela = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO_TELA)
    janela.show_view(MenuPrincipal())
    arcade.run()


if __name__ == "__main__":
    main()
