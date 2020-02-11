
#Loading necessary modules
using PorousMaterials

PorousMaterials.set_path_to_data("$data_path")
path = PorousMaterials.PATH_TO_DATA
working_dir = pwd() * "/"
mkdir(working_dir * "Output")

temperature = $temperature
ljff = LJForceField("$ff", cutoffradius=$cutoff, mixing_rules="$mixing")
framework = Framework(working_dir * "$framework", check_charge_neutrality=false)
rep_factor = replication_factors(framework.box, ljff)
framework = replicate(framework, rep_factor)
density = crystal_density(framework)

result = open("Output/$output_filename","w")

write(result,"!!!Generated results using aiida-porousmaterials plugin!!!\n")
write(result,"Framework Density\n")
write(result,string(density),"\n")
write(result,"Temperature(K)\n")
write(result,string(temperature),"\n")
write(result, "Ev_K,boltzmann_factor,weighted_energy_K,Rv_A,x,y,z\n")

posfile = open(working_dir * "${frameworkname}.voro_accessible")
lines = readlines(posfile)
n_nodes = parse(Int, lines[1])

for k = 1:n_nodes
    xyz = split(lines[2+k])[2:4]
    r = split(lines[2+k])[5]
    x = parse.(Float64, xyz)
    molecule = Molecule("$adsorbate")
    set_fractional_coords!(molecule, framework.box)
    translate_to!(molecule,framework.box.c_to_f * x)
    energy = (vdw_energy(framework, molecule, ljff))
    boltzmann_factor = exp(-energy / temperature)
    wtd_energy = boltzmann_factor * energy
    saveresults = energy, boltzmann_factor, wtd_energy, r, x[1], x[2], x[3]
    write(result, join(saveresults,","), "\n")
end
close(posfile)
close(result)
