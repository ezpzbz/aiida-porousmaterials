#Loading necessary modules
using PorousMaterials

# TODO: This should be the fist variable. This is where Julia would look for
# the data folder. variable name? --> $data_path
PorousMaterials.set_path_to_data("/storage/brno9-ceitec/home/pezhman/projects/noble_gas_epfl/xe_kr/data")
path = PorousMaterials.PATH_TO_DATA

# Loading General Setting like LJForceField, Framework, and replication
# TODO: This part should contain four variables.:
# 1) forcefiled file name: $ff
# 2) cutoff: $cutoff
# 3) mixing rules: $mixing
# 4) framework cssr filename: $framework.
ljff = LJForceField("UFF.csv", cutoffradius=12.5, mixing_rules="Lorentz-Berthelot")
framework = Framework("AMIMEP_clean.cssr")
rep_factor = replication_factors(framework.box, ljff)
framework = replicate(framework, rep_factor)

# Generating associated result file
# TODO: The output filename can be contructed internally and then be replaced.
# $output_filename
result = open("Ev_AMIMEP_clean.csv","w")
# TODO: I can provide more flexibility hear by defining a string varibale for the
# header: somethng like: $header.
write(result, "Ev(kJ/mol),Rv(A),x,y,z,Framework,Adsorbate,Accuracy\n")

# Iterating over Adsorbates
# TODO: three sets of variables here to be replaces:
# 1) list of adsorbates: $adsorbates --> this can come from zeo++ calc in the workchain
# or be defined in run script for standlone calculations.
# 2) list of zeo++ accuracy: same as above.
# 3) name of framework which can be constructed internally.
for i in ["Xe","Kr"]
        for j in ["S50"]
        posfile = open(path*"/zeopp/Voronoi/AMIMEP_clean_voro_"*i*"_acc_"*j*".xyz")
        lines = readlines(posfile)
        n_nodes = parse(Int, lines[1])

                # Iterating over nodes, calculating the Voronoi energy, and saving results.
                # TODO: there is only one here at line 50 which is already available from
                # previous section, ie. name of framework.
                for k = 1:n_nodes
                        xyz = split(lines[2+k])[2:4]
                        r = split(lines[2+k])[5]
                        x = parse.(Float64, xyz)
                        molecule = Molecule(i)
                        set_fractional_coords!(molecule, framework.box)
                        translate_to!(molecule,framework.box.c_to_f * x)
                        energy = (vdw_energy(framework, molecule, ljff)) * 0.00831441001625545
                        saveresults = energy, r, x[1], x[2], x[3], "AMIMEP_clean", i, j
                        write(result, join(saveresults,","), "\n")
                end
                close(posfile)
        end
end
close(result)
