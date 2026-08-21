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
| ---	| ---	| ---	| ---	| ---	| ---	| ---	| ---	| ---	|
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

Running these validations as matrix operations, and using 1s and 0s for full/empty circles would likely drastically increase efficiency if needed.

## Generator

### **Backward approach**

One approach is to generate fully solved puzzles so as to then mask cells until only few cells are remaining. The number of cells remaining, and how many more cells could have been masked while still yielding a starting point with a unique solution would determine the difficulty of the puzzle.


#### Full puzzle generation #1 (deprecated)

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

#### Full puzzle generation #2 (adopted)

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

Considering even just row 0, construction crash is definitely a possibility using this algorithm when there is only one of a kind left on the stack but more than one cells to fill and the most recent element popped off the stack was of the other kind. For example, “O, O, O, ⚫, ⚫, O, ⚫, ⚫” violates R3 at 0,6; but it could have been known already at 0,5 that the row was going to lead to an irreparable violation if information of the memory stack is used according to the principle named above: if the stack is longer than 1, if an element is selected that is the only one of its kind left on the stack, and this element is of a different type that the last element popped off the stack (or in the position directly preceding the current position in the given row or column), then select a different element from the stack. This would ensure that “O, O, O, ⚫, ⚫, O” would be repaired to “O, O, O, ⚫, ⚫, ⚫” such that it can converge to the only well-formed option left after “O, O, O, ⚫”, namely “O, O, O, ⚫, ⚫, ⚫, ⚫, O”.
The open question is whether this one principle will be sufficient to have grid converge in general or just often enough to make the algorithm practical.
At this stage it isn’t even clear that proceeding with adjacency from one corner should be more successful than proceeding row-column-row-column or just row by row. If the current row and column stacks are both checked anyway, it stands to reason that the derivations are equivalent.

Finally, considering that puzzles have color-reversing symmetry, before committing puzzles to the archive, the puzzles should be color-reversed half of the time so as to ensure that if there is a bias toward one color being over-sampled in the starting configuration, this will even out the bias.

### <do not implement for now>

### **Forward approach**

The alternative approach is to fill few starting cells based on some principles that will maximize likelihood of yielding uniquely-solvable puzzles.

Some guiding principles in the forward approach could be based on the same principles that guide a Solver. These are in turn guided by the rules of the game which place constraints on when a cell cannot be filled with one or the other circle type.

Having a principled understanding that is sufficiently exhaustive to determine unique puzzles, such that it basically subsumes a Solver, goes beyond the practical scope of creating playable puzzles. This approach will not be pursued.

### </do not implement for now>

## Solver

There are a few approaches to a Solver. The most naive approach is to fill cells at random and check if the outcome is valid. Within this family, there are more sophisticated algorithms, like a sequential fill-validate-backtrack process:

1. Reach a new “progress point”, i.e. the sum of filled cells is reached for the first time.
2. Fill one random cell with a random value.
3. Validate the grid.
4. If validation fails, attempt the other value for this cell.
5. If validation still fails, backtrack this cell: remove this cell from the set of cells to be considered for selection at this progress point, and try filling a new random cell.
6. If validation fails for all cell-value pairs at this progress point, backtrack to the previous progress point. 

This would be a computationally inefficient approach and presumably would not converge often or in reasonable time on a regular machine. The BigO would be one of exponential backtracking: We have all remaining cells with two values. Order does not actually matter. So this would be 2^N, where N is the number of remaining cells, e.g. 2^54 to 2^59 assuming we can get the starting puzzle to have somewhere between 5 and 30 cells filled out.

