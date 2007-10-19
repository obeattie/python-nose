
import compiler
from compiler import visitor
from pprint import pprint

class ModuleVisitor(object):
    class Inna:
        def inna2():
            pass
    def __init__(self, filename):
        self.filename = filename
        self.classes = []
        self.functions = []
        
    def default(self, node):
        for child in node.getChildNodes():
            # visit = ASTVisitor.dispatch
            self.visit(child, node.lineage + [node])
            
    def visitModule(self, node):
        node.name = self.filename
        node.lineage = []
        # descend into classes and functions
        self.default(node)
        
    def visitClass(self, node, lineage=[]):
        node.lineage = lineage
        self.classes.append(node)
        # descend into subclasses and functions...
        self.default(node) 
        
    def visitFunction(self, node, lineage=[]):
        node.lineage = lineage
        self.functions.append(node)

def parseFile(filename):
    ast = compiler.parseFile(filename)
    modnode = ModuleVisitor(filename)
    visitor.walk(ast, modnode)
    return modnode

if __name__ == '__main__':
    modnode = parseFile(__file__)
    pprint([(n.name, n.lineno, [p.name for p in n.lineage]) 
            for n in modnode.classes])
    pprint([(n.name, n.lineno, [p.name for p in n.lineage]) 
            for n in modnode.functions])
            