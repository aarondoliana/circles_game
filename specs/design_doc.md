# Circles Game

This document goes over steps to re-create the New York Magazine game.

## The game

The game originates from the New York Times Magazine (or New Yorker? or New York Magazine?). I don’t remember its name. But it is very simple. The game is made up of an 8x8 grid of cells, with a few cells filled to being with. You then fill out the remaining cells in accordance with the following rules:

### Rules

**R1.** A cell can be filled with either a full circle (⚫), or an empty circle (O). (Before a solution, a cell may be blank.)
**R2.** Each row and each column must have 4 full circles (⚫) and 4 empty circles (O).
**R3.** A circle of one kind cannot be “squeezed between” two circles of the other kind. In other words, three consecutive cells, in a row or a column, cannot form ⚫O⚫ or O⚫O.

### Example

***Start:***

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|	|	|	|O	|⚫	|	|	|	|
|1	|	|O	|	|	|	|	|⚫	|	|
|2	|	|	|	|O	|	|	|	|	|
|3	|	|	|	|O	|⚫	|	|	|⚫	|
|4	|⚫	|	|	|⚫	|O	|	|	|O	|
|5	|	|	|	|	|	|	|	|	|
|6	|	|	|⚫	|	|	|	|O	|	|
|7	|	|	|	|⚫	|O	|	|	|O	|

***Solution:***

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|O	|⚫	|⚫	|O	|O	|O	|⚫	|⚫	|
|1	|⚫	|O	|O	|⚫	|⚫	|⚫	|O	|O	|
|2	|⚫	|O	|O	|⚫	|⚫	|⚫	|O	|O	|
|3	|O	|⚫	|⚫	|O	|O	|O	|⚫	|⚫	|
|4	|O	|⚫	|⚫	|O	|O	|O	|⚫	|⚫	|
|5	|⚫	|O	|O	|⚫	|⚫	|⚫	|O	|O	|
|6	|⚫	|O	|O	|⚫	|⚫	|⚫	|O	|O	|
|7	|O	|⚫	|⚫	|O	|O	|O	|⚫	|⚫	|

## Components to re-create the game

The following **algorithms** are needed to create the game:

1. **Generator:** Puzzles need to be **generated.**
2. **Validator:** Every step of the puzzle must be **valid.**
3. **Solver:** Optionally, it may be necessary to be able to solve a puzzle, or attempt a solution at a puzzle to validate whether there is a single solution.

In addition, to play the game, it will need the following **objects**:

1. **Cell:** The cells containing the circles. A cell can generally have one of three *Values:* a full circle (⚫), an empty circle (O), or blank. Since a game goes through a starting stage, or playing stage, and a solution, Cells have values *stored* or *tracked* for these stages:
    1. *Starting stage:* When a game is started, some cells are filled out, and the rest are not so that the player can fill them out according to the rules of the game. The *starting value* of a cell can therefore be any of the three values.
    2. *Playing stage:* During play, the player fills out cells with a blank starting value. The *playing value* can therefore be any of the three values.
    3. *Solution stage:* All cells of a solved puzzle will be filled out. The *solution value* of a cell is therefore either a full circle (⚫) or a empty circle (O).
2. **Grid:** The arrangement of 8x8 cells to form a 2-dimensional matrix, i.e. Grid, which ultimately will form the puzzle.
3. **Puzzle:** A single Puzzle object, which was generated and validated, as well as classified for level of complexity. Each Puzzle has a unique ID, and a sorted ID based on complexity.
4. **Archive:** A collection of generated, validated, and classified Puzzles.
5. **Player:** The single player who starts a Game. A Player would have an ID through which you can access player-specific information, stats, filter out previously solved games, etc.
6. **Player archive:** An archive to track player-specific information, by player ID.
7. **Game:** The User Interface in which 
    1. *Selection:* the player can select the size and complexity and start a Game. A random Puzzle is selected from the Archive. The Puzzle is displayed with the starting value of all Cells. 
    2. *Moves:* The player can make one Move at a time. With a Move, the player changes the *playing value* of a Cell. Cells with a blank starting values cannot be changed throughout the game. (Changing a starting value would effectively change which puzzle you are playing.) The playing value of a cell can be changes any number of times on the path toward the solution. The playing value can be changed from blank to a circle, a circle to the other circle, or a circle to blank. 
    3. *Options:* At any point, the player can set the Game to show validation errors live or only once all numbers are entered. If live validation is turned on, after each Move, the playing value is the affected Cell is compared to the solution value to validate if it is correct or not and the Game provides feedback by coloring the cell orange if not. In addition, the Game runs the Validator to highlight with a red outline any group of three contiguous cells that don’t meet Rule R3, or any row or column that doesn’t meet Rule R2.
    4. *Memory:* The Game stores the sequence of moves by the player.
    5. *Meta-moves:*
        1. The player can go back and forth between moves played. 
        2. The player can restart the game.
        3. The player can show the solution.
        4. The player can start a new game (different puzzle from the archive).
