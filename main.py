import math
import time
import numpy as np
import pyvista as pv

#-------------------------------------------------------------------
# Variáveis globais
#-------------------------------------------------------------------
# Tamanho da malha (tecido) em pontos. Todos estão separados por 1 unidade.
TAMANHO_X = 40
TAMANHO_Y = 25
TAMANHO_BARRA_RETA = 1
TAMANHO_BARRA_DIAGONAL = math.sqrt(2)

# Acelerações
VENTO = [10, 0, 2]
GRAVIDADE = [0, -9.8, 0]

# Listas para armazenar pontos e barras
pontos = []  # [x, y, z]
ultimos_pontos = []  # Armazena dados (i-1) para os pontos
faces = []  # [num_vertices, indices_vertices...]
barras = []  # [indice_vertice, indice_vertice, tamanho]
barras_secundarias = []  # [indice_vertice, indice_vertice, tamanho]

# Posição da câmera
POSICAO_CAMERA = [
    (20, 0, 120),  # Localização da câmera
    (20, 0, 0),  # Ponto de foco
    (0, 0, 0),  # Vetor viewup
]

#-------------------------------------------------------------------
# Métodos auxiliares
#-------------------------------------------------------------------
def eh_movel(indice):
    """Retorna se o ponto com o índice dado é móvel ou não"""
    return indice % TAMANHO_Y != 0

def norma(v):
    """Retorna a norma do vetor v"""
    return math.sqrt(sum(val ** 2 for val in v))

def soma(u, v):
    """Retorna (u + v)"""
    return [u[i] + v[i] for i in range(len(u))]

def subtrai(u, v):
    """Retorna (u - v)"""
    return [u[i] - v[i] for i in range(len(u))]

def multiplica(v, k):
    """Retorna a multiplicação do vetor v com o escalar k"""
    return [val * k for val in v]

#-------------------------------------------------------------------
# Métodos
#-------------------------------------------------------------------
def impõe_restrição():
    """Impõe restrição nas barras"""
    for _ in range(20):
        for barra in barras + barras_secundarias:
            a = pontos[barra[0]]
            b = pontos[barra[1]]
            d = subtrai(b, a)
            dist = norma(d)
            u = multiplica(d, 1 / dist)
            dif = 0.9 * (dist - barra[2])

            if eh_movel(barra[0]):
                if eh_movel(barra[1]):
                    pontos[barra[0]] = soma(a, multiplica(u, dif / 2))
                else:
                    pontos[barra[0]] = soma(a, multiplica(u, dif))

            if eh_movel(barra[1]):
                if eh_movel(barra[0]):
                    pontos[barra[1]] = soma(b, multiplica(u, -dif / 2))
                else:
                    pontos[barra[1]] = soma(b, multiplica(u, -dif))

def animar(h):
    """Anima a malha"""
    global pontos, ultimos_pontos
    pontos_i = [p.copy() for p in pontos]
    coef_amortecimento = 0.2

    for i, ponto in enumerate(pontos):
        if eh_movel(i):
            ponto[0] += (1 - coef_amortecimento) * (ponto[0] - ultimos_pontos[i][0]) + (h ** 2) * (VENTO[0] + GRAVIDADE[0])
            ponto[1] += (1 - coef_amortecimento) * (ponto[1] - ultimos_pontos[i][1]) + (h ** 2) * (VENTO[1] + GRAVIDADE[1])
            ponto[2] += (1 - coef_amortecimento) * (ponto[2] - ultimos_pontos[i][2]) + (h ** 2) * (VENTO[2] + GRAVIDADE[2])

    impõe_restrição()
    ultimos_pontos = pontos_i

def iniciar():
    """Configura pontos e faces na malha e restrições de barras"""
    global ultimos_pontos
    indice_ponto = 0
    for j in range(TAMANHO_X):
        for i in range(TAMANHO_Y):
            pontos.append([j, i, 0])

            if j < TAMANHO_X - 1 and i < TAMANHO_Y - 1:
                faces.append([4, indice_ponto, indice_ponto + 1, indice_ponto + TAMANHO_Y + 1, indice_ponto + TAMANHO_Y])
                barras.append([indice_ponto, indice_ponto + 1, TAMANHO_BARRA_RETA])
                barras.append([indice_ponto, indice_ponto + TAMANHO_Y + 1, TAMANHO_BARRA_DIAGONAL])
                barras.append([indice_ponto, indice_ponto + TAMANHO_Y, TAMANHO_BARRA_RETA])
            elif j == TAMANHO_X - 1 and i < TAMANHO_Y - 1:
                barras.append([indice_ponto, indice_ponto + 1, TAMANHO_BARRA_RETA])
            elif i == TAMANHO_Y - 1 and j < TAMANHO_X - 1:
                barras.append([indice_ponto, indice_ponto + TAMANHO_Y, TAMANHO_BARRA_RETA])

            if j % 2 == 0:
                if j < TAMANHO_X - 2 and i < TAMANHO_Y - 2:
                    barras_secundarias.append([indice_ponto, indice_ponto + 2, 2 * TAMANHO_BARRA_RETA])
                    barras_secundarias.append([indice_ponto, indice_ponto + 2 * (TAMANHO_Y + 1), 2 * TAMANHO_BARRA_DIAGONAL])
                    barras_secundarias.append([indice_ponto, indice_ponto + 2 * TAMANHO_Y, 2 * TAMANHO_BARRA_RETA])
                elif j == TAMANHO_X - 1 and i < TAMANHO_Y - 2:
                    barras_secundarias.append([indice_ponto, indice_ponto + 2, 2 * TAMANHO_BARRA_RETA])
                elif i == TAMANHO_Y - 1 and j < TAMANHO_X - 2:
                    barras_secundarias.append([indice_ponto, indice_ponto + 2 * TAMANHO_Y, 2 * TAMANHO_BARRA_RETA])

            indice_ponto += 1

    ultimos_pontos = [p.copy() for p in pontos]

#-------------------------------------------------------------------
# Execução
#-------------------------------------------------------------------
iniciar()
print("Escolha o ângulo e posição da câmera")
print("Para iniciar a animação, clique 'q'")

plotter = pv.Plotter()
malha = pv.PolyData(np.array(pontos), np.array(faces))
plotter.add_mesh(malha, color='y', show_edges=False, interpolate_before_map=True)
plotter.add_axes()
plotter.enable_eye_dome_lighting()
plotter.camera_position = POSICAO_CAMERA
plotter.show(interactive=True, auto_close=False, window_size=[800, 600])

plotter.open_gif("animacao.gif")
plotter.write_frame()

n_passos = 75
tempo_total = 0
for i in range(n_passos):
    inicio = time.time()
    animar(0.4)
    fim = time.time()
    print(f"   Plotando passo {i+1} de {n_passos}... tempo decorrido para passo de 0.4s: {(fim - inicio)}s", end="\r")
    tempo_total += (fim - inicio)
    plotter.update_coordinates(np.array(pontos), mesh=malha)
    plotter.write_frame()

print("\n")
plotter.close()
print(tempo_total)
