# Map the work library to its physical location
vmap work test_modelsim/work
# Run simulation
vsim -c -voptargs="+acc" -do "run -all; quit" work.tb_counter