So the search space must be reduced before backtracking. The Rules (R2 and R3) can be leveraged to create deterministic outcomes for ideally small context windows for evaluation. For both R2 and R3, conditions can be defined which do not require the full grid and complex conditionals to determine a necessary move. Just as when playing the game, many cells can be filled out based on very short context windows:
* **R2.** Can be leveraged whenever one row or column already has 4 of one kind. All empty cells in that row or column are to be filled with the other kind.
* **R3.** Can be leveraged in two configurations: 
    * *1/ heterogeneous triplets* with a circle of one kind, a circle of the other kind, and a blank cell at either side. In such cases, the blank cell must be filled with the kind of the adjacent circle. For example, |--|⚫|O|, has to result in |⚫|⚫|O| given that |⚫|O|⚫| results in a violation of R3. 
    * *2/ homogenous triplets* with a blank cell between two circles of the same kind. In such cases, the blank cell must be filled with a circle of the same kind. For example, |⚫|--|⚫| must result in |⚫|⚫|⚫| because |⚫|O|⚫| is an R3 violation.

Both these processes are independent of a solving order and locally evaluable within their context window. They could therefore each have their own stack. At the outset, they would each amount to a process that searches the grid for applicable configurations. As the grid gets filled/solved, they would each amount to a listener that checks whether the rows/columns and triplets that contain the newly filled cell result in R2- or R3-solutions.

When neither of these two processes result in progress, the Solver would need to resort to more complex conditional reasoning. In practice, this could amount to saving the state, randomly filling a cell, proceeding as before, and backtracking if a invalid state is reached. Of course, this may result in a backtracking forest which would bring us back to the exponential complexity, but considering that we may be able to make significant progress with the rule-based solutions, this challenge may be practically surmountable.

### Algorithm

Summarizing, this approach results in the following algorithm:

1. While the grid contains R3-solvable configurations, solve them one by one. [The while loop stops when the candidate configuration space -- for R3 it includes all rows and columns -- is exhausted.]
2. Search the grid for an R2-solvable configuration, and solve them one by one. [The while loop stops when the candidate configuration space -- for R2 it includes all triplets within each row and each column -- is exhausted.]
3. Go back to (1). If all steps leading to the current step completed in sequence without filling a cell, mark this stage of the puzzle as an exception for qualitative review. [A player should be able to solve the puzzle by reasoning solely based on R2 and R3.]
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

**Note on additional solver patterns to add between (2) and (3)**

The following are solver deduction patterns that could be used between steps (2) and (3) of the algorithm. Being able to name the deduction patterns and place them into entailment relations or a complexity hierarchy can have two types of benefits: 1/ tracking which named patterns get used during a solve (once they exist) is a more natural difficulty signal than raw stats alone -- a mix of (A) number of starting given circles, (B) the distribution of which solving patterns were needed, and (C) number of backtracking attempts (implying how much of the puzzle depends on complex inter-line dependencies rather than local reasoning); 2/ they can be used by a Hint provider (see later in the document).

Intead, a more general approach will be adopted for patterns that can be solved within a line, by brute force trying every R2/R3-valid pattern within a given line to see which cell values remain constant, given that this approach should still be computationally cheap enough. So between steps (2) and (3) of the algorithm, there will be a more effective backtracking, "brute-force-line-solving", only then followed by more general recursive backtracking when reach step (3) without progress. 

In summary, we end up with the hierarchy R2 > R3 > brute-force-line-solving > recursive backtracking, such that grid-wide backtracking is reserved for complex inter-line dependencies that brute-force-line-solving can't resolve on its own. 

<deductive patterns parked for now to use later>

