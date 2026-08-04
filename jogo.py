import arcade
import random
import time

# Constantes
LARGURA_TELA = 800
ALTURA_TELA = 600
TITULO_TELA = "Jogo POO - IFPR"

class Jogador(arcade.Sprite):
    def __init__(self):
        super().__init__(r"imagens\jogador.png", 0.08)
        self.center_x = LARGURA_TELA // 2
        self.center_y = ALTURA_TELA // 2
        self.pontos = 0
        self.velocidade = 5

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y
        if self.left < 0: self.left = 0
        if self.right > LARGURA_TELA: self.right = LARGURA_TELA
        if self.bottom < 0: self.bottom = 0
        if self.top > ALTURA_TELA: self.top = ALTURA_TELA

class MoedaFixa(arcade.Sprite):
    def __init__(self):
        super().__init__(r"imagens\moeda.png", 0.01)
        self.center_x = random.randint(20, LARGURA_TELA - 20)
        self.center_y = random.randint(20, ALTURA_TELA - 20)
        self.valor = 1

class MoedaMovel(MoedaFixa):
    def __init__(self):
        super().__init__()
        self.color = arcade.color.GOLD
        self.change_x = 3
        self.change_y = 3
        self.valor = 5

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.left < 0 or self.right > LARGURA_TELA:
            self.change_x *= -1
        if self.bottom < 0 or self.top > ALTURA_TELA:
            self.change_y *= -1

class Inimigo(arcade.Sprite):
    def __init__(self):
        super().__init__(r"imagens\inimigo.png", 0.02)
        self.center_x = random.randint(20, LARGURA_TELA - 20)
        self.center_y = random.randint(20, ALTURA_TELA - 20)
        self.velocidade = 2
        self.change_x = 2
        self.change_y = 2

    def update(self, delta_time):
        self.center_x += self.change_x
        self.center_y += self.change_y

        if self.left < 0 or self.right > LARGURA_TELA:
            self.change_x *= -1
        if self.bottom < 0 or self.top > ALTURA_TELA:
            self.change_y *= -1

class InimigoEspecial(arcade.Sprite):
    def __init__(self):
        super().__init__(r"imagens\inimigo_especial.png", 0.1)
        self.center_x = random.randint(20, LARGURA_TELA - 20)
        self.center_y = random.randint(20, ALTURA_TELA - 20)
        self.velocidade = 1
        self.temporizador = 0

    def update(self, delta_time):
        self.temporizador += delta_time
        if self.temporizador >= 3:
            self.center_x = random.randint(20, LARGURA_TELA - 20)
            self.center_y = random.randint(20, ALTURA_TELA - 20)
            self.temporizador = 0

    def seguir_jogador(self, jogador):
        if self.center_x < jogador.center_x: self.center_x += self.velocidade
        elif self.center_x > jogador.center_x: self.center_x -= self.velocidade
        if self.center_y < jogador.center_y: self.center_y += self.velocidade
        elif self.center_y > jogador.center_y: self.center_y -= self.velocidade

class Desenvolvedor(arcade.Sprite):
    def __init__(self):
        super().__init__(r"imagens\eu.png", 0.08)
        self.center_x = LARGURA_TELA / 2
        self.center_y = ALTURA_TELA / 2 + 15