8. **Platform:** A User Interface that allows a player to sign up if they want so that their player ID is stored and they can access player stats.

## Some considerations

Generation runs into a number of challenges. The generation approach needs to ensure that there is a single valid solution based on a starting grid with few pre-filled cells. Generating a valid 8x8 is not difficult, but making it diverse already becomes more challenging. For example, creating valid solutions by random generation followed by checking for validity is computationally very inefficient. The validation is extremely simple, but still some constraints on the initial generation are needed. A principle for when a starting position will still yield only a single solution is lacking. Doing this by brute force through solving the puzzle many times and seeing how many solutions are yielded may be computationally very inefficient and requires defining a Solver. Nonetheless, computational efficiency may not be required considering that a set of puzzles can be generated on a longer timeline, with the results stored to create an archive of puzzles that can be pulled from when playing.

## Validator

The validator is trivial based on the three rules of the game:

1. **R1.** A cell can be filled with either a full circle (⚫), or an empty circle (O). (Before a solution, a cell may be blank.)
    1. This rule does not need be captured by the Validator given that it would be implicitly encoded already in the Generator, as well as in the Cell object property.
2. **R2.** Each row and each column must have 4 full circles (⚫) and 4 empty circles (O).
    1. This rule is validated by checking each row and each column, counting the number of full and empty circles, and checking that neither has a cardinality > 4. 
3. **R3.** A circle of one kind cannot be “squeezed between” two circles of the other kind. In other words, three consecutive cells, in a row or a column, cannot form ⚫O⚫ or O⚫O.
    1. This rule is validated by iterating over each column and each row, and within each iterating over each contiguous triplet of cells to validate that the triplet is neither full-empty-full nor empty-full-empty.

Running these validations as a matrix operations, and using 1s and 0s for full/empty circles would likely drastically increase efficiency.

## Generator

### **Backward approach**

One approach is to generate fully solved puzzles so as to then mask cells until only few cells are remaining. The number of cells remaining, and how many more cells could have been masked while still yielding a starting point with a unique solution would determine the difficulty of the puzzle.


#### Full puzzle generation #1

The following processes can constrain randomness during generation while still increasing variability:

1. Generate a starting grid which satisfies R2.
    1. An algorithm can be used to fill the grid one quadrant at the time. Start randomly in one quadrant. Then fill the adjacent quadrant with a circle-type opposite copy of the quadrant, moving in the direction of the adjacent quadrant. Then fill the final quadrant with the copy of the first quadrant.
2. Validate whether R2+R3 pass.
3. If not, Modify the grid 1-10 times with the following operations:
    1. Permute the columns and rows (maintains R2).
    2. Rotate 2x2 squares of diagonally matching circles [[o,x],[x,o]] (maintains R2).
4. Iterate between (2) and (3) until a valid end state is generated. Break after X amount of time.
5. Store the validated grid to an Archive. 

*Illustration of step 1. Generate a starting grid which satisfies R2.*

*Step1a:*

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|⚫	|⚫	|⚫	|O	|	|	|	|	|
|1	|O	|⚫	|⚫	|⚫	|	|	|	|	|
|2	|O	|O	|⚫	|⚫	|	|	|	|	|
|3	|O	|O	|O	|⚫	|	|	|	|	|
|4	|	|	|	|	|	|	|	|	|
|5	|	|	|	|	|	|	|	|	|
|6	|	|	|	|	|	|	|	|	|
|7	|	|	|	|	|	|	|	|	|