1. *Group-of-three configuration:* When a line has three circles of the same kind, the remaining fourth circle of that kind can only be: adjacent to the three (before or after), or in a line-edge as long as there are two or more cells between the edge and the closest cell of the group of three (else it would lead to an R3 violation); all other cells can be filled with the opposite circle type. Examples: |--|--|⚫|⚫|⚫|--|O|--| cannot be improved using this pattern, but |--|⚫|⚫|⚫|--|--|--|--| can be solved to |--|⚫|⚫|⚫|--|O|O|--|, and |⚫|⚫|⚫|--|--|--|--|--| can be solved to |⚫|⚫|⚫|--|O|O|O|--|.
2. *Quintuplet configuration:* When a line has two circles of the same kind with three blanks in between, the middle cell must be of the opposite type: A sequence of |⚫|--|⚫|--|⚫|, or |O|--|O|--|O| would either result in a sequence of five of a kind violating R2, or a triplet violating R3. |⚫|--|--|--|⚫| must therefore lead to |⚫|--|O|--|⚫|, and |O|--|--|--|O| must lead to |O|--|⚫|--|O|.
3. *Adjacency inference, no edge:* When a line has two circles of the same type occupying non-edge positions at some distance apart, the remaining two circles of the same type can only occur in: the positions adjacent to the two circles, or the two line edges. The remaining cells must be of the opposite type. Examples: |--|⚫|--|--|--|--|⚫|--| can be solved to |--|⚫|--|O|O|--|⚫|--|, and |--|⚫|--|--|⚫|--|--|--| can be solved to |--|⚫|--|--|⚫|--|O|O|.
4. *Adjacency inference, one edge:* When a line has two circles of the same type at some distance apart with only one of them occupying an edge positions, the remaining two circles of the same type can only occur in: the position adjacent to the circle on the edge, the other edge position, or the two cells on either side of the other circle (four cells). The remaining cells must be of the opposite type; worst case there are six cells possible for the same circle and none remaining for the opposite type. Examples: |⚫|--|--|⚫|--|--|--|--| can be solved to |⚫|--|--|⚫|--|--|O|--|, and |⚫|--|--|--|--|⚫|--|--| can be solved to |⚫|--|O|--|--|⚫|--|--|; in contrast, |⚫|--|--|--|⚫|--|--|--| cannot be solved further than |⚫|--|O|--|⚫|--|--|--| which was already covered by the quintuplet configuration. This amounts to two configurations with two points of symmetry each, total of only 8 configurations that might as well be hardcoded: |⚫|--|--|⚫|--|--|--|--|, |O|--|--|O|--|--|--|--|, |⚫|--|--|--|--|⚫|--|--|, |O|--|--|--|--|O|--|--|, |--|--|--|--|⚫|--|--|⚫|, |--|--|--|--|O|--|--|O|, |--|--|⚫|--|--|--|--|⚫|, |--|--|O|--|--|--|--|O|.
5. *Adjacency inference, two on one, no edge:* When a line contains three circles of the same type in non-edge positions, with a couple together, and the third one some distance apart, only the cells adjacent to the single cell can be of the same type, while all other cells can be solved as being of the other circle type.

</deductive patterns parked for now to use later>

### Difficulty levels of puzzles

Puzzles have 4 difficulty levels: Easy, Medium, Hard, and Extra Hard. At a high level, the difficulties are determined by:

* The number of given/filled out cells at the start
* The amount of "effort" involved in solving the puzzle to reach the unique solution.

How these are to be weighted and how "effort" is to be operationalized will be a matter of fine-tuning during play testing. A first pass was the following:

&xrarr; rank puzzle complexity using `given_cells` as the primary key and `solve_guesses` (times the solver had to recursively backtrack) as a tiebreaker.

This approach, combined with the generation parameters, created Easy puzzles with around 26 given cells and 0 guesses, Medium puzzles with 16 given cells and 0 guesses, Hard puzzles with 10-15 given cells and maybe some guesses (unsure), and Extra Hard puzzles with &lt;10 given cells and more guesses. Hard and Extra Hard were primarily ranked *relative* to each other based on given cells and guesses, but with guesses being a secondary criterion in a sorting mechanism. As an **outcome**, the puzzles did subjectively align into a categorical difficulty gradient.

With the more generalized solver-generator engine that uses brute-force line-solving between R2/R3 solving and grid-wide backtracking (as of Aug-11-2026), a more natural complexity gradient can be established to map it to difficulty.

* **Easy:** 17-24 given cells; fully R2/R3 solvable. 
* **Medium:** 12-18 given cells; some brute-force line-solving was required.
* **Hard:** 9-14 given cells; more brute-force line-solving needed, but still no grid-level backtracking. 
* **Extra Hard:** &le;11 given cells; grid-level backtracking is needed beyond brute-force line-solving (comment: it remains to be seen if this even exists -- if not, the scales need to be re-adjusted).


