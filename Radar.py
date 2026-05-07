import pygame
import serial
import math
import threading
import queue
import sys
import random

PORTA_SERIAL = 'COM9'
BAUD_RATE = 9600
LARGURA = 1000
ALTURA = 1000
CENTRO_X = LARGURA // 2
CENTRO_Y = ALTURA // 2 + 50
RAIO_MAXIMO = 200
RAIO_PIXELS = 380

PRETO = (0, 0, 0)
VERDE_SONAR = (0, 255, 0)
VERDE_RASTER = (0, 100, 0)
VERDE_TRACE = (0, 200, 0)
VERMELHO = (255, 0, 0)
LARANJA = (255, 100, 0)
BRANCO = (255, 255, 255)

class SonarSubmarino:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("SONAR - Radar de Submarino (cm)")
        self.clock = pygame.time.Clock()
        
        self.azimute_atual = 0
        self.distancia_atual = 0
        self.ultimo_contato = None
        self.eco_ativo = False
        self.tempo_eco = 0
        
        self.fila_dados = queue.Queue()
        
        self.intensidade_linha = 255
        
        self.fonte_pequena = pygame.font.Font(None, 18)
        self.fonte_media = pygame.font.Font(None, 24)
        self.fonte_grande = pygame.font.Font(None, 36)
        
        self.scan_y = 0
        self.scan_direction = 1
        
        self.iniciar_serial()
        
    def iniciar_serial(self):
        def ler_serial():
            try:
                ser = serial.Serial(PORTA_SERIAL, BAUD_RATE, timeout=1)
                print(f"Conectado na porta {PORTA_SERIAL}")
                
                while True:
                    if ser.in_waiting:
                        linha = ser.readline().decode('utf-8').strip()
                        if ',' in linha:
                            azimute, distancia = linha.split(',')
                            azimute = int(azimute)
                            distancia = float(distancia)
                            self.fila_dados.put((azimute, distancia))
                            
            except serial.SerialException:
                print(f"Erro na porta {PORTA_SERIAL}")
            except Exception as e:
                print(f"Erro: {e}")
        
        thread = threading.Thread(target=ler_serial, daemon=True)
        thread.start()
    
    def desenhar_rosa_dos_ventos(self):
        pontos = [
            ('N', 90),
            ('NE', 45),
            ('E', 0),
            ('SE', -45),
            ('S', -90),
            ('SW', -135),
            ('W', 180),
            ('NW', 135)
        ]
        
        for nome, angulo in pontos:
            rad = math.radians(angulo)
            x = CENTRO_X + (RAIO_PIXELS + 25) * math.cos(rad)
            y = CENTRO_Y - (RAIO_PIXELS + 25) * math.sin(rad)
            texto = self.fonte_pequena.render(nome, True, VERDE_RASTER)
            self.tela.blit(texto, (x - 10, y - 10))
    
    def desenhar_raster_sonar(self):
        self.tela.fill(PRETO)
        
        if random.random() < 0.03:
            for _ in range(30):
                x = random.randint(0, LARGURA)
                y = random.randint(0, ALTURA)
                pygame.draw.circle(self.tela, (0, 50, 0), (x, y), 1)
        
        aneis = [50, 100, 150, 200]
        for distancia_cm in aneis:
            raio = (RAIO_PIXELS * distancia_cm) // RAIO_MAXIMO
            pygame.draw.circle(self.tela, VERDE_RASTER, (CENTRO_X, CENTRO_Y), raio, 1)
            texto = self.fonte_pequena.render(f"{distancia_cm}cm", True, VERDE_RASTER)
            self.tela.blit(texto, (CENTRO_X + raio - 25, CENTRO_Y - 10))
        
        for azimute in range(0, 181, 30):
            rad = math.radians(90 - azimute)
            x = CENTRO_X + RAIO_PIXELS * math.cos(rad)
            y = CENTRO_Y - RAIO_PIXELS * math.sin(rad)
            
            pygame.draw.line(self.tela, VERDE_RASTER, (CENTRO_X, CENTRO_Y), (x, y), 1)
            
            texto = self.fonte_pequena.render(f"{azimute}°", True, VERDE_RASTER)
            self.tela.blit(texto, (x - 15, y - 10))
        
        self.desenhar_rosa_dos_ventos()
        
        pygame.draw.circle(self.tela, VERDE_SONAR, (CENTRO_X, CENTRO_Y), 10)
        pygame.draw.circle(self.tela, VERDE_SONAR, (CENTRO_X, CENTRO_Y), 6)
        pygame.draw.circle(self.tela, BRANCO, (CENTRO_X, CENTRO_Y), 3)
        
        pygame.draw.line(self.tela, VERDE_SONAR, (CENTRO_X - 20, CENTRO_Y), (CENTRO_X + 20, CENTRO_Y), 1)
        pygame.draw.line(self.tela, VERDE_SONAR, (CENTRO_X, CENTRO_Y - 20), (CENTRO_X, CENTRO_Y + 20), 1)
    
    def desenhar_linha_varredura(self):
        rad = math.radians(90 - self.azimute_atual)
        
        for offset in [-5, -3, -1, 1, 3, 5]:
            rad_offset = math.radians(90 - self.azimute_atual + offset)
            x = CENTRO_X + RAIO_PIXELS * math.cos(rad_offset)
            y = CENTRO_Y - RAIO_PIXELS * math.sin(rad_offset)
            
            intensidade = max(50, 200 - abs(offset) * 20)
            cor = (0, intensidade, 0)
            pygame.draw.line(self.tela, cor, (CENTRO_X, CENTRO_Y), (x, y), 2)
        
        x_fim = CENTRO_X + RAIO_PIXELS * math.cos(rad)
        y_fim = CENTRO_Y - RAIO_PIXELS * math.sin(rad)
        
        pygame.draw.line(self.tela, VERDE_SONAR, (CENTRO_X, CENTRO_Y), (x_fim, y_fim), 3)
        
        if self.eco_ativo:
            tamanho_eco = 12 + (pygame.time.get_ticks() - self.tempo_eco) // 50
            if tamanho_eco < 30:
                cor_eco = (0, max(100, 255 - tamanho_eco * 10), 0)
                pygame.draw.circle(self.tela, cor_eco, (int(x_fim), int(y_fim)), tamanho_eco, 2)
        
        pygame.draw.circle(self.tela, (100, 255, 100), (int(x_fim), int(y_fim)), 6)
        pygame.draw.circle(self.tela, VERDE_SONAR, (int(x_fim), int(y_fim)), 3)
    
    def desenhar_eco(self):
        if self.ultimo_contato:
            azimute, distancia = self.ultimo_contato
            if distancia <= RAIO_MAXIMO:
                rad = math.radians(90 - azimute)
                raio_pixels = (distancia / RAIO_MAXIMO) * RAIO_PIXELS
                x = CENTRO_X + raio_pixels * math.cos(rad)
                y = CENTRO_Y - raio_pixels * math.sin(rad)
                
                tempo = pygame.time.get_ticks()
                pulso = (math.sin(tempo * 0.01) + 1) / 2
                
                if distancia < 50:
                    cor_base = VERMELHO
                elif distancia < 100:
                    cor_base = LARANJA
                else:
                    cor_base = VERDE_SONAR
                
                intensidade = int(150 + pulso * 105)
                cor_eco = (cor_base[0] * intensidade // 255, 
                          cor_base[1] * intensidade // 255, 
                          cor_base[2] * intensidade // 255)
                
                tamanho_base = 14
                tamanho_pulso = tamanho_base + int(pulso * 4)
                
                pygame.draw.circle(self.tela, cor_eco, (int(x), int(y)), tamanho_pulso, 2)
                pygame.draw.circle(self.tela, cor_base, (int(x), int(y)), tamanho_base - 4)
                pygame.draw.circle(self.tela, BRANCO, (int(x), int(y)), 3)
                
                for i in range(0, int(raio_pixels), 15):
                    fator = i / raio_pixels if raio_pixels > 0 else 0
                    x_linha = CENTRO_X + i * math.cos(rad)
                    y_linha = CENTRO_Y - i * math.sin(rad)
                    pygame.draw.circle(self.tela, VERDE_TRACE, (int(x_linha), int(y_linha)), 2)
    
    def desenhar_efeito_scanline(self):
        self.scan_y += self.scan_direction * 8
        
        if self.scan_y >= ALTURA:
            self.scan_y = 0
        elif self.scan_y < 0:
            self.scan_y = ALTURA
        
        for y in range(int(self.scan_y) - 2, int(self.scan_y) + 3):
            if 0 <= y < ALTURA:
                pygame.draw.line(self.tela, (0, 50, 0), (0, y), (LARGURA, y), 1)
    
    def desenhar_info(self):
        titulo = self.fonte_grande.render("SONAR", True, VERDE_SONAR)
        self.tela.blit(titulo, (20, 20))
        
        if self.ultimo_contato:
            azimute, distancia = self.ultimo_contato
            
            texto_alvo = self.fonte_media.render("CONTATO:", True, VERDE_SONAR)
            self.tela.blit(texto_alvo, (20, 70))
            
            texto_dist = self.fonte_pequena.render(f"Distancia: {distancia:.0f} cm", True, VERDE_TRACE)
            self.tela.blit(texto_dist, (30, 100))
            
            texto_ang = self.fonte_pequena.render(f"Azimute: {azimute}°", True, VERDE_TRACE)
            self.tela.blit(texto_ang, (30, 125))
            
            if distancia < 50:
                alerta = self.fonte_media.render(">>> ALERTA! <<<", True, VERMELHO)
                self.tela.blit(alerta, (LARGURA - 200, 20))
                perigo = self.fonte_pequena.render("COLISAO IMINENTE", True, VERMELHO)
                self.tela.blit(perigo, (LARGURA - 200, 55))
            elif distancia < 100:
                alerta = self.fonte_media.render(">>> CUIDADO! <<<", True, LARANJA)
                self.tela.blit(alerta, (LARGURA - 200, 20))
        else:
            texto_espera = self.fonte_media.render("AGUARDANDO CONTATO...", True, VERDE_RASTER)
            self.tela.blit(texto_espera, (20, 70))
        
        status = "ATIVO" if self.fila_dados else "CONECTANDO..."
        cor_status = VERDE_SONAR if self.fila_dados else LARANJA
        texto_status = self.fonte_pequena.render(f"SONAR: {status}", True, cor_status)
        self.tela.blit(texto_status, (LARGURA - 120, ALTURA - 30))
        
        legenda_y = ALTURA - 100
        self.tela.blit(self.fonte_pequena.render("LEGENDA:", True, VERDE_RASTER), (20, legenda_y))
        pygame.draw.circle(self.tela, VERMELHO, (35, legenda_y + 25), 6)
        self.tela.blit(self.fonte_pequena.render("< 50cm", True, VERDE_RASTER), (50, legenda_y + 20))
        pygame.draw.circle(self.tela, LARANJA, (35, legenda_y + 45), 6)
        self.tela.blit(self.fonte_pequena.render("50-100cm", True, VERDE_RASTER), (50, legenda_y + 40))
        pygame.draw.circle(self.tela, VERDE_SONAR, (35, legenda_y + 65), 6)
        self.tela.blit(self.fonte_pequena.render("> 100cm", True, VERDE_RASTER), (50, legenda_y + 60))
    
    def atualizar_sonar(self):
        while not self.fila_dados.empty():
            azimute, distancia = self.fila_dados.get()
            self.azimute_atual = azimute
            self.distancia_atual = distancia
            
            self.ultimo_contato = (azimute, distancia)
            self.eco_ativo = True
            self.tempo_eco = pygame.time.get_ticks()
        
        if self.eco_ativo and (pygame.time.get_ticks() - self.tempo_eco) > 500:
            self.eco_ativo = False
    
    def executar(self):
        running = True
        fps = 60
        last_time = pygame.time.get_ticks()
        
        print("\n" + "="*50)
        print("SONAR - RADAR DE SUBMARINO")
        print("="*50)
        print("Medidas em CENTIMETROS")
        print("Azimute em graus")
        print("\nComandos:")
        print("  ESC - Sair")
        print("  P - Pausar")
        print("  C - Limpar contato")
        print("="*50 + "\n")
        
        pausado = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        pausado = not pausado
                        print(f"{'Pausado' if pausado else 'Retomado'}")
                    elif event.key == pygame.K_c:
                        self.ultimo_contato = None
                        print("Contato removido")
            
            if not pausado:
                self.atualizar_sonar()
                
                self.desenhar_raster_sonar()
                self.desenhar_eco()
                self.desenhar_linha_varredura()
                self.desenhar_efeito_scanline()
                self.desenhar_info()
                
                current_time = pygame.time.get_ticks()
                if current_time - last_time > 16:
                    pygame.display.flip()
                    last_time = current_time
                    self.clock.tick(fps)
            
            pygame.time.wait(10)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    sonar = SonarSubmarino()
    sonar.executar()