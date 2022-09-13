
#TODO: Consider making an abstract base class

class Extension():

    class Actions:
        pass

    class Inserts:
        pass

    def __init__(self, project):
        self.bookpass1_priority = 10
        self.cellpass1_priority = 10
        self.cellpass2_actions_priority = 10
        self.cellpass2_inserts_priority = 10

        self.project = project
        self.actions = self.Actions()
        self.inserts = self.Inserts()

    def set_priorities(self, priority):
        self.bookpass1_priority = priority
        self.cellpass1_priority = priority
        self.cellpass2_actions_priority = priority
        self.cellpass2_inserts_priority = priority

    def bookpass1(self, obook):
        pass

    def cellpass1(self, match, obook, idx):
        pass

    def cellpass2_actions(self, match, obook, cell):
        pass

    def cellpass2_inserts(self, match, obook, cell):
        pass