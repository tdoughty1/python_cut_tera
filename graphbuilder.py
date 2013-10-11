import networkx as nx
import os
import pylab


class depbuilder(nx.DiGraph):
    """Subclass of the directed graph class from the networkx package.
    When initialized, it builds a directed graph of all the cuts dependencies."""

    def __init__(
        self,
        cutdir='/data6/cdmsbatsProd/processing'
        '/cdmstools/CAP/FCCS/cuts/Soudan/r133'):
        """Builds a directed graph of cut dependencies upon initialization"""

        nx.DiGraph.__init__(self)
        self.cutdir = cutdir
        self.cutlist = [
            i.rstrip('m').rstrip('.')
            for i in (os.listdir(self.cutdir+'/Prodv5-3')+os.listdir(self.cutdir))
            if i.split('.')[-1] == 'm']
        #self.cutdict = {}
        #self.cutdict['Prodv5-3'] = self.lister(self.cutdir, 'Prodv5-3')
        #self.cutdict['root'] = self.lister(self.cutdir, '')
        for i in self.cutlist:
            if "v53" in i:
                prefix = '/Prodv5-3/'
            else:
                prefix = '/'

            self.add_node(i)
            with open(self.cutdir + prefix + i + '.m') as fyle:
                for lyne in fyle:
                    if '%$depend' in lyne:
                        for k in (j for j in lyne.split() if j in self.cutlist):
                            self.add_edge(i, k)

    def sketch(
        self):
        """Simple method to show a visualization of the gut graph."""

        nx.draw_shell(self, font_size=6, alpha=.8)
        pylab.show()

    def parents(
        self,
        cut):
        """Method takes a cut and recursively builds a list of
        all cuts that depend on it."""

        rents = []
        rents.append(cut)
        for i in rents:
            for j in self.predecessors_iter(i):
                rents.append(j)
        return rents

    def lister(pdir, ddir):
        return [i.rstrip('m').rstrip('.')
                for i in os.listdir(pdir+ddir)]



if __name__ == '__main__':
    a = depbuilder()
    a.sketch()
