import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword : Crossword):
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
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
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
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

    def solve(self):
         
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    # Build the domain values in a node consistent way at the start instead of doing it in this function
    def enforce_node_consistency(self):
        for var in self.crossword.variables:
            fits_var = lambda word: len(word) == var.length
            self.domains[var] = list(filter(fits_var, self.domains[var]))


    def revise(self, x : Variable, y : Variable):
        
        revised = False
        for word_x in self.domains[x].copy(): # I have to create a copy because i may change the original structure (in the middle of iteration)
            valid_crossing_word = False 
            for word_y in self.domains[y]:
                intersection = self.crossword.overlaps[x, y]
                if word_x[intersection[0]] == word_y[intersection[1]]:
                    valid_crossing_word = True 
            
            if not valid_crossing_word:
                self.domains[x].remove(word_x)
                revised = True 
            
        return revised
    

    # Transform variable `arcs` into a class property to avoid buildind the same structure every function call
    # Do not insert duplicate arcs (order does not matter)
    def get_arcs(self):
    
        arcs = set()
        for x in self.crossword.variables:
            for y in self.crossword.variables:
                #if self.crossword.overlaps[x, y] and not arcs.__contains__((y, x)):
                if self.crossword.overlaps[x, y]: # Let it duplicate arcs 
                    # (it makes it easier to revise arcs — for every x/y domain values find a y/x domain value)
                    arcs.add((x, y))
            
            arcs = list(arcs)

        print(f"Arcs: {arcs}")

        return arcs
    
    def vars_has_domain_value_left(self, a : Variable, b : Variable):
        return len(self.domains[a]) and len(self.domains[b])
        

    def ac3(self, arcs=None):
        
        if not arcs:
            arcs = self.get_arcs()

        for arc in arcs:
            
            if self.revise(arc[0], arc[1]):

                if not self.vars_has_domain_value_left(arc[0], arc[1]):
                    return False 
                                
                neighboors = self.crossword.neighbors(arc[0])
                arcs.extend(list(neighboors))
            
        return True    


    def assignment_complete(self, assignment):
        return len(assignment) == len(self.crossword.variables)

    # Review (use it to review word uniqueness)
    def consistent(self, assignment : dict):
        print("consistent")
        

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
                
                print(f"less remaining var: {selected_vars}")
        
        if len(selected_vars) > 1:
            
            print("Tie!")
            
            selected_var = None 
            for var in selected_vars:

                # Do What kind of structure is that?
                neighboors = self.crossword.neighbors(var)
                if len(neighboors) >= neighboors:
                    selected_var = var 

                    print(f"selected var: {selected_var}")

            return selected_var
        
        elif len(selected_var):
            return selected_var[0]
        
        else:

            # Do what kind of error can be raised here?
            raise Exception()


    def backtrack(self, assignment : dict):

        # 1. Escolha uma variável "arbitrária" inicialmente
        variable = self.select_unassigned_variable(assignment)
        
        # 2. Escolha um valor de domain "arbitrário" inicialmente
        order_domain_values = self.order_domain_values(variable, assignment)
        word = order_domain_values[0]

        # 3. Atribua o valor arbitrário a variável arbitrária numa cópia de assignment
        assignment_cp = assignment.copy()
        assignment_cp[variable] = word

        if not self.ac3():
            return None 
        
        self.backtrack(assignment)
         
        

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


