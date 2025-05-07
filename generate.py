import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword : Crossword):
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }
        self.arcs = list()

    def letter_grid(self, assignment):
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)


    def get_arcs(self):

        if not len(self.arcs):
    
            arcs = set()
            for x in self.crossword.variables:
                for y in self.crossword.variables:
                    #if self.crossword.overlaps[x, y] and not arcs.__contains__((y, x)):
                    if self.crossword.overlaps[x, y]: # Let it duplicate arcs 
                        # (it makes it easier to revise arcs — for every x/y domain values find a y/x domain value)
                        arcs.add((x, y))

                arcs = list(arcs)

            return arcs
        
        return self.arcs
    

    def domain_still_valid(self, a : Variable) -> bool:
        return self.domains[a] 
    

    def solve(self):
         
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    
    def enforce_node_consistency(self):
        for var in self.crossword.variables:
            fits_var = lambda word: len(word) == var.length
            self.domains[var] = list(filter(fits_var, self.domains[var]))


    def revise(self, x : Variable, y : Variable):

    
        revised = False

        # Needs a copy in order to change the original structure (on iteraction)
        crossing_y = list()
        for word_x in self.domains[x].copy(): 
            valid_crossing_word = False 
            for word_y in self.domains[y]:
                intersection = self.crossword.overlaps[x, y]
                if word_x[intersection[0]] == word_y[intersection[1]]:
                    valid_crossing_word = True 
                    crossing_y.append(word_y)
                
            if not valid_crossing_word:
                self.domains[x].remove(word_x)
                revised = True 
            
            self.domains[y] = crossing_y
            
        return revised
    

    def ac3(self, arcs=None):
        
        if not arcs:
            arcs = self.get_arcs()

        # Calling function is passing arcs as parameters wich relates to the last assigned variable 
        # (or it is the first call at the beginning of the algorithm) 
        for arc in arcs:
            if self.revise(arc[0], arc[1]):
                
                # There is no more domain values left for the current configuration (for one or neither)
                if not self.domain_still_valid(arc[0]) or not self.domain_still_valid(arc[1]):

                    # Build a construct that permits to explicitly return some value just if this value is False (#macros?)
                    # return_if not self.domain_still_valid(arc[0]) or not self.domain_still_valid(arc[1])
                    return False 
                                
                neighboors = self.crossword.neighbors(arc[0]) 
                arcs.extend(list(neighboors)) 
            
        return True # This returning means current configuration is node consistent


    def assignment_complete(self, assignment):
        return len(assignment) == len(self.crossword.variables)


    def consistent(self, assignment : dict):
        return len(assignment.values()) == len(set(assignment.values()))
        

    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """
        return assignment


    def select_unassigned_variable(self, assignment : dict):
        
        unassigned_vars = list()
        assignment_keys = assignment.keys()
        for var in self.crossword.variables:
            if not assignment_keys.__contains__(var):
                unassigned_vars.append(var)
        
        less_remaining = len(self.crossword.words)
        selected_vars = []
        for var in unassigned_vars:
            if len(self.domains[var] <= less_remaining):
                less_remaining = len(self.domains[var])
                selected_vars.append(var)
        
        if len(selected_vars) > 1:
            
            selected_var = None 
            for var in selected_vars:
                neighboors = self.crossword.neighbors(var)
                if len(neighboors) >= neighboors:
                    selected_var = var 


            return selected_var
        
        elif len(selected_var):
            return selected_var[0]
        
        else:

            # Do what kind of error can be raised here?
            raise Exception()


    def backtrack(self, assignment : dict):

        # [1. Escolha uma variável "arbitrária" inicialmente]
        # (Evolutiva) 1.1 - Escolher uma variável que tenha o menor número de valores de domain possíveis. 
        # Isto acarreta uma verificação ordenada na medida em que verificamos a consistência dos arcos que 
        # se relacionam com a variável assinada. A primeira variável escolhida será aquela que tem o maior
        # número de relações dentro do grafo
        variable = self.select_unassigned_variable(assignment) # Can have same number of connections and same number of 
        # domain values (what happens?)
        
        # 2. Choose an arbitrary domain value initially
        order_domain_values = self.order_domain_values(variable, assignment)
        assignment[variable] = word = order_domain_values[0]
 
        # Base case [Condition] 2: Solution not possible from the current system configuration (repeated word)
        # n = 1
        # while not self.consistent(assignment):
        #     if len(order_domain_values) > n:
        #         assignment[variable] = word = order_domain_values[n]
        #     else:
        #         return None 
        #     n += 1
        
        var_domain_current_state = self.domains.copy() 
        self.domains[variable] = [word]

        neighboors = self.crossword.neighbors(variable) 
        is_arc_consistent = self.ac3(arcs=neighboors)

        if not is_arc_consistent:
            self.domains[variable] = var_domain_current_state - word
            del assignment[variable]

            if not self.domains[variable]: # It means i do not have any more values for this specific domain
                return None 

        # Base case [Condition] -1: assignment is Complete
        if self.assignment_complete(assignment):
            return assignment
        
        result = self.backtrack(assignment)

        if result is None:
            return None
        
        return assignment

        
def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()


