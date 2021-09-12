# pygame is the display engine used to show everything visually
import pygame
from pygame.locals import (K_ESCAPE, K_SPACE, KEYDOWN, K_LEFTBRACKET, K_RIGHTBRACKET,
                           MOUSEBUTTONDOWN, MOUSEBUTTONUP, QUIT)

# lists of vertices, so they exist in the global scope (redundant, but PEP-compliant!)
vertices = []
temporary_vertices = []


# vertex class for a node on a graph: has an alphabet name, an ID (not strictly necessary, a computed distance
# from the start point (as well as a flag if that distance is permanent), a list of valid edges to other
# nodes, a list of valid edges to the start, and what vertex precedes it in the path (for traceback)
class Vertex:
    def __init__(self, matrix, vertex_id):
        self.vertex_id = vertex_id
        self.name = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[vertex_id]
        self.distances = matrix[vertex_id]
        self.valid_connections = [a for a, b in enumerate(self.distances) if b > 0]

        self.distance_label = None
        self.permanent = False
        self.traceback_predecessor = None

    # eg. "Vertex B (3 conn's, distance 16, permanent False)
    def __repr__(self):
        return f'Vertex {self.name} ({len(self.valid_connections)} conn\'s, distance {self.distance_label},' \
               f' permanent {self.permanent})'

    # for sorting purposes: an integer corresponding to its distance from the start
    def __int__(self):
        if self.distance_label is None:
            return 10 ** 10
        else:
            return self.distance_label


# Another vertex class, but for the vertex's representation on the board (stored separately)
class DrawnVertex(pygame.sprite.Sprite):
    def __init__(self, x, y, numerical_id):
        # initialises the class it inherits from
        super(DrawnVertex, self).__init__()

        # data for the drawn vertex: coordinates, an ID and a name
        self.x, self.y = x, y
        self.numerical_id = numerical_id
        self.name = ALPHABET[numerical_id]

        # objects for display purposes
        self.surf = pygame.Surface((10, 10))
        self.surf.fill((0, 0, 0))
        self.text_surface = arial_font.render(self.name, False, (0, 0, 0))