*Step1b:*

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|⚫	|⚫	|⚫	|O	|O	|O	|O	|⚫	|
|1	|O	|⚫	|⚫	|⚫	|O	|O	|O	|⚫	|
|2	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|O	|
|3	|O	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|
|4	|	|	|	|	|	|	|	|	|
|5	|	|	|	|	|	|	|	|	|
|6	|	|	|	|	|	|	|	|	|
|7	|	|	|	|	|	|	|	|	|

*Step1c:*

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|⚫	|⚫	|⚫	|O	|O	|O	|O	|⚫	|
|1	|O	|⚫	|⚫	|⚫	|⚫	|O	|O	|O	|
|2	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|O	|
|3	|O	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|
|4	|O	|O	|O	|⚫	|	|	|	|	|
|5	|⚫	|O	|O	|O	|	|	|	|	|
|6	|⚫	|⚫	|O	|O	|	|	|	|	|
|7	|⚫	|⚫	|⚫	|O	|	|	|	|	|

*Step1d:*

|	|0	|1	|2	|3	|4	|5	|6	|7	|
|---	|---	|---	|---	|---	|---	|---	|---	|---	|
|0	|⚫	|⚫	|⚫	|O	|O	|O	|O	|⚫	|
|1	|O	|⚫	|⚫	|⚫	|⚫	|O	|O	|O	|
|2	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|O	|
|3	|O	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|
|4	|O	|O	|O	|⚫	|⚫	|⚫	|⚫	|O	|
|5	|⚫	|O	|O	|O	|⚫	|⚫	|⚫	|O	|
|6	|⚫	|⚫	|O	|O	|O	|O	|⚫	|⚫	|
|7	|⚫	|⚫	|⚫	|O	|O	|O	|O	|⚫	|

#### Full puzzle generation #2

To maximize randomness and variation, the end puzzle can be generated by locally expanding to nearby cells and keeping a memory stack for each row and column. Considering that the number of rows and columns is fixed, the memory stacks should not be a problem. Then one neighboring each cell at a time, it is filled randomly by full or empty and validated against R3 and R2. If neither are valid the puzzle construction crashes and starts over.

1. 0,0: O. Valid.
2. 0,1: O. Valid.
3. 1,0: ⚫. Valid.
4. 1,1: O. Valid.
5. 0,2: ⚫. Valid.
6. 2,0: O. Violates R3. ⚫. Valid.
7. 2,1: O. Valid.
8. 1,2: ⚫. Valid.
9. 2,2: ⚫. Violates R3 for row2. O. Valid.

Considering even just row 0, construction crash is definitely a possibility using this algorithm when there is only one of a kind left on the stack but more than one cells to fill and the most recent element popped off the stack was of the other kind. For example, “O, O, O, ⚫, ⚫, O, ⚫, ⚫” violates R3 at 0,6; but it could have been known already at 0,5 that the row was going to lead to an irreparable violation if information of the memory stack is used according to the principle name above: if the stack is longer than 1, if an element is selected that is the only one of its kind left on the stack, and this element is of a different type that the last element popped off the stack (or in the position directly preceding the current position in the given row or column), then select a different element from the stack. This would ensure that “O, O, O, ⚫, ⚫, O” would be repaired to “O, O, O, ⚫, ⚫, ⚫” such that it can converge to the only well-formed option left after “O, O, O, ⚫”, namely “O, O, O, ⚫, ⚫, ⚫, ⚫, O”.
The open question is whether this one principle will be sufficient to have grid converge in general or just often enough to make the algorithm practical.
At this stage it isn’t even clear that proceeding with adjacency from one corner should be more successful than proceeding row-column-row-column or just row by row. If the current row and column stacks are both checked anyway, it stands to reason that the derivations are equivalent.

### <do not implement for now>

### **Forward approach**

The alternative approach is to fill few starting cells based on some principles that will maximize likelihood of yielding uniquely-solvable puzzles.

Some guiding principles in the forward approach could be based on the same principles that guide a Solver. These are in turn guided by the rules of the game which place constraints on when a cell cannot be filled with one or the other circle type. 

### </do not implement for now>

## Solver

There are a few approaches to a Solver. The most naive approach is to fill cells at random and check if the outcome is valid. Within this family, there are more sophisticated algorithms, like a sequential fill-validate-backtrack process:

1. Reach a new “progress point”, i.e. the sum of filled cells is reached for the first time.
2. Fill one random cell with a random value.
3. Validate the grid.
4. If validation fails, attempt the other value for this cell.
5. If validation still fails, backtrack this cell: remove this cell from the set of cells to be considered for selection at this progress point, and try filling a new random cell.
6. If validation fails for all cell-value pairs at this progress point, backtrack to the previous progress point. 

