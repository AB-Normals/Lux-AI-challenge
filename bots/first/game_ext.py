from lux.game import Game

class GameExtended(Game):
  """ A Game class with steroids """
  def __init__(self):
    Game.__init__(self)

  def _update(self, messages):
    if messages["step"] == 0:
      Game._initialize(self, messages["updates"])
      Game._update(self, messages["updates"][2:])
      self.id = messages.player
    else:
      Game._update(self, messages["updates"])

  