# Edge class: a weighted connection between two vertices (technically directional, but directionality
# has not been implemented for ease of use)
class Edge:
    def __init__(self, start_vertex, ending_vertex, weight):
        # start and end vertices and their coordinates for display
        self.start_vertex, self.end_vertex = start_vertex, ending_vertex
        self.start_coords = (start_vertex.x + 5, start_vertex.y + 5)
        self.end_coords = (ending_vertex.x + 5, ending_vertex.y + 5)
        self.mid_coords = ((start_vertex.x + ending_vertex.x + 10) // 2,
                           (start_vertex.y + ending_vertex.y + 10) // 2)

        # black by default, stores its weight and makes a render object
        self.colour = (0, 0, 0)
        self.weight = weight
        self.text_surface = arial_font.render(str(weight), False, (0, 0, 0))

    # set colour: True means red and False means black
    def set_colour(self, is_red):
        if is_red:
            self.colour = (255, 0, 0)
        else:
            self.colour = (0, 0, 0)


# generates a matrix from what's on the screen (vertices, edges)
def convert_to_matrix():

    # creates a blank NxN matrix
    num_vertices = len(drawn_vertices)
    matrix = [[0 for _ in range(num_vertices)] for _ in range(num_vertices)]

    # for each edge, update the matrix for both directions
    for e in edges:
        endpoint_1, endpoint_2 = e.start_vertex.numerical_id, e.end_vertex.numerical_id
        matrix[endpoint_1][endpoint_2] = e.weight
        matrix[endpoint_2][endpoint_1] = e.weight

    return matrix


# arranges the two primary lists based on a given question matrix (in the global scope)
def setup_vertices(matrix):
    global vertices, temporary_vertices

    # blank vertex list NxN where N is the number of drawn_vertices
    vertices = []
    number_of_vertices = len(matrix)

    # create drawn_vertices with appropriate parameters
    for i in range(number_of_vertices):
        vertices.append(Vertex(matrix, i))

    # drawn_vertices get removed from here when made permanent
    temporary_vertices = vertices.copy()


# for a given origin vertex, update all connected temporary labels
def connect_all_vertices(origin_vertex: Vertex):

    # for all connections, get data
    for vertex_number in origin_vertex.valid_connections:
        v = vertices[vertex_number]
        new_distance_label = origin_vertex.distance_label + origin_vertex.distances[vertex_number]

        # if it has no temporary label or the new one is better, update it
        if v.distance_label is None or v.distance_label > new_distance_label:
            v.distance_label = new_distance_label
            v.traceback_predecessor = origin_vertex


# implements Dijkstra's algorithm for a defined start and end vertex,
# as well as a weighted adjacency matrix
def execute_algorithm(start_vertex: Vertex, end_vertex: Vertex):
    global temporary_vertices

    # start vertex has distance 0
    most_recent_vertex = start_vertex
    most_recent_vertex.distance_label = 0

    # while the end vertex is not permanent, repeat this process
    while not end_vertex.permanent:
        most_recent_vertex.permanent = True
        connect_all_vertices(most_recent_vertex)

        # make it permanent and sort the remaining temporaries by distance
        temporary_vertices.remove(most_recent_vertex)
        temporary_vertices = sorted([v for v in temporary_vertices], key=lambda x: int(x))

        # select the first (lowest temporary label) and repeat
        if len(temporary_vertices) > 0:
            most_recent_vertex = temporary_vertices[0]

    # use smart traceback to recreate the path
    path = end_vertex.name
    current_traceback_vertex = end_vertex

    while True:
        # with each step, add to the start of the path and trace back one step
        current_traceback_vertex = current_traceback_vertex.traceback_predecessor
        path = current_traceback_vertex.name + '-' + path

        # when you reach the start vertex, stop
        if current_traceback_vertex == start_vertex:
            break

    # return the optimal path and its length
    return path, end_vertex.distance_label


# does setup with a matrix and parses letters into indices
def find_path(start_vertex, end_vertex, matrix):
    setup_vertices(matrix)

    # gets an index for start and end in the obvious way (it's alphabetical)
    start_vertex = vertices[ALPHABET.index(start_vertex)]
    end_vertex = vertices[ALPHABET.index(end_vertex)]

    # execute Dijkstra's algorithm, and return the result
    return execute_algorithm(start_vertex, end_vertex)


# highlights the edges in a path in red
def display_path(dijkstra_path):
    path_string = dijkstra_path[0]
    path_string_backwards = dijkstra_path[0][::-1]

    # iterate through all edges and highlight them if necessary
    for e in edges:
        # make the edge black
        e.set_colour(False)

        # if the start-end string appears in the path, change the colour to red
        edge_identifier = e.start_vertex.name + '-' + e.end_vertex.name
        if edge_identifier in path_string or edge_identifier in path_string_backwards:
            e.set_colour(True)


# some general useful variables
ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVXYZ'
drawn_vertices = []
vertex_coordinates = []
edges = []

# pygame setup
pygame.init()
pygame.font.init()
arial_font = pygame.font.SysFont('Arial', 36)
screen = pygame.display.set_mode((768, 768))
pygame.display.set_caption('Dijkstra\'s Algorithm')

# some more setup for text on the screen
origin_vertex, end_vertex = None, None
current_weight = 1
editing_weight = False
cw_surface = arial_font.render(f'Current Weight: {current_weight} (press N to edit)', False, (0, 0, 0))
target_path = ['A', 'A']
tp_surface = arial_font.render(f'Start and end points not yet selected.', False, (0, 0, 0))
clock = pygame.time.Clock()
last_action = 'no-action'
ck_surfaces = [arial_font.render(f'RMB - Create new vertex at cursor', False, (0, 0, 0)),
               arial_font.render(f'LMB - Click and drag to create an edge', False, (0, 0, 0)),
               arial_font.render(f'[ - Select start point (hover)', False, (0, 0, 0)),
               arial_font.render(f'] - Select end point (hover)', False, (0, 0, 0)),
               arial_font.render(f'Z - Undo last action', False, (0, 0, 0))]

# main loop - FPS capped at 30 to save resources
running = True
while running:
    clock.tick(30)

    # event handler
    for event in pygame.event.get():
        if event.type == KEYDOWN:

            # escape closes out of the program
            if event.key == K_ESCAPE:
                quit()

            # select start and end points with [ and ]
            elif event.key in (K_LEFTBRACKET, K_RIGHTBRACKET):
                mouse_pos = pygame.mouse.get_pos()
                for cpair in vertex_coordinates:

                    # update the target_path list accordingly
                    if abs(cpair[0] - mouse_pos[0]) < 15 and abs(cpair[1] - mouse_pos[1]) < 15:
                        target_path[0 if event.key == K_LEFTBRACKET else 1] = ALPHABET[vertex_coordinates.index(cpair)]
                        tp_surface = arial_font.render(f'Finding path from {" to ".join(target_path)}'
                                                       f' - press space to confirm.',
                                                       False, (0, 0, 0))

            # press space: find the best path and highlight it (only if target_path is valid)
            elif event.key == K_SPACE and target_path[0] != target_path[1]:
                last_action = 'display-path'
                drawn_matrix = convert_to_matrix()
                setup_vertices(drawn_matrix)
                current_path = find_path(*target_path, drawn_matrix)
                display_path(current_path)

            # Z - undo key, which deletes the last vertex or edge as appropriate
            elif event.key == 122:
                if last_action == 'create-vertex':
                    drawn_vertices.remove(drawn_vertices[-1])
                    vertex_coordinates.remove(vertex_coordinates[-1])

                elif last_action == 'create-edge':
                    edges.remove(edges[-1])

                last_action = 'undo-action'

            # N - toggles weight editing
            elif event.key == 110:
                if editing_weight:
                    editing_weight = False
                    cw_surface = arial_font.render(f'Current Weight: {current_weight} (press N to edit)',
                                                   False, (0, 0, 0))
                else:
                    current_weight = 0
                    editing_weight = True
                    cw_surface = arial_font.render(f'Current Weight: {current_weight} (press N to confirm)',
                                                   False, (0, 0, 0))

            # if weight editing is on, number keys can be used to type
            elif editing_weight and (47 < event.key < 58):
                current_weight = current_weight * 10 + (event.key - 48)
                cw_surface = arial_font.render(f'Current Weight: {current_weight} (press N to confirm)',
                                               False, (0, 0, 0))

        # close out of the window
        elif event.type == QUIT:
            quit()

        # mouse handler - on click
        elif event.type == MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()

            # right click - create a vertex
            if event.button == 3:
                drawn_vertices.append(DrawnVertex(*mouse_pos, len(drawn_vertices)))
                vertex_coordinates.append(mouse_pos)
                last_action = 'create-vertex'

            # left click - find the closest vertex and set it as the start of a new edge
            elif event.button == 1:
                for cpair in vertex_coordinates:
                    if abs(cpair[0] - mouse_pos[0]) < 15 and abs(cpair[1] - mouse_pos[1]) < 15:
                        origin_vertex = drawn_vertices[vertex_coordinates.index(cpair)]

        # mouse handler - on release
        elif event.type == MOUSEBUTTONUP:
            mouse_pos = pygame.mouse.get_pos()

            # left click - find the closest vertex and set it as the end of a new edge
            if event.button == 1:
                for cpair in vertex_coordinates:
                    if abs(cpair[0] - mouse_pos[0]) < 15 and abs(cpair[1] - mouse_pos[1]) < 15:
                        end_vertex = drawn_vertices[vertex_coordinates.index(cpair)]

            # if the click and drag was successful (from A to B), create a new edge
            if (end_vertex is not None and origin_vertex is not None
                    and end_vertex != origin_vertex and current_weight > 0):
                edges.append(Edge(origin_vertex, end_vertex, current_weight))
                last_action = 'create-edge'

            # reset for next click
            origin_vertex, end_vertex = None, None

    # display code
    screen.fill((255, 255, 255))

    # draw each vertex on the screen
    for vertex in drawn_vertices:
        screen.blit(vertex.surf, (vertex.x, vertex.y))
        screen.blit(vertex.text_surface, (vertex.x, vertex.y - 24))

    # draw each edge on the screen
    for edge in edges:
        pygame.draw.line(screen, edge.colour, edge.start_coords, edge.end_coords, 2)
        screen.blit(edge.text_surface, edge.mid_coords)

    # display the controls at the bottom of the screen
    for ck_surface_number in range(5):
        screen.blit(ck_surfaces[ck_surface_number], (10, 608 + 30 * ck_surface_number))

    # display other info at the top of the screen
    screen.blit(cw_surface, (10, 10))
    screen.blit(tp_surface, (10, 40))

    # Update the display
    pygame.display.flip()