This would be a computationally inefficient approach and presumably would not converge often or in reasonable time on a regular machine. (What would be the O here? You have all remaining cells with two values. Order does not actually matter. So this might be 2^N, where N is the number of remaining cells. So this is exponential.) In addition, the backtracking requires dynamic memory stacks: one constant stack for progress points, and one maintained for each progress point from start to current, to track its set of candidate cells remaining. The computational complexity for each progress point is 2 values per cell remaining: 2(N−P), where N=maximum number of cells=64, and P is the progress point=cells currently filled. The complexity of each possible progress point is combined, with P decreasing by 1 each time, leading to a factorial increase: ∏P=1N​2(N−P)=2N−1

A further step of sophistication would be to take as much of the guess work out of the filling of the cells. This would mean leveraging the Rules (R2 and R3) to create deterministic outcomes for ideally small context windows for evaluation. For both R2 and R3, conditions can be defined which do not require the full grid and complex conditionals to determine a necessary move. Just as when playing the game, many cells can be filled out based on very short context windows:
**R2.** Can be leveraged whenever one row or column already has 4 of one kind. All empty cells in that row or column are to be filled with the other kind.
**R3.** Can be leveraged whenever an empty cell, a circle of one kind, and a circle of the other kind form a triplet. In such cases, the empty cell must be filled with the kind of the adjacent circle. For example, [ __, O, ⚫ ], has to result in [ O, O, ⚫ ] given that [ ⚫, O, ⚫ ] results in a violation of R3.
Both these processes are independent of a solving order and locally evaluable within their context window. They could therefore each have their own stack. At the outset, they would each amount to a process that searches the grid for applicable configurations. As the grid gets filled/solved, they would each amount to a listener that checks whether the rows/columns and triplets that contain the newly filled cell result in R2- or R3-solutions.

When neither of these two processes result in progress, the Solver would need to resort to more complex conditional reasoning. In practice, this could amount to saving the state, randomly filling a cell, proceeding as before, and backtracking if a invalid state is reached. Of course, this may result in a backtracking forest which would bring us back to the exponential complexity, but considering that we may be able to make significant progress with the rule-based solutions, this challenge may be practically surmountable.

### Algorithm

Summarizing, this approach results in the following algorithm:

1. While the grid contains R3-solvable configurations, solve them one by one. [The while loop stops when the candidate configuration space, for R3 all rows and columns, is exhausted.]
2. Search the grid for an R2-solvable configuration, and solve them one by one. [The while loop stops when the candidate configuration space, for R2 all triplets within each row and each column, is exhausted.]
3. Go back to (1). If steps (1) and (2) completed in sequence without filling a cell, mark this stage of the puzzle as an exception for qualitative review. [A player should be able to solve the puzzle by reasoning solely based on R2 and R3.]
4. Validate. [might be unnecessary]
5. Check if puzzle if complete. If yes, exit.
6. Save the current State to the Backtracking stack.
7. Fill a cell at random with a random circle type.
8. Validate. 
    1. If the State is valid, go to (1).
    2. If the State is not valid, change the value entered and validate again.
        1. If the State is valid, go to (1).
        2. If the State is not valid, save this cell as depleted for this State. 
            1. If there are still empty cells not marked as depleted in the last State added to the Backtracking stack, backtrack to that State and go to (7).
            2. If all empty cells in the last State added to the Backtracking stack are marked as depleted, move to the State prior to the last one considered if one exists and go to (7), else raise a critical error.

**Additional solver patterns to add between (1) and (2)**

1. When a line has two circles of the same kind with three blanks in between, the middle cell must be of the opposite type: A sequence of ⚫ _ ⚫ _ ⚫, or O _ O _ O would either result in a sequence of five of a kind violating R2, or a triplet violating R3. ⚫ _ _ _ ⚫ must therefore lead to ⚫ _ O _ ⚫, and O _ _ _ O must lead to O _ ⚫ _ O.
2. 



### <do not implement for now>

#### Future alternative algorithms

A different *kind* of sophistication would be to let the Solver apply randomly, but include learning, such as reinforcement learning.

Considering that the Solver should be of reasonable computational efficiency 

### </do not implement for now>