class MenuPrincipal(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("TUN TUN SAHUR: A CAÇADA DAS MOEDAS", LARGURA_TELA/2, ALTURA_TELA/2 + 120, arcade.color.WHITE, 25, anchor_x="center")
        arcade.draw_text("[J] Jogar", LARGURA_TELA/2, ALTURA_TELA/2 + 30, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[I] Instruções", LARGURA_TELA/2, ALTURA_TELA/2 - 10, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[S] Sobre o Jogo", LARGURA_TELA/2, ALTURA_TELA/2 - 50, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[ESC] Sair", LARGURA_TELA/2, ALTURA_TELA/2 - 90, arcade.color.WHITE, 18, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.J:
            tela = JogoPrincipal()
            tela.setup()
            self.window.show_view(tela)
        elif key == arcade.key.I:
            self.window.show_view(Instrucoes())
        elif key == arcade.key.S:
            self.window.show_view(Sobre())
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

class Instrucoes(arcade.View):
    def on_draw(self):
        self.clear()
        arcade.draw_text("INSTRUÇÕES", LARGURA_TELA/2, ALTURA_TELA/2 + 120, arcade.color.WHITE, 30, anchor_x="center")
        arcade.draw_text("Objetivo: Ajude Tun Tun Sahur a coletar moedas e aumentar sua pontuação.", LARGURA_TELA/2, ALTURA_TELA/2 + 60, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("Bosta Maluca persegue o jogador pelo mapa.", LARGURA_TELA/2, ALTURA_TELA/2 + 25, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("Bosta Fofa se teletransporta pelo cenário para surpreender o jogador.", LARGURA_TELA/2, ALTURA_TELA/2 - 10, arcade.color.WHITE, 12, anchor_x="center")
        arcade.draw_text("Controles: Setas = movimentação | ESC ou M = Menu Principal", LARGURA_TELA/2, ALTURA_TELA/2 - 55, arcade.color.WHITE, 12, anchor_x="center")

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
        arcade.draw_text("SOBRE O JOGO", LARGURA_TELA/2, ALTURA_TELA/2 + 150, arcade.color.WHITE, 30, anchor_x="center")
        self.lista_desenvolvedor.draw()
        arcade.draw_text("Desenvolvedor:", LARGURA_TELA/2, ALTURA_TELA/2 - 130, arcade.color.WHITE, 15, anchor_x="center")
        arcade.draw_text("João Pedro Almeida", LARGURA_TELA/2, ALTURA_TELA/2 - 160, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[ESC] ou [M] para voltar ao Menu", LARGURA_TELA/2, 50, arcade.color.WHITE, 15, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE or key == arcade.key.M:
            self.window.show_view(MenuPrincipal())

class JogoPrincipal(arcade.View):
    def __init__(self):
        super().__init__()
        self.tempo_inicio = 0
        self.alerta = ""
        self.jogador = None
        self.lista_moedas = None
        self.lista_inimigos = None

    def setup(self):
        self.tempo_inicio = time.time()
        self.fundo = arcade.load_texture(r"imagens\fundo.png")
        self.jogador = Jogador()
        self.lista_moedas = arcade.SpriteList()
        self.lista_inimigos = arcade.SpriteList()

        for i in range(25):
            self.lista_moedas.append(MoedaFixa())
            self.lista_moedas.append(MoedaMovel())

        self.lista_inimigos.append(Inimigo())
        self.lista_inimigos.append(InimigoEspecial())

    def finalizar_jogo(self, venceu):
        tempo_total = int(time.time() - self.tempo_inicio)
        tela = GameOver(self.jogador.pontos, tempo_total, venceu)
        self.window.show_view(tela)

    def on_draw(self):
        self.clear()
        arcade.draw_texture_rect(self.fundo, arcade.LBWH(0, 0, LARGURA_TELA, ALTURA_TELA))
        arcade.draw_sprite(self.jogador)
        self.lista_moedas.draw()
        self.lista_inimigos.draw()

        tempo = int(time.time() - self.tempo_inicio)
        arcade.draw_text(f"Pontos: {self.jogador.pontos}", 10, ALTURA_TELA - 20, arcade.color.WHITE, 14)
        arcade.draw_text(f"Tempo: {tempo}s", 10, ALTURA_TELA - 40, arcade.color.WHITE, 14)
        
        if self.alerta:
            arcade.draw_text(self.alerta, LARGURA_TELA / 2, 50, arcade.color.RED, 18, anchor_x="center")

    def on_update(self, delta_time):
        self.jogador.update(delta_time)
        self.lista_moedas.update()
        self.lista_inimigos.update()

        for inimigo in self.lista_inimigos:
            if isinstance(inimigo, InimigoEspecial):
                inimigo.seguir_jogador(self.jogador)

        moedas_coletadas = arcade.check_for_collision_with_list(self.jogador, self.lista_moedas)
        for moeda in moedas_coletadas:
            self.jogador.pontos += moeda.valor
            moeda.kill()

        if len(self.lista_moedas) == 0:
            self.finalizar_jogo(True)

        inimigos_atingidos = arcade.check_for_collision_with_list(self.jogador, self.lista_inimigos)
        for inimigo in inimigos_atingidos:
            self.jogador.pontos -= 1
            self.alerta = "CUIDADO! INIMIGO ATINGIU VOCÊ!"
            
            if isinstance(inimigo, InimigoEspecial):
                inimigo.center_x = random.randint(20, LARGURA_TELA - 20)
                inimigo.center_y = random.randint(20, ALTURA_TELA - 20)
                
            self.jogador.center_x = LARGURA_TELA // 2
            self.jogador.center_y = ALTURA_TELA // 2

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            self.window.show_view(MenuPrincipal())
        elif key in [arcade.key.UP, arcade.key.W]:
            self.jogador.change_y = self.jogador.velocidade
        elif key in [arcade.key.DOWN, arcade.key.S]:
            self.jogador.change_y = -self.jogador.velocidade
        elif key in [arcade.key.LEFT, arcade.key.A]:
            self.jogador.change_x = -self.jogador.velocidade
        elif key in [arcade.key.RIGHT, arcade.key.D]:
            self.jogador.change_x = self.jogador.velocidade

    def on_key_release(self, key, modifiers):
        if key in [arcade.key.UP, arcade.key.DOWN, arcade.key.W, arcade.key.S]:
            self.jogador.change_y = 0
        elif key in [arcade.key.LEFT, arcade.key.RIGHT, arcade.key.A, arcade.key.D]:
            self.jogador.change_x = 0

class GameOver(arcade.View):
    def __init__(self, pontos, tempo, venceu):
        super().__init__()
        self.pontos = pontos
        self.tempo = tempo
        self.venceu = venceu

    def on_draw(self):
        self.clear()
        if self.venceu:
            arcade.draw_text("PARABÉNS! VOCÊ VENCEU!", LARGURA_TELA/2, ALTURA_TELA/2 + 100, arcade.color.GREEN, 30, anchor_x="center")
            arcade.draw_text("Você coletou tudo perfeitamente!", LARGURA_TELA/2, ALTURA_TELA/2 + 40, arcade.color.WHITE, 15, anchor_x="center")
        else:
            arcade.draw_text("FIM DE JOGO", LARGURA_TELA/2, ALTURA_TELA/2 + 80, arcade.color.RED, 40, anchor_x="center")
            arcade.draw_text("Você sobreviveu, mas acabaram as vidas!", LARGURA_TELA/2, ALTURA_TELA/2 + 20, arcade.color.WHITE, 18, anchor_x="center")

        arcade.draw_text(f"Pontuação final: {self.pontos}", LARGURA_TELA/2, ALTURA_TELA/2, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text(f"Tempo de jogo: {self.tempo} segundos", LARGURA_TELA/2, ALTURA_TELA/2 - 40, arcade.color.WHITE, 18, anchor_x="center")
        arcade.draw_text("[M] Menu Principal   [ESC] Sair", LARGURA_TELA/2, 50, arcade.color.WHITE, 15, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if key == arcade.key.M:
            self.window.show_view(MenuPrincipal())
        elif key == arcade.key.ESCAPE:
            arcade.close_window()

def main():
    window = arcade.Window(LARGURA_TELA, ALTURA_TELA, TITULO_TELA)
    menu = MenuPrincipal()
    window.show_view(menu)
    arcade.run()

if __name__ == "__main__":
    main()