## Hint provider

A further component to help players who want to improve at the game is to add a Hint feature. Hints should be ones that follow know solving patterns. To ensure that the player learns the game with solid foundations, the offering of hints should follow a hierarchy of solving patterns, starting from the simplest and offering more advanced ones only when simpler ones are exhausted. There could be an option that is enabled by default but can be disabled for a “learning mode” to make it easier. When it is enabled by default, a hint only becomes available after every n (say 3) correctly filled cells. As hints become available, they are added to a Hint stack, which the player can cycle through to view all currently available hints. Hints are removed from the Hint stack once the are “consumed”, i.e. when the pattern that the hint points at is completed. This seems like a more challenging implementation in comparison to just showing hints. However, hints are identified based on configurations for which a solving pattern is known, such that the corresponding solution can be identified at low cost for each hint configuration found.

**Hint hierarchy (sorted shown first to show last)**

1. R2 solvable rows
    1. Identifier: line with 4 of a kind.
    2. Hint highlights: the four cells in the line that have the same circle type.
    3. Solution to track for ‘hint consumption’: the remaining cells of the line are filled out with circles of the opposite type.
2. R3 solvable triplet
    1. Identifier: triplet with edges filled with the same circle type and blank in the middle (|⚫|--|⚫|, or |O|--|O|).
    2. Hint highlights: the two triplet-edge cells that have the same circle type.
    3. Solution to track for ‘hint consumption’: the blank cell in the middle of the triplet is filled out with a circle of the same type.
3. Group-of-three configuration
    1. Identifier: line contains a group of three adjacent circles of one type, and fewer than three circles of the other type.
    2. Hint highlights: the group of three adjacent circles of the same type.
    3. Solution to track for ‘hint consumption’: the cells that are not adjacent to the group and not a line edge are filled with circles of the other type.
4. Quintuplet configuration
    1. Identifier: sequence of five cells with edges filled with the same circle type and blank in the middle (|⚫|--|⚫|, or |O|--|O|).
    2. Hint highlights: the two triplet-edge cells that have the same circle type.
    3. Solution to track for ‘hint consumption’: the blank cell in the middle of the triplet is filled out with a circle of the same type.
5. Adjacency inference, no edge
    1. Identifier: line contains exactly two circles of one type, with two or more cells between them, and neither in an edge position.
    2. [TO BE COMPLETED]
6. [TO BE COMPLETED]

## UI features

### Daily puzzle per difficulty tier + past-puzzle navigation

Puzzles are presented to the user in such a way that there is a "daily challenge" plus navigation of older puzzles. The daily challenge is a unique puzzle for each difficulty level for the given day, updated daily; all users see the same puzzle for each day so that they can compare themselves (like the Wordle model).

The archive is pre-generated such that there are enough puzzles going forward for a period of time and then incremented periodically off-line. The puzzles for the given that are mapped to the date from the archive to ensure common uniqueness among users.

Users have access to all historical puzzles.

### Hints

The game features a Hint button which allows the player to get a rule-based hint to make progress and improve their understanding of the game. By default, the player must earn the ability to use a hint by making a certain number of valid moves. However, there is a high-level option to play the game in a “Free hints mode” in which hints are freely available.

### Solve time tracking

The timer, placed between the grid and the first row of buttons, keeps track of the solve time. The timer starts when a new puzzle is started with a difficulty level button. When the puzzle is refreshed with the Restart button, the timer keeps running. If the Show Solution button is hit during the puzzle, the timer is Null and visually becomes a “n/a”.

### Solve stats

The statistics tracked are:

* Number of games solved.
* Best (min) solve time.
* Average (mean) solve time.
* Best average (inter-quartile mean) solve time.

Solve stats are disaggregated by difficulty level and by whether hints were used.

**Exclusions:**

* Puzzles where the Show Solution button was pressed at any point do not count toward solve stats.
* Puzzles where the free hints mode was selected at any point do not count toward solve stats.

