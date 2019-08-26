#Loading necessary modules
using PorousMaterials

PorousMaterials.set_path_to_data("$data_path")
path = PorousMaterials.PATH_TO_DATA
working_dir = pwd() * "/"

ljff = LJForceField("$ff", cutoffradius=$cutoff, mixing_rules="$mixing")
framework = Framework(working_dir * "$framework")
rep_factor = replication_factors(framework.box, ljff)
framework = replicate(framework, rep_factor)

result = open("$output_filename","w")

write(result, "Ev(kJ/mol),Rv(A),x,y,z,Framework,Adsorbate,Accuracy\n")
for i in $adsorbates
        for j in ["$accuracy"]
        posfile = open(working_dir * "${frameworkname}_voro_"*i*"_acc_"*j*".xyz")
        lines = readlines(posfile)
        n_nodes = parse(Int, lines[1])
                for k = 1:n_nodes
                        xyz = split(lines[2+k])[2:4]
                        r = split(lines[2+k])[5]
                        x = parse.(Float64, xyz)
                        molecule = Molecule(i)
                        set_fractional_coords!(molecule, framework.box)
                        translate_to!(molecule,framework.box.c_to_f * x)
                        energy = (vdw_energy(framework, molecule, ljff)) * 0.00831441001625545
                        saveresults = energy, r, x[1], x[2], x[3], "$frameworkname", i, j
                        write(result, join(saveresults,","), "\n")
                end
                close(posfile)
        end
end
close(result)
