# preCICE AI

**What is preCICE?**
preCICE is a coupling library which glues together different physics solvers. For e.g. there is a solve for solid and another solve for the liquids, preCICE helps these to solvers to communicate and exchange data between them in order to perform multi-physics simulations.
It handles:
- communication
- data exchange
- mesh mapping
- coupling time steps
- convergence handling
- profiling/logging
<br>

**Basic Words**
- participant  = one solver/program in the coupled simulation
- mesh         = coupling interface geometry
- data         = values exchanged, e.g. Force, Displacement, Temperature
- mapping      = how data moves between non-matching meshes
- coupling     = when and how participants exchange data
- adapter      = code that connects a solver to preCICE