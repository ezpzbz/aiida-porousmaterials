#Loading necessary modules
using PorousMaterials

PorousMaterials.set_path_to_data("/storage/brno9-ceitec/home/pezhman/projects/noble_gas_epfl/xe_kr/data")
path = PorousMaterials.PATH_TO_DATA

ljff = LJForceField("UFF.csv", cutoffradius=12.5, mixing_rules="Lorentz-Bert")
framework = Framework("AMIMIP_clean.cssr")
rep_factor = replication_factors(framework.box, ljff)
framework = replicate(framework, rep_factor)

result = open("AMIMPI_clean.csv","w")

write(result, "Ev(kJ/mol),Rv(A),x,y,z,Framework,Adsorbate,Accuracy\n")
for i in ['Xe', 'Kr']
        for j in ["S50"]
        posfile = open(path*"/zeopp/Voronoi/AMIMIP_clean_voro_"*i*"_acc_"*j*".xyz")
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
                        saveresults = energy, r, x[1], x[2], x[3], "AMIMIP_clean", i, j
                        write(result, join(saveresults,","), "\n")
                end
                close(posfile)
        end
end
close(result)
