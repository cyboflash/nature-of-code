import copy
import math
import noise
import pygame
import random
import subpixelsurface
import sys

SCREEN_SIZE = SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
SCREEN_COLOR = pygame.Color("white")

SCREEN = pygame.display.set_mode(SCREEN_SIZE)
FRAME_RATE = 30
NBR_MOVERS = 20

class PVector(object):
  tx = 0.001
  ty = 10000
  def __init__(self, x, y):
    self.x = x
    self.y = y

  def add(self, vector):
    self.x += vector.x
    self.y += vector.y

  def sub(self, vector):
    self.x -= vector.x
    self.y -= vector.y

  def mult(self, n):
    self.x *= n
    self.y *= n

  def div(self, n):
    self.x /= n
    self.y /= n

  def mag(self):
    return math.sqrt(self.x**2 + self.y**2)

  def normalize(self):
    m = self.mag()
    if 0 != m:
      self.div(m)

  @classmethod
  def random2D_vector(self):
    v = PVector(noise.pnoise1(PVector.tx), noise.pnoise1(PVector.ty))
    PVector.tx += 0.01
    PVector.ty += 0.01
    v.normalize()
    return v

  @classmethod
  def add_vector(vector1, vector2):
    return PVector(vector1.x + vector2.x, vector1.y + vector2.y)

  @classmethod
  def sub_vector(self, vector1, vector2):
    return PVector(vector1.x - vector2.x, vector1.y - vector2.y)

class Mover(object):
  CIRCLE_COLOR = (0, 0, 0, 127)
  RIM_COLOR = pygame.Color("black")
  def __init__(self, m, x, y):
    self.location = PVector(x, y)
    self.velocity = PVector(0, 0)
    self.acceleration = PVector(0, 0)
    self.mass = m

    surface = pygame.Surface((self.mass, self.mass), pygame.SRCALPHA, 32)
    surface = surface.convert_alpha()

    width = int(math.ceil(0.05*self.mass))
    pygame.draw.circle(
        surface,
        self.RIM_COLOR,
        (int(surface.get_width()/2), int(surface.get_height()/2)),
        int(self.mass/2), width
    )

    pygame.draw.circle(
        surface,
        self.CIRCLE_COLOR,
        (int(surface.get_width()/2), int(surface.get_height()/2)),
        int(math.ceil(self.mass/2 - width)) + 1
    )

    self.rect = surface.get_rect()
    self.surface = subpixelsurface.SubPixelSurface(surface)

  def check_edges(self):
    if self.location.x + self.rect.width/2 >= SCREEN_WIDTH:
      self.location.x = SCREEN_WIDTH - self.rect.width/2
      self.velocity.x *= -1
    elif self.location.x - self.rect.width/2 <= 0:
      self.location.x = self.rect.width/2
      self.velocity.x *= -1

    if self.location.y + self.rect.height/2 >= SCREEN_HEIGHT:
      self.location.y = SCREEN_HEIGHT - self.rect.height/2
      self.velocity.y *= -1

  def update(self):
    self.velocity.add(self.acceleration)
    self.location.add(self.velocity)
    self.acceleration.mult(0)

  def display(self):
    SCREEN.blit(self.surface.at(self.location.x, self.location.y),
                (self.location.x - self.mass/2, self.location.y - self.mass/2))

  def limit(self, l):
    if self.velocity.mag() > l:
      self.velocity.normalize()
      self.velocity.mult(l)

  def apply_force(self, vector):
    force = copy.deepcopy(vector)
    force.div(self.mass)
    self.acceleration.add(force)

  def repel(self, m):
    force = PVector.sub_vector(m.location, self.location)
    distance = force.mag()
    if distance - self.mass/2 - m.mass/2 < 20:
      g = 0.8

      force.normalize()
      force.mult(g*self.mass*m.mass)
      force.div(2*distance)

      m.apply_force(force)

  def attract(self, m):
    g = 0.4
    force = PVector.sub_vector(self.location, m.location)
    distance = force.mag()

    # Constrain the distance
    if distance < 50:
      distance = 50
    if distance > 100:
      distance = 100

    force.normalize()
    force.mult(g*self.mass*m.mass)
    force.div(distance**2)

    m.apply_force(force)

class Liquid(object):
  def __init__(self, drag, x, y, width, height):
    self.drag = drag
    self.surface = pygame.Surface((width, height))
    self.surface.fill(pygame.Color("grey"))
    self.rect = self.surface.get_rect()
    self.rect.top = y
    self.rect.left = x

  def display(self):
    SCREEN.blit(self.surface, self.rect)

  def is_inside(self, m):
    return (m.location.x + m.rect.width / 2 >= self.rect.left) and \
           (m.location.x + m.rect.width / 2 <= self.rect.left + self.rect.width) and \
           (m.location.y + m.rect.height / 2 >= self.rect.top) and \
           (m.location.y + m.rect.height / 2 <= self.rect.top + self.rect.height)

  def get_drag(self, m):
    drag = copy.deepcopy(m.velocity)
    speed = drag.mag()

    drag.mult(-1)
    drag.normalize()
    drag.mult(self.drag*speed*speed)

    return drag

class Attractor(object):
  COLOR = pygame.Color("blue")
  def __init__(self, x, y, m, g):
    self.location = PVector(x, y)
    self.mass = m
    self.g = g

    self.surface = pygame.Surface((self.mass, self.mass), pygame.SRCALPHA, 32)
    pygame.draw.circle(self.surface, self.COLOR,
                       (int(self.surface.get_width()/2),
                        int(self.surface.get_height()/2)),
                       int(self.mass/2), 2)

  def display(self):
    SCREEN.blit(self.surface, (self.location.x - self.mass/2, self.location.y - self.mass/2))

  def get_attarction(self, m):
    force = PVector.sub_vector(self.location, m.location)
    distance = force.mag()

    # Constrain the distance
    if distance < 50:
      distance = 50
    if distance > 100:
      distance = 100

    force.normalize()
    force.mult(self.g*self.mass*m.mass)
    force.div(distance**2)

    return force

def main():
  movers = [Mover(random.randrange(10, 50),
                  random.randrange(SCREEN_WIDTH),
                  random.randrange(SCREEN_HEIGHT)) for i in range(NBR_MOVERS)]

  clock = pygame.time.Clock()

  while True:
    clock.tick(FRAME_RATE)
    for event in pygame.event.get():
      if event.type == pygame.QUIT: sys.exit()

    SCREEN.fill(SCREEN_COLOR)

    for i in movers:
      for j in movers:
        if i != j:
          i.attract(j)
          i.repel(j)

    for m in movers:
      m.update()
      m.display()

    pygame.display.flip()

if '__main__' == __name__:
  main()
