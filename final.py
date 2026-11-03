import arcade
import random
import time
import datetime
from peewee import *

# Constantes
LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO_TELA = "Jogo POO - IFPR"

# --- Configuração da Spritesheet do jogador ---
# Se for usar outra folha de sprites, basta ajustar os valores abaixo.
ARQUIVO_SPRITESHEET = r"imagens\jogador_spritesheet.png"
LARGURA_QUADRO = 48        # largura de CADA quadro, em pixels
ALTURA_QUADRO = 48         # altura de CADA quadro, em pixels
COLUNAS_SHEET = 4          # quantas colunas a folha tem
TOTAL_QUADROS = 4          # quantos quadros a folha tem no total
QUADRO_PARADO = 0          # índice do quadro "parado"
QUADROS_ANDANDO = [1, 2]   # índices dos quadros do ciclo de caminhada
QUADRO_PULO = 3            # índice do quadro de pulo/queda
INTERVALO_ANIMACAO = 0.1   # 100 ms entre um quadro e outro da caminhada

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


db.connect()
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

        # Carrega a folha de sprites e fatia em quadros (texturas)
        try:
            folha = arcade.load_spritesheet(ARQUIVO_SPRITESHEET)
            self.texturas = folha.get_texture_grid(
                size=(LARGURA_QUADRO, ALTURA_QUADRO),
                columns=COLUNAS_SHEET,
                count=TOTAL_QUADROS,
            )
        except Exception as erro:
            print(f"Aviso: não foi possível carregar a spritesheet ({erro}).")
            quadro_reserva = arcade.make_soft_square_texture(32, arcade.color.GOLD)
            self.texturas = [quadro_reserva] * TOTAL_QUADROS

        # Escala única: todos os quadros da folha têm o mesmo tamanho
        self.escala = 1.0

        # Define a textura inicial
        self.texture = self.texturas[QUADRO_PARADO]
        self.scale_x = self.escala
        self.scale_y = self.escala

        self.center_x = 100
        self.center_y = 100
        self.pontos = 0
        self.vidas = 3
        self.velocidade = 5
        self.tempo_invulneravel = 0
        self.virado_para = "direita"

        # Estado de animação
        self.estado_atual = "parado"
        self.quadro_atual = 0      # posição dentro de QUADROS_ANDANDO
        self.tempo_quadro = 0      # tempo acumulado desde a última troca de quadro

    def update(self, delta_time=1 / 60):
        # OBS: não chamamos super().update() de propósito, porque quem move o
        # jogador é o PhysicsEnginePlatformer (evita mover duas vezes).

        # Efeito de piscar quando está invulnerável
        if self.tempo_invulneravel > 0:
            self.tempo_invulneravel -= delta_time
            self.alpha = 128 if int(self.tempo_invulneravel * 10) % 2 == 0 else 255
        else:
            self.alpha = 255

        # Não deixa o jogador sair da tela
        if self.left < 0:
            self.left = 0
        if self.right > LARGURA_TELA:
            self.right = LARGURA_TELA

        # --- Máquina de estados (ordem de prioridade) ---
        # 1º Pulo/Queda  ->  2º Parado  ->  3º Andando
        if self.change_y != 0:
            novo_estado = "pulando"
        elif self.change_x == 0:
            novo_estado = "parado"
        else:
            novo_estado = "andando"

        if novo_estado == "pulando":
            self.texture = self.texturas[QUADRO_PULO]

        elif novo_estado == "parado":
            # Textura estática (o lado é definido pela direção abaixo)
            self.texture = self.texturas[QUADRO_PARADO]

        else:  # andando
            # Se acabou de começar a andar, reinicia o ciclo da caminhada
            if self.estado_atual != "andando":
                self.quadro_atual = 0
                self.tempo_quadro = 0

            # Temporizador por delta_time: troca de quadro a cada 100 ms
            self.tempo_quadro += delta_time
            if self.tempo_quadro >= INTERVALO_ANIMACAO:
                self.tempo_quadro -= INTERVALO_ANIMACAO
                self.quadro_atual = (self.quadro_atual + 1) % len(QUADROS_ANDANDO)

            self.texture = self.texturas[QUADROS_ANDANDO[self.quadro_atual]]

        self.estado_atual = novo_estado

        # Direção (virado_para): espelha a imagem quando olha para a esquerda
        direcao = -1 if self.virado_para == "esquerda" else 1
        self.scale_x = self.escala * direcao
        self.scale_y = self.escala


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

        # 1º a física move o jogador (gravidade, colisões, pulo)...
        self.physics_engine.update()

        # 2º o jogador atualiza a própria animação (usa change_x e change_y)
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
        # Aceita só caracteres imprimíveis e limita o tamanho do nome
        if text.isprintable() and len(self.nome) < 15:
            self.nome += text

    def on_key_press(self, key, modifiers):
        if key == arcade.key.BACKSPACE:
            self.nome = self.nome[:-1]
        elif key == arcade.key.ENTER:
            if self.nome.strip():
                registro = Pontuacao.create(
                    nome_jogador=self.nome.strip(),
                    pontos=self.pontos,
                    tempo_partida=self.tempo
                )
                print("Pontuação salva:", registro)  # usa o __str__ da Pontuacao
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
        arcade.draw_text("[M] ou [ESC] Voltar ao Menu Principal", LARGURA_TELA / 2,
                         ALTURA_TELA / 2 - 100, arcade.color.WHITE, 15,
                         anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.R:
            tela = JogoPrincipal()
            tela.setup()
            self.window.show_view(tela)
        elif key in [arcade.key.M, arcade.key.ESCAPE]:
            self.window.show_view(MenuPrincipal())


class TelaRanking(arcade.View):
    def __init__(self):
        super().__init__()
        # A consulta é executada UMA única vez, aqui no __init__.
        # list(...) é o que realmente roda a consulta agora: sem ele, o Peewee
        # guardaria só a "receita" da busca e ela rodaria dentro do on_draw().
        self.melhores = list(
            Pontuacao.select()
            .order_by(Pontuacao.pontos.desc(), Pontuacao.tempo_partida.asc())
            .limit(10)
        )

    def on_draw(self):
        self.clear()
        arcade.draw_text("RANKING - TOP 10", LARGURA_TELA / 2, ALTURA_TELA - 70,
                         arcade.color.GOLD, 30, anchor_x="center")

        if len(self.melhores) == 0:
            arcade.draw_text("Nenhuma pontuação ainda!", LARGURA_TELA / 2,
                             ALTURA_TELA / 2, arcade.color.WHITE, 18,
                             anchor_x="center")
        else:
            # Cabeçalho das colunas (posições X fixas = textos alinhados)
            y_cab = ALTURA_TELA - 130
            arcade.draw_text("Pos.", 100, y_cab, arcade.color.GOLD, 16, bold=True)
            arcade.draw_text("Jogador", 170, y_cab, arcade.color.GOLD, 16, bold=True)
            arcade.draw_text("Pontos", 560, y_cab, arcade.color.GOLD, 16,
                             bold=True, anchor_x="right")
            arcade.draw_text("Tempo", 700, y_cab, arcade.color.GOLD, 16,
                             bold=True, anchor_x="right")

            for indice, pontuacao in enumerate(self.melhores, 1):
                y = ALTURA_TELA - 130 - indice * 35
                arcade.draw_text(f"{indice}º", 100, y, arcade.color.WHITE, 16)
                arcade.draw_text(pontuacao.nome_jogador, 170, y,
                                 arcade.color.WHITE, 16)
                arcade.draw_text(f"{pontuacao.pontos}", 560, y,
                                 arcade.color.WHITE, 16, anchor_x="right")
                arcade.draw_text(f"{pontuacao.tempo_partida:.1f}s", 700, y,
                                 arcade.color.WHITE, 16, anchor_x="right")

        arcade.draw_text("[M] Menu Principal", LARGURA_TELA / 2, 35,
                         arcade.color.WHITE, 15, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.M or key == arcade.key.ESCAPE:
            self.window.show_view(MenuPrincipal())


def main():
    window = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO_TELA)
    menu = MenuPrincipal()
    window.show_view(menu)
    arcade.run()


if __name__ == "__main__":
    main()
